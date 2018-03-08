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



class ObservableError(Exception):
    pass

class UnrecognizedEventError(ObservableError):
    def __init__(self, event_name):
        self.event_name = event_name

    def __str__(self):
        return ('The event name "' + self.event_name + 
                '" is not a recognized observable event supported by this class.')

class InvaledRegistrationIDError(ObservableError):
    def __init__(self, reg_id):
        self.reg_id = reg_id

    def __str__(self):
        return (
            'The registration ID {0} is not a valid registration ID for this '
            'observable.'.format(self.reg_id)
        )


class _ObserverReg(object):
    """
    A simple struct-like class that contains the data for a single observer
    registration.
    """
    def __init__(self, reg_id, observer, dataval):
        self.reg_id = reg_id
        self.observer = observer
        self.dataval = dataval

    def __eq__(self, other):
        """
        Use only the observer and dataval values for hashing and equality
        comparisons, because the registration ID is not semantically meaningful
        for deciding equality.
        """
        return (
            (self.observer == other.observer) and
            (self.dataval == other.dataval)
        )

    def __hash__(self):
        """
        Use only the observer and dataval values for hashing and equality
        comparisons, because the registration ID is not semantically meaningful
        for deciding equality.
        """
        return hash((self.observer, self.dataval))


class Observable(object):
    """
    A mixin class to provide basic observable functionality to child classes.
    Implements the ability to define event types and register/unregister clients
    to receive event notifications.
    """
    def defineObservableEvents(self, event_names):
        """
        This method initializes the Observable and defines the event names.
        This method must be called prior to registering any observers.

        event_names: A list of event name strings.
        """
        # An incrementing integer for generating new observer registration IDs.
        self._cur_reg_id = 0

        # A set of all registration IDs in current use.
        self._reg_ids = set()

        # A set of all blocked observer registrations.
        self._blocked_reg_ids = set()

        try:
            self._observers
        except AttributeError:
            self._observers = {}

        for event_name in event_names:
            if event_name not in self._observers:
                self._observers[event_name] = set()

    def registerObserver(self, event_name, observer, dataval=None):
        """
        Registers a new observer that will be notified whenever event_name
        occurs.  Returns the ID for the registration if the registration
        succeeded, return -1 otherwise (i.e., if the observer/dataval pair is
        already registered).

        event_name (string): The event name to observe.
        observer: A callable object (typically a function or method) with an
            interface that matches the arguments passed when event_name occurs.
        dataval: A data value to pass to observers at event notifications.
        """
        if event_name not in self._observers:
            raise UnrecognizedEventError(event_name)

        new_reg = _ObserverReg(self._cur_reg_id, observer, dataval)

        if new_reg not in self._observers[event_name]:
            self._observers[event_name].add(new_reg)
            self._reg_ids.add(self._cur_reg_id)
            self._cur_reg_id += 1

            return self._cur_reg_id - 1
        else:
            return -1

    def unregisterObserver(self, event_name, observer):
        """
        Removes all registrations for an observer from the set of observers
        that will be notified when event_name occurs.
        """
        try:
            to_delete = []
            for observer_reg in self._observers[event_name]:
                if observer_reg.observer == observer:
                    to_delete.append(observer_reg)

            for observer_reg in to_delete:
                self._reg_ids.remove(observer_reg.reg_id)
                if observer_reg.reg_id in self._blocked_reg_ids:
                    self._blocked_reg_ids.remove(observer_reg.reg_id)
                self._observers[event_name].remove(observer_reg)

        except KeyError:
            raise UnrecognizedEventError(event_name)

    def blockObserver(self, reg_id):
        """
        Prevents an observer from being notified of events.

        reg_id: The registration ID to block.
        """
        if reg_id not in self._reg_ids:
            raise InvaledRegistrationIDError(reg_id)

        self._blocked_reg_ids.add(reg_id)

    def unblockObserver(self, reg_id):
        """
        Restores notifications to an observer.

        reg_id: The registration ID to unblock.
        """
        if reg_id not in self._reg_ids:
            raise InvaledRegistrationIDError(reg_id)

        if reg_id in self._blocked_reg_ids:
            self._blocked_reg_ids.remove(reg_id)

    def notifyObservers(self, event_name, args):
        """
        Notify all observers registered for event_name.  Notification arguments
        are provided as an iterable that will be unpacked when calling the
        observer.  If a data value was provided when the observer was
        registered, it will be passed as the first argument to the observer.

        event_name (string): The event name for which to send notifications.
        args: An iterable of arguments to send to the observer.
        """
        try:
            for observer_reg in self._observers[event_name]:
                if observer_reg.reg_id not in self._blocked_reg_ids:
                    if observer_reg.dataval is not None:
                        observer_reg.observer(observer_reg.dataval, *args)
                    else:
                        observer_reg.observer(*args)
        except KeyError as e:
            raise UnrecognizedEventError(event_name)

