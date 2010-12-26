#!/usr/bin/env python
# -*- coding: utf-8 -*-

import gobject
import gtk



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
        self.started = gobject.timeout_add(60000, self._tick)

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


class CoreNotYetStarted(Exception):
    """Raised when `ticking' a core object not yet started.
    """


class Core(gobject.GObject):
    """XXX
    """

    __gsignals__ = {
        'new-phase': (gobject.SIGNAL_RUN_FIRST, None, (gobject.TYPE_PYOBJECT,))
    }

    def __init__(self):
        super(Core, self).__init__()

        self.timers = {'work': Timer(25),
                       'break': Timer(5),
                       'coffee': Timer(10)}
        self.current = None
        self.next_timer = self._next_timer()

        for timer in self.timers.values():
            timer.connect('fire', self.fire_cb)

    def fire_cb(self, timer):
        """Emit a signal to notify the beginning of a new phase.
        """
        self.current = next(self.next_timer)
        self.emit('new-phase', self.current)

    def _next_timer(self):
        """Return the name of the next timer to activate.
        """
        while True:
            for i in xrange(4):
                yield 'work'
                yield 'break' if i != 3 else 'coffee'

    def start(self):
        """Load a timer, and start to receive ticks.

        Raise:
            CoreAlreadyStarted
        """
        if self.current is not None:
            raise CoreAlreadyStarted()
        self.current = next(self.next_timer)
        self.emit('new-phase', self.current)

    def tick(self):
        """Route the tick to the active timer.

        When a timer reach its limit, then we have to select the next one.

        Raise:
            CoreNotYetStarted
        """
        if self.current is None:
            raise CoreNotYetStarted()
        self.timers[self.current].tick()

    def stop(self):
        """Reset the current timer and set self.current to None.

        Raise:
            CoreNotYetStarted
        """
        if self.current is None:
            raise CoreNotYetStarted()
        self.timers[self.current].reset()
        self.current = None


class FractionValueError(ValueError):
    """Raised when users try to set a fraction with a value < 0 or > 1.
    """

    def __init__(self):
        super(FractionValueError, self).__init__(
                "Fraction value not in range [0.0, 1.0]."
            )


class UI(object):
    """User interface.
    """

    __gsignals__ = {
        'begin': (gobject.SIGNAL_RUN_FIRST, None, ()),
        'end': (gobject.SIGNAL_RUN_FIRST, None, ()),
        'close': (gobject.SIGNAL_RUN_FIRST, None, ()),
    }

    def __init__(self):
        self.window = gtk.Window()
        self.window.set_title('Pomodoro')

        self.progressbar = gtk.ProgressBar()

        self.window.add(self.progressbar)
        self.window.show_all()

    @property
    def text(self):
        return self.progressbar.get_text()

    def set_text(self, name):
        self.progressbar.set_text("%s" % (name,))

    @property
    def fraction(self):
        return self.progressbar.get_fraction()

    def set_fraction(self, fraction):
        if fraction < 0 or fraction > 1:
            raise FractionValueError
        self.progressbar.set_fraction(fraction)


#def _tick_cb(clk, core):
    #core.tick()

#def _new_phase_cb(core, name, ui):
    #ui.set_text(name)

#def _delete_cb(ui, mainloop):
    #mainloop.quit()


#def _main():
    #mainloop = gobject.MainLoop()
    #clk = Clock()
    #core = Core()
    #ui = UI()

    #clk.connect('tick', _tick_cb, core)
    #core.connect('new-phase', _new_phase_cb, ui)
    #ui.connect('delete-event', _delete_cb, mainloop)
    
    #mainloop.run()



#if __name__ == '__main__':
    #_main()
