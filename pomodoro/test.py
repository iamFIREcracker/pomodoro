#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest

import pomodoro



class TestClockFunctions(unittest.TestCase):

    def test_init(self):
        clk = pomodoro.Clock()

        self.assertTrue(clk.started is None)

    def test_start(self):
        clk = pomodoro.Clock()

        clk.start()
        self.assertTrue(clk.started != None)

        self.assertRaises(pomodoro.ClockAlreadyStarted, clk.start)

    def test_stop(self):
        clk = pomodoro.Clock()

        clk.start()
        clk.stop()
        self.assertTrue(clk.started is None)

        self.assertRaises(pomodoro.ClockNotStarted, clk.stop)


class TestTimerFunctions(unittest.TestCase):

    def test_init(self):
        t = pomodoro.Timer(10)

        self.assertEqual(t.ticks, 10)
        self.assertEqual(t.count, 0)

        self.assertRaises(pomodoro.TicksValueError, pomodoro.Timer, 0)
        self.assertRaises(pomodoro.TicksValueError, pomodoro.Timer, -1)


    def test_tick(self):
        t = pomodoro.Timer(10)

        t.tick()
        self.assertEqual(t.count, 1)

        [t.tick() for i in xrange(9)]
        self.assertEqual(t.count, 0)

    def test_reset(self):
        t = pomodoro.Timer(10)

        t.tick()
        t.reset()
        self.assertEqual(t.ticks, 10)
        self.assertEqual(t.count, 0)

        t.reset(20)
        self.assertEqual(t.ticks, 20)
        self.assertEqual(t.count, 0)

        self.assertRaises(pomodoro.TicksValueError, t.reset, 0)
        self.assertRaises(pomodoro.TicksValueError, t.reset, -1)


class TestCoreFunctions(unittest.TestCase):

    def test_init(self):
        c = pomodoro.Core()

        self.assertTrue(c.current is None)

    def test_next_timer(self):
        c = pomodoro.Core()

        for i in xrange(4):
            self.assertEqual(next(c.next_timer), 'work')
            if i != 3:
                self.assertEqual(next(c.next_timer), 'break')
            else:
                self.assertEqual(next(c.next_timer), 'coffee')

        self.assertEqual(next(c.next_timer), 'work')

    def test_start(self):
        c = pomodoro.Core()

        c.start()
        self.assertEqual(c.current, 'work')

        self.assertRaises(pomodoro.CoreAlreadyStarted, c.start)

    def test_tick(self):
        c = pomodoro.Core()

        self.assertRaises(pomodoro.CoreNotYetStarted, c.tick)

        c.start()
        for i in xrange(4):
            [c.tick() for j in xrange(25)]
            if i != 3:
                self.assertEqual(c.current, 'break')
                [c.tick() for j in xrange(5)]
            else:
                self.assertEqual(c.current, 'coffee')
                [c.tick() for j in xrange(10)]

            self.assertEqual(c.current, 'work')

        [c.tick() for i in xrange(25)]
        self.assertEqual(c.current, 'break')



if __name__ == '__main__':
    unittest.main()
