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
        """Initializer.
        """
        super(Clock, self).__init__()

        self.started = None

    def start(self):
        """Start to emit ticks.

        Raises:
            ClockAlreadyStarted
        """
        if self.started is not None:
            raise ClockAlreadyStarted()
        self.started = gobject.timeout_add(1000, self.tick)

    def stop(self):
        """Stop to emit ticks.

        Raises:
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
