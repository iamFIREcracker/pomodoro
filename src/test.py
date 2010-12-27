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
        for timer in c.timers.values():
            self.assertEqual(timer.count, 0)

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
            [c.tick() for j in xrange(pomodoro.WORK)]
            if i != 3:
                self.assertEqual(c.current, 'break')
                self.assertEqual(c.timers[c.current].count, 0)
                [c.tick() for j in xrange(pomodoro.BREAK)]
            else:
                self.assertEqual(c.current, 'coffee')
                self.assertEqual(c.timers[c.current].count, 0)
                [c.tick() for j in xrange(pomodoro.COFFEE)]

            self.assertEqual(c.current, 'work')
            self.assertEqual(c.timers[c.current].count, 0)

        [c.tick() for i in xrange(pomodoro.WORK)]
        self.assertEqual(c.current, 'break')
        self.assertEqual(c.timers[c.current].count, 0)

    def test_stop(self):
        c = pomodoro.Core()

        c.start()
        c.tick()
        c.tick()
        c.stop()
        self.assertTrue(c.current is None)
        for timer in c.timers.values():
            self.assertEqual(timer.count, 0)

        self.assertRaises(pomodoro.CoreNotYetStarted, c.stop)


class TestUIFunctions(unittest.TestCase):

    def test_init(self):
        ui = pomodoro.UI()

    def test_set_text(self):
        ui = pomodoro.UI()

        ui.set_text('foo')
        self.assertEqual(ui.text, 'foo')

    def test_set_fraction(self):
        ui = pomodoro.UI()

        ui.set_fraction(0.5)
        self.assertEqual(ui.fraction, 0.5)

        self.assertRaises(pomodoro.FractionValueError, ui.set_fraction, -1)

    def test_buzz(self):
        ui = pomodoro.UI()

        ui.buzz()


class TestPomodoroFunctions(unittest.TestCase):

    def test_ticks_to_time(self):
        self.assertEqual(pomodoro.ticks_to_time(10), (0, 10))
        self.assertEqual(pomodoro.ticks_to_time(61), (1, 1))

        self.assertRaises(ValueError, pomodoro.ticks_to_time, -1)



if __name__ == '__main__':
    unittest.main()