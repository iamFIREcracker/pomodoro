#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest

from pomodoro import timer



class TestClockFunctions(unittest.TestCase):

    def setUp(self):
        self.clk = timer.Clock()

    def test_start(self):
        self.assertTrue(self.clk.started is None)

        self.clk.start()
        self.assertTrue(self.clk.started != None)

        self.assertRaises(timer.ClockAlreadyStarted, self.clk.start)

    def test_stop(self):
        self.clk.start()
        self.clk.stop()
        self.assertTrue(self.clk.started is None)

        self.assertRaises(timer.ClockNotStarted, self.clk.stop)

    def test_tick(self):
        self.assertTrue(self.clk.tick())



if __name__ == '__main__':
    unittest.main()
