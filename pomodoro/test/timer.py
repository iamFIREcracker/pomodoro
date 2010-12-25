#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest

from pomodoro import timer



class TestClockFunctions(unittest.TestCase):

    def test_init(self):
        clk = timer.Clock()

        self.assertTrue(clk.started is None)

    def test_start(self):
        clk = timer.Clock()

        clk.start()
        self.assertTrue(clk.started != None)

        self.assertRaises(timer.ClockAlreadyStarted, clk.start)

    def test_stop(self):
        clk = timer.Clock()

        clk.start()
        clk.stop()
        self.assertTrue(clk.started is None)

        self.assertRaises(timer.ClockNotStarted, clk.stop)

    def test_tick(self):
        clk = timer.Clock()

        self.assertTrue(clk.tick())


class TestTimerFunctions(unittest.TestCase):

    def test_init(self):
        t = timer.Timer(10)

        self.assertEqual(t.ticks, 10)
        self.assertEqual(t.count, 0)

        self.assertRaises(timer.TicksValueError, timer.Timer, 0)
        self.assertRaises(timer.TicksValueError, timer.Timer, -1)


    def test_tick(self):
        t = timer.Timer(10)

        t.tick()
        self.assertEqual(t.count, 1)

        [t.tick() for i in xrange(9)]
        self.assertEqual(t.count, 0)

    def test_reset(self):
        t = timer.Timer(10)

        t.tick()
        t.reset()
        self.assertEqual(t.ticks, 10)
        self.assertEqual(t.count, 0)

        t.reset(20)
        self.assertEqual(t.ticks, 20)
        self.assertEqual(t.count, 0)

        self.assertRaises(timer.TicksValueError, t.reset, 0)
        self.assertRaises(timer.TicksValueError, t.reset, -1)


if __name__ == '__main__':
    unittest.main()
