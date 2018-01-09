#!/usr/bin/python
# Copyright (C) 2018 Brian J. Stucky
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


from seqtrace.core.observable import Observable
import unittest


class ObserverStub:
    """
    A simple class that acts as an observer.
    """
    notified_cnt = 0
    received_vals = None
    def event1Fired(self, arg1, arg2):
        self.notified_cnt += 1
        self.received_vals = (arg1, arg2)


class TestObservable(unittest.TestCase):
    def setUp(self):
        pass

    def test_defineObservableEvents(self):
        obs = Observable()

        obs.defineObservableEvents(['event1'])
        self.assertEqual(1, len(obs._observers))
        self.assertTrue('event1' in obs._observers)

        # Make sure that when we add a new event, it doesn't wipe out the old
        # events.
        obs.defineObservableEvents(['event2'])
        self.assertEqual(2, len(obs._observers))
        self.assertTrue('event1' in obs._observers)
        self.assertTrue('event2' in obs._observers)

        # Make sure that if we "add" the same event twice, it doesn't wipe out
        # observers that are already registered on that event.
        observer = ObserverStub()
        obs.registerObserver('event1', observer.event1Fired)
        self.assertEqual(1, len(obs._observers['event1']))

        obs.defineObservableEvents(['event1'])
        self.assertEqual(1, len(obs._observers['event1']))

    def test_registerObserver(self):
        obs = Observable()

        obs.defineObservableEvents(['event1'])
        self.assertEqual(0, len(obs._observers['event1']))

        observer = ObserverStub()
        obs.registerObserver('event1', observer.event1Fired)
        self.assertEqual(1, len(obs._observers['event1']))

        # Verify that registering the same observer twice doesn't result in
        # duplication.
        obs.registerObserver('event1', observer.event1Fired)
        self.assertEqual(1, len(obs._observers['event1']))

        observer2 = ObserverStub()
        obs.registerObserver('event1', observer2.event1Fired)
        self.assertEqual(2, len(obs._observers['event1']))

    def test_unregisterObserver(self):
        obs = Observable()
        obs.defineObservableEvents(['event1'])

        observer = ObserverStub()
        observer2 = ObserverStub()
        obs.registerObserver('event1', observer.event1Fired)
        obs.registerObserver('event1', observer2.event1Fired)
        self.assertEqual(2, len(obs._observers['event1']))

        obs.unregisterObserver('event1', observer2.event1Fired)
        self.assertEqual(1, len(obs._observers['event1']))
        self.assertTrue(observer.event1Fired in obs._observers['event1'])

        obs.unregisterObserver('event1', observer.event1Fired)
        self.assertEqual(0, len(obs._observers['event1']))

    def test_notifyObservers(self):
        obs = Observable()
        obs.defineObservableEvents(['event1'])
        observer = ObserverStub()
        obs.registerObserver('event1', observer.event1Fired)

        self.assertEqual(0, observer.notified_cnt)
        self.assertIsNone(observer.received_vals)

        obs.notifyObservers('event1', ('arg1val', 2))

        self.assertEqual(1, observer.notified_cnt)
        self.assertEqual(('arg1val', 2), observer.received_vals)

