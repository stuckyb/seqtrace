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


from seqtrace.core.observable import Observable, InvaledRegistrationIDError
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

    def event2Fired(self, regid, arg1, arg2):
        self.notified_cnt += 1
        self.received_vals = (regid, arg1, arg2)


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
        self.assertEqual(0, len(obs._reg_ids))

        observer = ObserverStub()
        reg_id = obs.registerObserver('event1', observer.event1Fired)
        self.assertEqual(1, len(obs._observers['event1']))
        self.assertEqual(1, len(obs._reg_ids))
        self.assertEqual(0, reg_id)

        # Verify that registering the same observer twice doesn't result in
        # duplication.
        reg_id = obs.registerObserver('event1', observer.event1Fired)
        self.assertEqual(1, len(obs._observers['event1']))
        self.assertEqual(1, len(obs._reg_ids))
        self.assertEqual(-1, reg_id)

        # Verify that registering the same observer twice with different
        # data values does result in two registrations.
        reg_id = obs.registerObserver('event1', observer.event1Fired, 2)
        self.assertEqual(2, len(obs._observers['event1']))
        self.assertEqual(2, len(obs._reg_ids))
        self.assertEqual(1, reg_id)

        observer2 = ObserverStub()
        reg_id = obs.registerObserver('event1', observer2.event1Fired)
        self.assertEqual(3, len(obs._observers['event1']))
        self.assertEqual(3, len(obs._reg_ids))
        self.assertEqual(2, reg_id)

    def test_unregisterObserver(self):
        obs = Observable()
        obs.defineObservableEvents(['event1'])

        observer = ObserverStub()
        observer2 = ObserverStub()
        reg_id1 = obs.registerObserver('event1', observer.event1Fired)
        obs.registerObserver('event1', observer2.event1Fired)
        self.assertEqual(2, len(obs._observers['event1']))
        self.assertEqual(2, len(obs._reg_ids))

        obs.unregisterObserver('event1', observer2.event1Fired)
        self.assertEqual(1, len(obs._observers['event1']))
        self.assertEqual(1, len(obs._reg_ids))
        self.assertTrue(reg_id1 in obs._reg_ids)
        self.assertTrue(
            observer.event1Fired == list(obs._observers['event1'])[0].observer
        )

        obs.unregisterObserver('event1', observer.event1Fired)
        self.assertEqual(0, len(obs._observers['event1']))
        self.assertEqual(0, len(obs._reg_ids))

    def test_notifyObservers(self):
        obs = Observable()
        obs.defineObservableEvents(['event1', 'event2'])
        observer = ObserverStub()
        obs.registerObserver('event1', observer.event1Fired)

        self.assertEqual(0, observer.notified_cnt)
        self.assertIsNone(observer.received_vals)

        obs.notifyObservers('event1', ('arg1val', 2))

        self.assertEqual(1, observer.notified_cnt)
        self.assertEqual(('arg1val', 2), observer.received_vals)

        obs.registerObserver('event2', observer.event2Fired, 1)
        obs.notifyObservers('event2', (3, 'arg2val'))

        self.assertEqual(2, observer.notified_cnt)
        self.assertEqual((1, 3, 'arg2val'), observer.received_vals)

    def test_blockObserver(self):
        obs = Observable()
        obs.defineObservableEvents(['event1'])
        observer1 = ObserverStub()
        reg_id1 = obs.registerObserver('event1', observer1.event1Fired, 'data1')
        reg_id2 = obs.registerObserver('event1', observer1.event1Fired, 'data2')
        observer2 = ObserverStub()
        reg_id3 = obs.registerObserver('event1', observer2.event1Fired, 'data3')

        obs.notifyObservers('event1', ('argval',))
        self.assertEqual(2, observer1.notified_cnt)
        self.assertEqual(1, observer2.notified_cnt)

        # Test blocking and unblocking an observer with only 1 registration.
        obs.blockObserver(reg_id3)

        obs.notifyObservers('event1', ('argval',))
        self.assertEqual(4, observer1.notified_cnt)
        self.assertEqual(1, observer2.notified_cnt)

        obs.unblockObserver(reg_id3)

        obs.notifyObservers('event1', ('argval',))
        self.assertEqual(6, observer1.notified_cnt)
        self.assertEqual(2, observer2.notified_cnt)

        # Test blocking and unblocking an observer with multiple registrations.
        obs.blockObserver(reg_id2)

        obs.notifyObservers('event1', ('argval',))
        self.assertEqual(7, observer1.notified_cnt)
        self.assertEqual(3, observer2.notified_cnt)

        obs.unblockObserver(reg_id2)

        obs.notifyObservers('event1', ('argval',))
        self.assertEqual(9, observer1.notified_cnt)
        self.assertEqual(4, observer2.notified_cnt)

        # Test attempting to block and unblock an invalid registration ID.
        with self.assertRaises(InvaledRegistrationIDError):
            obs.blockObserver(-1)

        with self.assertRaises(InvaledRegistrationIDError):
            obs.unblockObserver(-1)

