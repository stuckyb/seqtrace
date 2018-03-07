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


class Observable(object):
    """
    A mixin class to provide basic observable functionality to child classes.
    Implements the ability to define event types and register/unregister clients
    to receive event notifications.
    """
    def defineObservableEvents(self, event_names):
        """
        event_names: A list of event name strings.
        """
        try:
            self._observers
        except AttributeError:
            self._observers = {}

        for event_name in event_names:
            if event_name not in self._observers:
                self._observers[event_name] = set()

    def registerObserver(self, event_name, observer, regID = None):
        """
        Registers a new observer that will be notified whenever event_name
        occurs.

        event_name (string): The event name to observe.
        observer: A callable object (typically a function or method) with an
            interface that matches the arguments passed when event_name occurs.
        regID: A value that serves as an identifier for this observer
            registration.  If provided, the ID will always be passed to
            observers when a notification occurs.
        """
        try:
            self._observers[event_name].add((observer, regID))
        except KeyError:
            raise UnrecognizedEventError(event_name)

    def unregisterObserver(self, event_name, observer):
        """
        Removes an observer from the list of observers that will be notified
        when event_name occurs.
        """
        try:
            to_delete = []
            for observer_reg in self._observers[event_name]:
                if observer_reg[0] == observer:
                    to_delete.append(observer_reg)

            for observer_reg in to_delete:
                self._observers[event_name].remove(observer_reg)

        except KeyError:
            raise UnrecognizedEventError(event_name)

    def notifyObservers(self, event_name, args):
        """
        Notify all observers registered for event_name.  Notification arguments
        are provided as an iterable that will be unpacked when calling the
        observer.  If a registration ID was provided when the observer was
        registered, it will be passed as the first argument to the observer.

        event_name (string): The event name for which to send notifications.
        args: An iterable of arguments to send to the observer.
        """
        try:
            for observer_reg in self._observers[event_name]:
                if observer_reg[1] is not None:
                    observer_reg[0](observer_reg[1], *args)
                else:
                    observer_reg[0](*args)
        except KeyError as e:
            raise UnrecognizedEventError(event_name)

