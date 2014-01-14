# Copyright (C) 2014 Brian J. Stucky
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


class Observable:
    """
    A mixin class to provide basic observable functionality to child classes.
    Implements the ability to define event types and register/unregister clients
    to receive event notifications.
    """
    def defineObservableEvents(self, event_names):
        self.__observers = {}

        for event_name in event_names:
            self.__observers[event_name] = []

    def registerObserver(self, event_name, observer):
        try:
            self.__observers[event_name].append(observer)
        except KeyError:
            raise UnrecognizedEventError(event_name)

    def unregisterObserver(self, event_name, observer):
        try:
            if observer in self.__observers[event_name]:
                self.__observers[event_name].remove(observer)
        except KeyError:
            raise UnrecognizedEventError(event_name)

    def notifyObservers(self, event_name, args):
        try:
            for observer in self.__observers[event_name]:
                observer(*args)
        except KeyError as e:
            raise UnrecognizedEventError(event_name)



