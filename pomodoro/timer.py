#!/usr/bin/env python
# -*- coding: utf-8 -*-

import gobject



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
        self.started = gobject.timeout_add(1000, self.tick)

    def stop(self):
        """Stop to emit ticks.

        Raise:
            ClockNotStarted.
        """
        if self.started is None:
            raise ClockNotStarted()
        gobject.source_remove(self.started)
        self.started = None

    def tick(self):
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
