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



class ClockAlreadyStarted(Exception):
    """Raised when users try to start a clock more than once.
    """
    pass


class ClockNotStarted(Exception):
    """Raised when users try to stop a clock not yet started.
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
            ClockAlreadyStarted
        """
        if self.started is not None:
            raise ClockAlreadyStarted()
        self.started = gobject.timeout_add(1000 // TICKS, self._tick)

    def stop(self):
        """Stop to emit ticks.

        Raise:
            ClockNotStarted.
        """
        if self.started is None:
            raise ClockNotStarted()
        gobject.source_remove(self.started)
        self.started = None

    def _tick(self):
        """Emit a `tick' signal.
        """
        self.emit('tick')

        return True


class TicksValueError(Exception):
    """Raised when trying to set the number of ticks to a value not
    greater than 0.
    """

    def __init__(self):
        super(TicksValueError, self).__init__(
            "Param `ticks' should be greater than 0."
        )


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
            ValueError
        """
        super(Timer, self).__init__()

        if ticks <= 0:
            raise TicksValueError()
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
            ValueError
        """
        self.count = 0
        if ticks is not None:
            if ticks <= 0:
                raise TicksValueError()
            self.ticks = ticks


class CoreAlreadyStarted(Exception):
    """Raised when users try to start a core object twice.
    """
    pass


class CoreNotYetStarted(Exception):
    """Raised when `ticking' a core object not yet started.
    """
    pass


class Core(gobject.GObject):
    """XXX
    """

    __gsignals__ = {
        'phase-fraction': (gobject.SIGNAL_RUN_FIRST, None,
                           (gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT,
                            gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT))
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
        """Return the name of the next timer to activate.

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
            CoreAlreadyStarted
        """
        if self.current is not None:
            raise CoreAlreadyStarted()
        self.current = next(self.next_timer)
        self.phase = 1
        timer = self.timers[self.current]
        self.emit('phase-fraction', self.current, self.phase, timer.count,
                  timer.ticks)

    def tick(self):
        """Route the tick to the active timer.

        When a timer reach its limit, then we have to select the next one.

        Raise:
            CoreNotYetStarted
        """
        if self.current is None:
            raise CoreNotYetStarted()
        timer = self.timers[self.current]
        # emit the signal before to tick the timer in orde to prevent
        # race conditions between signals.
        self.emit('phase-fraction', self.current, self.phase,
                  (timer.count + 1), timer.ticks)
        timer.tick()

    def stop(self):
        """Reset the current timer and set self.current to None.

        Raise:
            CoreNotYetStarted
        """
        if self.current is None:
            raise CoreNotYetStarted()
        self.timers[self.current].reset()
        self.current = None
        self.phase = 0
        self.next_timer = self._next_timer()

    def skip(self):
        """Skip the current pomodoro phase.

        Raise:
            CoreNotYetStarted
        """
        if self.current is None:
            raise CoreNotYetStarted()
        self.timers[self.current].reset()
        self._fire_cb(self.timers[self.current])


class FractionValueError(ValueError):
    """Raised when users try to set a fraction with a value < 0 or > 1.
    """

    def __init__(self, fraction):
        super(FractionValueError, self).__init__(
                "Fraction value not in range [0.0, 1.0]: %s." % (fraction,)
            )


class UI(gobject.GObject):
    """User interface.
    """

    __gsignals__ = {
        'begin': (gobject.SIGNAL_RUN_FIRST, None, ()),
        'end': (gobject.SIGNAL_RUN_FIRST, None, ()),
        'skip': (gobject.SIGNAL_RUN_FIRST, None, ()),
        'close': (gobject.SIGNAL_RUN_FIRST, None, ()),
    }

    def __init__(self):
        super(UI, self).__init__()

        self.window = gtk.Window()
        self.window.connect('delete-event', self._delete_cb)

        self.vbox = gtk.VBox(homogeneous=False)

        self.hbox = gtk.HBox(homogeneous=False)

        self.progressbar = gtk.ProgressBar()

        play_img = gtk.Image()
        play_img.set_from_stock(gtk.STOCK_MEDIA_PLAY,
                                gtk.ICON_SIZE_LARGE_TOOLBAR)
        stop_img = gtk.Image()
        stop_img.set_from_stock(gtk.STOCK_MEDIA_STOP,
                                gtk.ICON_SIZE_LARGE_TOOLBAR)
        skip_img = gtk.Image()
        skip_img.set_from_stock(gtk.STOCK_MEDIA_NEXT,
                                gtk.ICON_SIZE_LARGE_TOOLBAR)
        self.images = {'play': play_img,
                       'stop': stop_img,
                       'skip': skip_img
                      }
        [widget.show() for widget in self.images.values()]

        button = gtk.Button()
        button.add(self.images['play'])
        button.connect('clicked', self._clicked_cb)
        self.hbox.pack_start(button, False, False)

        button = gtk.Button()
        button.add(self.images['skip'])
        button.connect('clicked', self._clicked_cb)
        self.hbox.pack_start(button, False, False)

        self.vbox.pack_start(self.hbox, True, True)

        self.entry = gtk.Entry()
        self.vbox.pack_start(self.entry, False, False)

        self.hbox.pack_start(self.progressbar)
        self.window.add(self.vbox)
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
                self.emit('skip')
            else:
                button.remove(image)
                if image == self.images['play']:
                    button.add(self.images['stop'])
                    self.emit('begin')
                else:
                    button.add(self.images['play'])
                    self.emit('end')

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
            FractionValueError
        """
        if fraction < 0 or fraction > 1:
            raise FractionValueError(fraction)
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

    def buzz(self):
        """Raise the window to catch the attention of the user.
        """
        self.window.window.show()


class PlayerError(Exception):
    """Raised when something went wrong with the gst backend.
    """

    def __init__(self, error, debug):
        super(PlayerError, self).__init__("%s %s" % (error, debug))


class PlayerAlreadyStarted(Exception):
    """Raised when users try to start a player more than once.
    """
    pass


class PlayerNotYetStarted(Exception):
    """Raised when users try to stop a player not yet started.
    """
    pass


class Player(object):
    """Audio player.
    """

    def __init__(self):
        pygame.mixer.init()
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
        """
        if self.started:
            raise PlayerAlreadyStarted()
        self.channel = self.sound.play()

    def stop(self):
        """Stop to play the audio file.
        """
        if not self.started:
            raise PlayerNotYetStarted()
        self.sound.stop()


def ticks_to_time(ticks):
    """Convert ticks time to minutes and seconds.

    Keyword:
        ticks number of elapsed ticks.
    """
    if ticks < 0:
        raise ValueError()
    secs = ticks // TICKS
    return divmod(secs, 60)


def _tick_cb(clk, core):
    """Notify the core object about the new tick event.
    """
    core.tick()


def _phase_fraction_cb(core, name, phase, count, ticks, ui, player):
    """Update the progress-bar with the new fraction value.
    """
    (mins, secs) = ticks_to_time(ticks - count)
    ui.set_text("%s %sm:%ss" % (name, mins, secs))
    ui.set_fraction(count / ticks)
    if count == 0:
        try:
            player.start()
        except PlayerAlreadyStarted:
            pass
        if name == 'work':
            ui.set_title("Pomodoro %d/4" % (phase,))
        ui.buzz()
    if count == ticks and name == 'work':
        with open(LOG, 'a+') as f:
            date = datetime.datetime.utcnow()
            message = ui.label if ui.label else '#void'
            f.write("%s | %s\n" % (date, message))


def _begin_cb(ui, core, clk):
    """Start the core object first, and the clock second.
    """
    try:
        core.start()
    except CoreAlreadyStarted:
        pass
    try:
        clk.start()
    except ClockAlreadyStarted:
        pass


def _skip_cb(ui, core):
    """Jump to the next pomodoro phase.
    """
    try:
        core.skip()
    except CoreNotYetStarted:
        return


def _end_cb(ui, clk, core, player):
    """Stop the clock first, and the core object second.
    """
    try:
        clk.stop()
    except ClockNotStarted:
        pass
    try:
        core.stop()
    except CoreNotYetStarted:
        pass
    try:
        player.stop()
    except PlayerNotYetStarted:
        pass

    ui.set_title('Pomodoro')
    ui.set_fraction(0.0)
    ui.set_text('')


def _close_cb(ui, clk, core, player):
    """Stop eventually active objects and quit the mainloop.
    """
    _end_cb(ui, clk, core, player)

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
    ui.connect('end', _end_cb, clk, core, player)
    ui.connect('close', _close_cb, clk, core, player)
    
    gtk.main()


if __name__ == '__main__':
    _main()
