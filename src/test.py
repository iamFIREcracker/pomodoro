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

        self.assertRaises(pomodoro.AlreadyStarted, clk.start)

    def test_stop(self):
        clk = pomodoro.Clock()

        clk.start()
        clk.stop()
        self.assertTrue(clk.started is None)

        self.assertRaises(pomodoro.NotYetStarted, clk.stop)


class TestTimerFunctions(unittest.TestCase):

    def test_init(self):
        t = pomodoro.Timer(10)

        self.assertEqual(t.ticks, 10)
        self.assertEqual(t.count, 0)

        self.assertRaises(ValueError, pomodoro.Timer, 0)
        self.assertRaises(ValueError, pomodoro.Timer, -1)


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

        self.assertRaises(ValueError, t.reset, 0)
        self.assertRaises(ValueError, t.reset, -1)


class TestCoreFunctions(unittest.TestCase):

    def test_init(self):
        c = pomodoro.Core()

        self.assertTrue(c.current is None)
        self.assertEqual(c.phase, 0)
        for timer in c.timers.values():
            self.assertEqual(timer.count, 0)

    def test_start(self):
        c = pomodoro.Core()

        c.start()
        self.assertEqual(c.current, 'work')
        self.assertEqual(c.phase, 1)

        self.assertRaises(pomodoro.AlreadyStarted, c.start)

    def test_tick(self):
        c = pomodoro.Core()

        self.assertRaises(pomodoro.NotYetStarted, c.tick)

        c.start()

        # XXX refactor????
        # phase 1/4
        self.assertEqual(c.current, 'work')
        self.assertEqual(c.phase, 1)
        self.assertEqual(c.timers[c.current].count, 0)
        [c.tick() for j in xrange(pomodoro.WORK)]
        self.assertEqual(c.current, 'break')
        self.assertEqual(c.phase, 1)
        self.assertEqual(c.timers[c.current].count, 0)
        [c.tick() for j in xrange(pomodoro.BREAK)]

        # phase 2/4
        self.assertEqual(c.current, 'work')
        self.assertEqual(c.phase, 2)
        self.assertEqual(c.timers[c.current].count, 0)
        [c.tick() for j in xrange(pomodoro.WORK)]
        self.assertEqual(c.current, 'break')
        self.assertEqual(c.phase, 2)
        self.assertEqual(c.timers[c.current].count, 0)
        [c.tick() for j in xrange(pomodoro.BREAK)]

        # phase 3/4
        self.assertEqual(c.current, 'work')
        self.assertEqual(c.phase, 3)
        self.assertEqual(c.timers[c.current].count, 0)
        [c.tick() for j in xrange(pomodoro.WORK)]
        self.assertEqual(c.current, 'break')
        self.assertEqual(c.phase, 3)
        self.assertEqual(c.timers[c.current].count, 0)
        [c.tick() for j in xrange(pomodoro.BREAK)]

        # phase 4/4
        self.assertEqual(c.current, 'work')
        self.assertEqual(c.phase, 4)
        self.assertEqual(c.timers[c.current].count, 0)
        [c.tick() for j in xrange(pomodoro.WORK)]
        self.assertEqual(c.current, 'coffee')
        self.assertEqual(c.phase, 4)
        self.assertEqual(c.timers[c.current].count, 0)
        [c.tick() for j in xrange(pomodoro.COFFEE)]

        # phase 1/4
        self.assertEqual(c.current, 'work')
        self.assertEqual(c.phase, 1)
        self.assertEqual(c.timers[c.current].count, 0)
        [c.tick() for j in xrange(pomodoro.WORK)]
        self.assertEqual(c.current, 'break')
        self.assertEqual(c.phase, 1)
        self.assertEqual(c.timers[c.current].count, 0)

    def test_stop(self):
        c = pomodoro.Core()

        c.start()
        c.tick()
        c.tick()
        c.stop()
        self.assertTrue(c.current is None)
        self.assertEqual(c.phase, 0)
        for timer in c.timers.values():
            self.assertEqual(timer.count, 0)

        self.assertRaises(pomodoro.NotYetStarted, c.stop)

    def test_skip(self):
        c = pomodoro.Core()

        self.assertRaises(pomodoro.NotYetStarted, c.skip)

        c.start()
        c.skip()
        self.assertEqual(c.current, 'break')

        [c.skip() for i in xrange(6)]
        self.assertEqual(c.current, 'coffee')
        self.assertEqual(c.phase, 4)
        c.skip()
        self.assertEqual(c.current, 'work')
        self.assertEqual(c.phase, 1)


class TestUIFunctions(unittest.TestCase):

    def test_init(self):
        ui = pomodoro.UI()

        button = ui.buttons['begin']

    def test_buzz(self):
        ui = pomodoro.UI()

        ui.buzz()

    def test_begin_cb(self):
        ui = pomodoro.UI()

        button = ui.buttons['begin']
        self.assertEqual(button.get_children()[0], ui.images['play'])
        ui.begin_toggle()
        self.assertEqual(button.get_children()[0], ui.images['pause'])
        ui.begin_toggle()
        self.assertEqual(button.get_children()[0], ui.images['play'])
        ui.begin_toggle()
        self.assertEqual(button.get_children()[0], ui.images['pause'])

    def test_skip(self):
        ui = pomodoro.UI()
        
        ui.skip()

    def test_set_title(self):
        ui = pomodoro.UI()

        ui.set_text('foo')
        self.assertEqual(ui.text, 'foo')

    def test_set_text(self):
        ui = pomodoro.UI()

        ui.set_text('foo')
        self.assertEqual(ui.text, 'foo')

    def test_set_fraction(self):
        ui = pomodoro.UI()

        ui.set_fraction(0.5)
        self.assertEqual(ui.fraction, 0.5)

        self.assertRaises(ValueError, ui.set_fraction, -1)
        self.assertRaises(ValueError, ui.set_fraction, 1.1)

    def test_set_label(self):
        ui = pomodoro.UI()

        ui.set_label('foo')
        self.assertEqual(ui.label, 'foo')


class TestPlayerFunctions(unittest.TestCase):

    def test_init(self):
        p = pomodoro.Player()

        self.assertEqual(p.started, False)

    def test_start(self):
        p = pomodoro.Player()

        p.start()
        self.assertEqual(p.started, True)

        self.assertRaises(pomodoro.AlreadyStarted, p.start)

    def test_stop(self):
        p = pomodoro.Player()
        
        p.start()
        p.stop()
        self.assertEqual(p.started, False)

        self.assertRaises(pomodoro.NotYetStarted, p.stop)



if __name__ == '__main__':
    unittest.main()
