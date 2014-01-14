#!/usr/bin/python
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


import pygtk
pygtk.require('2.0')
import gtk



# constant for the "yes to all" response
YES_TO_ALL = 1


class CommonDialogs:
    """ A mixin class to add common message dialog functionality to classes that inherit
    from gtk.Window.  The methods essentially act as facades to the GTK MessageDialog class. """

    def showMessage(self, message, mtype=gtk.MESSAGE_ERROR):
        msg = gtk.MessageDialog(self, gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT, mtype,
                gtk.BUTTONS_OK, message)
        response = msg.run()
        msg.destroy()
    
    def showYesNoDialog(self, message, mtype=gtk.MESSAGE_QUESTION):
        msg = gtk.MessageDialog(self, gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_QUESTION,
                gtk.BUTTONS_YES_NO, message)
        response = msg.run()
        msg.destroy()
        
        return response

    def showYesNoCancelDialog(self, message, mtype=gtk.MESSAGE_QUESTION):
        msg = gtk.MessageDialog(self, gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_QUESTION,
            gtk.BUTTONS_NONE, message)
        msg.add_buttons(gtk.STOCK_YES, gtk.RESPONSE_YES, gtk.STOCK_NO, gtk.RESPONSE_NO,
                gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
        msg.set_default_response(gtk.RESPONSE_CANCEL)
        response = msg.run()
        msg.destroy()

        return response

    def showYesToAllDialog(self, message, mtype=gtk.MESSAGE_QUESTION):
        """ Shows a "yes to all" dialog, which also contains "yes", "no", and "cancel" buttons. """

        msg = gtk.MessageDialog(self, gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_QUESTION,
            gtk.BUTTONS_NONE, message)
        msg.add_buttons('Yes to All', YES_TO_ALL, gtk.STOCK_YES, gtk.RESPONSE_YES,
                gtk.STOCK_NO, gtk.RESPONSE_NO, gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
        msg.set_default_response(gtk.RESPONSE_YES)
        response = msg.run()
        msg.destroy()

        return response
        


class EntryDialog(gtk.Dialog):
    """ Defines a simple text entry dialog with a single text entry box. """

    def __init__(self, parent, title, prompt, init_text, entry_width=20):
        gtk.Dialog.__init__(self, title, parent, gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                (gtk.STOCK_OK, gtk.RESPONSE_OK, gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))
        self.set_default_response(gtk.RESPONSE_OK)

        vb = gtk.VBox()
        vb.set_border_width(14)

        hb1 = gtk.HBox()
        hb1.pack_start(gtk.Label(prompt), False)
        vb.pack_start(hb1)

        hb2 = gtk.HBox()
        self.entry = gtk.Entry()
        self.entry.set_width_chars(entry_width)
        self.entry.set_activates_default(True)
        self.entry.set_text(init_text)
        hb2.pack_start(self.entry, False)
        vb.pack_start(hb2)

        self.vbox.pack_start(vb)
        self.vbox.show_all()

    def get_text(self):
        return self.entry.get_text()


class ProgressBarDialog(gtk.Window):
    """ Defines a simple, non-blocking dialog window for displaying a progress bar
    and a cancel button. """

    def __init__(self, parent=None, msg='Progress...', title=''):
        gtk.Window.__init__(self, gtk.WINDOW_TOPLEVEL)
        self.connect('delete-event', self.deleteWindow)

        self.is_canceled = False

        self.set_title(title)

        # associate this window with its parent and make it modal
        self.set_transient_for(parent)
        self.set_destroy_with_parent(True)
        self.set_modal(True)

        self.vbox = gtk.VBox(False, 14)
        self.vbox.set_border_width(14)
        self.add(self.vbox)

        # create the message label
        label = gtk.Label(msg)
        self.vbox.pack_start(label)

        # create the progress bar
        self.pb = gtk.ProgressBar()
        self.pb.set_orientation(gtk.PROGRESS_LEFT_TO_RIGHT)
        self.pb.set_text('0%')
        self.vbox.pack_start(self.pb)

        # create the 'Close' button
        bbox = gtk.HButtonBox()
        bbox.set_layout(gtk.BUTTONBOX_END)
        self.button = gtk.Button('Cancel', gtk.STOCK_CANCEL)
        self.button.connect('clicked', self.cancelPressed)
        bbox.add(self.button)
        self.vbox.pack_start(bbox)

        self.vbox.show_all()
        self.set_position(gtk.WIN_POS_CENTER_ON_PARENT)

    def show(self):
        gtk.Window.show(self)

        # give the dialog window a chance to display
        while gtk.events_pending():
           gtk.main_iteration(False)

    def updateProgress(self, fraction):
        self.pb.set_fraction(fraction)

        self.pb.set_text(str(int(fraction * 100)) + '%')

        if fraction >= 1.0:
            self.button.set_sensitive(False)

        # give the progress bar a chance to actually update its display
        while gtk.events_pending():
           gtk.main_iteration(False)

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
