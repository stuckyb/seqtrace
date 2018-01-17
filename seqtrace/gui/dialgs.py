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


import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk


# constant for the "yes to all" response
YES_TO_ALL = 1


class CommonDialogs:
    """
    A mixin class to add common message dialog functionality to classes that
    inherit from Gtk.Window.  The methods essentially act as facades to the GTK
    MessageDialog class.
    """
    def showMessage(self, message, mtype=Gtk.MessageType.ERROR):
        msg = Gtk.MessageDialog(
            self, Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
            mtype, Gtk.ButtonsType.OK, message
        )
        response = msg.run()
        msg.destroy()
    
    def showYesNoDialog(self, message, mtype=Gtk.MessageType.QUESTION):
        msg = Gtk.MessageDialog(
            self, Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
            Gtk.MessageType.QUESTION, Gtk.ButtonsType.YES_NO, message
        )
        response = msg.run()
        msg.destroy()
        
        return response

    def showYesNoCancelDialog(self, message, mtype=Gtk.MessageType.QUESTION):
        msg = Gtk.MessageDialog(
            self, Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
            Gtk.MessageType.QUESTION, Gtk.ButtonsType.NONE, message
        )
        msg.add_buttons(Gtk.STOCK_YES, Gtk.ResponseType.YES, Gtk.STOCK_NO, Gtk.ResponseType.NO,
                Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)
        msg.set_default_response(Gtk.ResponseType.CANCEL)
        response = msg.run()
        msg.destroy()

        return response

    def showYesToAllDialog(self, message, mtype=Gtk.MessageType.QUESTION):
        """
        Shows a "yes to all" dialog, which also contains "yes", "no", and
        "cancel" buttons.
        """
        msg = Gtk.MessageDialog(
            self, Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
            Gtk.MessageType.QUESTION, Gtk.ButtonsType.NONE, message
        )
        msg.add_buttons('Yes to All', YES_TO_ALL, Gtk.STOCK_YES, Gtk.ResponseType.YES,
                Gtk.STOCK_NO, Gtk.ResponseType.NO, Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)
        msg.set_default_response(Gtk.ResponseType.YES)
        response = msg.run()
        msg.destroy()

        return response


class EntryDialog(Gtk.Dialog):
    """
    Defines a simple text entry dialog with a single text entry box.
    """
    def __init__(self, parent, title, prompt, init_text, entry_width=20):
        Gtk.Dialog.__init__(
            self, title, parent,
            Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
            (Gtk.STOCK_OK, Gtk.ResponseType.OK, Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)
        )
        self.set_default_response(Gtk.ResponseType.OK)

        vb = Gtk.VBox()
        vb.set_border_width(14)

        hb1 = Gtk.HBox()
        hb1.pack_start(Gtk.Label(prompt), False, True, 0)
        vb.pack_start(hb1, True, True, 0)

        hb2 = Gtk.HBox()
        self.entry = Gtk.Entry()
        self.entry.set_width_chars(entry_width)
        self.entry.set_activates_default(True)
        self.entry.set_text(init_text)
        hb2.pack_start(self.entry, False, True, 0)
        vb.pack_start(hb2, True, True, 0)

        self.vbox.pack_start(vb, True, True, 0)
        self.vbox.show_all()

    def get_text(self):
        return self.entry.get_text()


class ProgressBarDialog(Gtk.Window):
    """
    Defines a simple, non-blocking dialog window for displaying a progress bar
    and a cancel button.
    """
    def __init__(self, parent=None, msg='Progress...', title=''):
        Gtk.Window.__init__(self, Gtk.WindowType.TOPLEVEL)
        self.connect('delete-event', self.deleteWindow)

        self.is_canceled = False

        self.set_title(title)

        # associate this window with its parent and make it modal
        self.set_transient_for(parent)
        self.set_destroy_with_parent(True)
        self.set_modal(True)

        self.vbox = Gtk.VBox(False, 14)
        self.vbox.set_border_width(14)
        self.add(self.vbox)

        # create the message label
        label = Gtk.Label(label=msg)
        self.vbox.pack_start(label, True, True, 0)

        # create the progress bar
        self.pb = Gtk.ProgressBar()
        self.pb.set_orientation(Gtk.Orientation.HORIZONTAL)
        self.pb.set_inverted(False)
        self.pb.set_text('0%')
        self.vbox.pack_start(self.pb, True, True, 0)

        # create the 'Close' button
        bbox = Gtk.HButtonBox()
        bbox.set_layout(Gtk.ButtonBoxStyle.END)
        self.button = Gtk.Button('Cancel', Gtk.STOCK_CANCEL)
        self.button.connect('clicked', self.cancelPressed)
        bbox.add(self.button)
        self.vbox.pack_start(bbox, True, True, 0)

        self.vbox.show_all()
        self.set_position(Gtk.WindowPosition.CENTER_ON_PARENT)

    def show(self):
        Gtk.Window.show(self)

        # Give the dialog window a chance to display.
        while Gtk.events_pending():
           Gtk.main_iteration()

    def updateProgress(self, fraction):
        self.pb.set_fraction(fraction)

        self.pb.set_text(str(int(fraction * 100)) + '%')

        if fraction >= 1.0:
            self.button.set_sensitive(False)

        # Give the progress bar a chance to actually update its display.
        while Gtk.events_pending():
           Gtk.main_iteration()

    def getIsCanceled(self):
        return self.is_canceled

    def cancelPressed(self, widget):
        self.is_canceled = True
        self.button.set_sensitive(False)

    def deleteWindow(self, widget, data):
        self.is_canceled = True

        return True


if __name__ == '__main__':
    import time

    pbwin = ProgressBarDialog(None, 'Working on some task that requires a lot of time and effort...')

    for cnt in range(100):
        pbwin.updateProgress(float(cnt) / 99)
        if pbwin.getIsCanceled():
            break
        time.sleep(1)
