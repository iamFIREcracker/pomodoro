#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
import datetime
import os
import sys

import gobject
import gtk

try:
    import pygame
    assert pygame.__version__ >= '1.8'
except (ImportError, AssertionError, AttributeError):
    sys.stderr.write('PyGame 1.8 or more recent required\n')
    sys.exit(1)


TICKS = 1 # number of ticks per second
WORK = 25 * 60 # in seconds
BREAK = 5 * 60 # in seconds
COFFEE = 10 * 60 # in seconds

BEEP = sys.path[0] + '/beep.wav'
LOG = os.path.join(os.path.expanduser("~"), '.pomodoro_history')


class AlreadyStarted(Exception):
    """Raised when users try to start startable objects more than once.
    """
    pass

class NotYetStarted(Exception):
    """Raised when users try to stop objects not yet started.
    """
    pass


class Clock(gobject.GObject):
    """Tick generator object.

    Emit a `tick' signal per second.
    """

    __gsignals__ = {
        'tick': (gobject.SIGNAL_RUN_FIRST, None, ())
    }

    def __init__(self):
        super(Clock, self).__init__()

        self.started = None

    def start(self):
        """Start to emit ticks.

        Raise:
            AlreadyStarted
        """
        if self.started is not None:
            raise AlreadyStarted()
        self.started = gobject.timeout_add(1000 // TICKS, self._tick)

    def stop(self):
        """Stop to emit ticks.

        Raise:
            NotYetStarted.
        """
        if self.started is None:
            raise NotYetStarted()
        gobject.source_remove(self.started)
        self.started = None

    def _tick(self):
        """Emit a `tick' signal.
        """
        self.emit('tick')

        return True


class Timer(gobject.GObject):
    """Count incoming ticks and emit a signals.
    """

    __gsignals__ = {
        'fire': (gobject.SIGNAL_RUN_FIRST, None, ()),
    }

    def __init__(self, ticks):
        """Initializer.

        Keywords:
            ticks how many ticks to wait before to emit the signal.

        Raise:
            ValueError: ticks <= 0
        """
        super(Timer, self).__init__()

        if ticks <= 0:
            raise ValueError()
        self.ticks = ticks
        self.count = 0

    def tick(self):
        """Increment the tick counter and emit a signal on overflow.
        """
        self.count += 1
        if self.count == self.ticks:
            self.emit('fire')
            self.count = 0

    def reset(self, ticks=None):
        """Reset tick counter and, optionally, the tick threshold.

        Keywords:
            ticks how many ticks to wait before to emit a signal.

        Raise:
            ValueError: ticks <= 0
        """
        self.count = 0
        if ticks is not None:
            if ticks <= 0:
                raise ValueError()
            self.ticks = ticks


class Core(gobject.GObject):
    """Core object of the pomodoro tracker.

    The object periodically emit signals to notify the status of the current
    session:
    - name of the current session [ 'work', 'break', 'coffee' ]
    - how many pomodoros have you done since last long break?
    - how many elapsed ticks since the beginning of the current session?
    - how many ticks count the current session?
    """

    __gsignals__ = {
        'phase-fraction': (gobject.SIGNAL_RUN_FIRST, None,
                           (gobject.TYPE_STRING, # name of the current fase
                            gobject.TYPE_INT, # index of the current fase [ 1..4 ]
                            gobject.TYPE_INT, # number of elapsed ticks
                            gobject.TYPE_INT, # number of total ticks
                           ))
    }

    def __init__(self):
        super(Core, self).__init__()

        self.timers = {'work': Timer(WORK * TICKS),
                       'break': Timer(BREAK * TICKS),
                       'coffee': Timer(COFFEE * TICKS)}
        self.current = None
        self.phase = 0
        self.next_timer = self._next_timer()

        for timer in self.timers.values():
            timer.connect('fire', self._fire_cb)

    def _next_timer(self):
        """Generator return the name of next timers to use.

        Phase 1/4: work, break.
        Phase 2/4: work, break.
        Phase 3/4: work, break.
        Phase 4/4: work, coffee.
        """
        while True:
            for i in xrange(4):
                yield 'work'
                yield 'break' if i != 3 else 'coffee'

    def _fire_cb(self, timer):
        """Emit a signal to notify the beginning of a new phase.
        """
        self.current = next(self.next_timer)
        if self.current == 'work':
            self.phase += 1
            if self.phase == 5:
                self.phase = 1
        timer = self.timers[self.current]
        self.emit('phase-fraction', self.current, self.phase, timer.count,
                  timer.ticks)

    def start(self):
        """Load a timer, and start to receive ticks.

        Raise:
            AlreadyStarted
        """
        if self.current is not None:
            raise AlreadyStarted()
        self.current = next(self.next_timer)
        self.phase = 1
        timer = self.timers[self.current]
        self.emit('phase-fraction', self.current, self.phase, timer.count,
                  timer.ticks)

    def tick(self):
        """Route the tick to the active timer.

        When a timer reach its limit, then we have to select the next one.

        Raise:
            NotYetStarted
        """
        if self.current is None:
            raise NotYetStarted()
        timer = self.timers[self.current]
        # emit the signal before to tick the timer in orde to prevent
        # race conditions between signals.
        self.emit('phase-fraction', self.current, self.phase,
                  (timer.count + 1), timer.ticks)
        timer.tick()

    def stop(self):
        """Reset the current timer and set self.current to None.

        Raise:
            NotYetStarted
        """
        if self.current is None:
            raise NotYetStarted()
        self.timers[self.current].reset()
        self.current = None
        self.phase = 0
        self.next_timer = self._next_timer()

    def skip(self):
        """Skip the current pomodoro phase.

        Raise:
            NotYetStarted
        """
        if self.current is None:
            raise NotYetStarted()
        self.timers[self.current].reset()
        self._fire_cb(self.timers[self.current])


class UI(gobject.GObject):
    """User interface.
    """

    __gsignals__ = {
        'begin': (gobject.SIGNAL_RUN_FIRST, None, ()),
        'suspend': (gobject.SIGNAL_RUN_FIRST, None, ()),
        'skip': (gobject.SIGNAL_RUN_FIRST, None, ()),
        'close': (gobject.SIGNAL_RUN_FIRST, None, ()),
    }

    def __init__(self):
        super(UI, self).__init__()

        self.window = gtk.Window()
        self.window.connect('delete-event', self._delete_cb)

        vbox = gtk.VBox(homogeneous=False)

        hbox = gtk.HBox(homogeneous=False)

        self.progressbar = gtk.ProgressBar()

        play_img = gtk.Image()
        play_img.set_from_stock(gtk.STOCK_MEDIA_PLAY,
                                gtk.ICON_SIZE_LARGE_TOOLBAR)
        pause_img = gtk.Image()
        pause_img.set_from_stock(gtk.STOCK_MEDIA_PAUSE,
                                 gtk.ICON_SIZE_LARGE_TOOLBAR)
        skip_img = gtk.Image()
        skip_img.set_from_stock(gtk.STOCK_MEDIA_NEXT,
                                gtk.ICON_SIZE_LARGE_TOOLBAR)
        self.images = {'play': play_img,
                       'pause': pause_img,
                       'skip': skip_img
                      }
        [widget.show() for widget in self.images.values()]

        self.buttons = dict()
        self.buttons['begin'] = gtk.Button()
        self.buttons['begin'].add(self.images['play'])
        self.buttons['begin'].connect('clicked', self._clicked_cb)
        hbox.pack_start(self.buttons['begin'], False, False)

        self.buttons['skip'] = gtk.Button()
        self.buttons['skip'].add(self.images['skip'])
        self.buttons['skip'].connect('clicked', self._clicked_cb)
        hbox.pack_start(self.buttons['skip'], False, False)

        vbox.pack_start(hbox, True, True)

        self.entry = gtk.Entry()
        vbox.pack_start(self.entry, False, False)

        hbox.pack_start(self.progressbar)
        self.window.add(vbox)
        self.window.show_all()

    def _delete_cb(self, window, event):
        """The window has been closed, so emit the proper signal.
        """
        self.emit('close')

    def _clicked_cb(self, button):
        """Emit begin/end event depeing on the button label.
        """
        for image in button.get_children():
            if image == self.images['skip']:
                self.skip()
            else:
                self.begin_toggle()

    def buzz(self):
        """Raise the window to catch the attention of the user.
        """
        self.window.window.show()

    def begin_toggle(self):
        """Change the image on the first button, and emit the right signal.

        If the current image is the play button, then change it to the stop
        button and emit the 'begin' signal.
        """
        button = self.buttons['begin']
        image = button.get_children()[0]
        button.remove(image)
        if image == self.images['play']:
            button.add(self.images['pause'])
            self.emit('begin')
        else:
            button.add(self.images['play'])
            self.emit('suspend')

    def skip(self):
        """Emit a `skip' signal.
        """
        self.emit('skip')

    @property
    def title(self):
        return self.window.get_title()

    def set_title(self, title):
        """Set the title of the window.

        Keywords:
            title text-string for the title
        """
        self.window.set_title(title)

    @property
    def text(self):
        return self.progressbar.get_text()

    def set_text(self, name):
        """Set the text displayed inside the progress bar.

        Keywords:
            name text-string to show.
        """
        self.progressbar.set_text("%s" % (name,))

    @property
    def fraction(self):
        return self.progressbar.get_fraction()

    def set_fraction(self, fraction):
        """Set the elapsed fraction of the progress bar.

        Keywords:
            fraction number in range [0.0, 1.0]

        Raise:
            ValueError: fraction not in [ 0..1 ]
        """
        if fraction < 0 or fraction > 1:
            raise ValueError()
        self.progressbar.set_fraction(fraction)

    @property
    def label(self):
        return self.entry.get_text()

    def set_label(self, text):
        """Set the label for the next pomodoro.

        Keywords:
            text text-string label
        """
        self.entry.set_text(text)


class Player(object):
    """Audio player.
    """

    def __init__(self):
        pygame.mixer.init() # XXX successive initializations?
        self.sound = pygame.mixer.Sound(BEEP)
        self.channel = None

    @property
    def started(self):
        try:
            return self.channel.get_busy() != 0
        except AttributeError:
            return False

    def start(self):
        """Start to play the audio file.

        Raise:
            AlreadyStarted
        """
        if self.started:
            raise AlreadyStarted()
        self.channel = self.sound.play()

    def stop(self):
        """Stop to play the audio file.

        Raise:
            NotYetStarted
        """
        if not self.started:
            raise NotYetStarted()
        self.sound.stop()



def _tick_cb(clk, core):
    """Notify the core object about the new tick event.
    """
    core.tick()


def _phase_fraction_cb(core, name, phase, count, ticks, ui, player):
    """Update the ui object, given the status of the core object.

    Keywords:
        core Core object which generated the signal.
        name name of the timer [ 'work', 'break', 'coffee' ]
        phase index of the current phase [ 1..4 ]
        count number of elapsed ticks
        ticks total number of ticks
        ui Ui object that we need to update
        player Player object used to play sounds.
    """
    (mins, secs) = divmod((ticks - count) // TICKS, 60)
    ui.set_text("%s %sm:%ss" % (name, mins, secs))
    ui.set_fraction(count / ticks)
    if count == 0:
        try:
            player.start()
        except AlreadyStarted:
            pass
        if name == 'work':
            ui.set_title("Pomodoro %d/4" % (phase,))
        ui.buzz()
    if count == ticks:
        if name == 'work':
            # log the pomodoro on the file ...
            with open(LOG, 'a+') as f:
                date = datetime.datetime.now()
                message = ui.label if ui.label else '#void'
                f.write("%s | %s\n" % (date, message))
            pass
        else:
            # and force the user to start a new pomodoro manually.
            ui.begin_toggle()


def _begin_cb(ui, core, clk):
    """Start the core object first, and the clock second.
    """
    try:
        core.start()
    except AlreadyStarted:
        pass
    clk.start()


def _skip_cb(ui, core):
    """Jump to the next pomodoro phase.
    """
    core.skip()


def _suspend_cb(ui, clk):
    """Stop the clock.
    """
    clk.stop()


def _close_cb(ui, clk, core, player):
    """Stop the clock first, and the core object second.
    """
    try:
        clk.stop()
    except NotYetStarted:
        pass
    try:
        core.stop()
    except NotYetStarted:
        pass
    try:
        player.stop()
    except NotYetStarted:
        pass

    gtk.main_quit()


def _main():
    clk = Clock()

    core = Core()

    ui = UI()
    ui.set_title('Pomodoro')

    player = Player()

    clk.connect('tick', _tick_cb, core)
    core.connect('phase-fraction', _phase_fraction_cb, ui, player)
    ui.connect('begin', _begin_cb, core, clk)
    ui.connect('skip', _skip_cb, core)
    ui.connect('suspend', _suspend_cb, clk)
    ui.connect('close', _close_cb, clk, core, player)
    
    gtk.main()


if __name__ == '__main__':
    _main()
