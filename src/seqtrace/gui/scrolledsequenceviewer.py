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
gi.require_version('PangoCairo', '1.0')
from gi.repository import Gtk

from sequenceviewer import ConsensusSequenceViewer


class _CSVRescrollData:
    """
    A simple struct-like class used by ScrolledConsensusSequenceViewer to store
    size and scroll state information to properly handle font changes of the
    contained ConsensusSequenceViewer.
    """
    def __init__(self):
        # The old allocated width of the ConsensusSequenceViewer.
        self.oldwidth = 0

        # A float between 0 and 1.0 that specifies the x position (as a
        # proportion of total width) of the ConsensusSequenceViewer to center
        # in the visible part of the scrolled view.
        self.oldpos = 0.0

        # Indicates whether a font size change was initiated.
        self.fontchanged = False


class ScrolledConsensusSequenceViewer(Gtk.ScrolledWindow):
    def __init__(self, mod_consensseq_builder):
        Gtk.ScrolledWindow.__init__(self)

        self.da = ConsensusSequenceViewer(mod_consensseq_builder)
        self.innerhbox = Gtk.HBox(False)
        self.innerhbox.pack_start(self.da, False, False, 0)
        self.set_policy(Gtk.PolicyType.ALWAYS, Gtk.PolicyType.NEVER)
        self.add_with_viewport(self.innerhbox)

        self.rescrolldata = _CSVRescrollData()

        #self.da.connect('size-request', self.consViewerResized)
        self.da.connect('configure-event', self.consViewerConfigured)

    def consViewerResized(self, widget, req):
        """
        Respond to size request changes by the child ConsensusSequenceViewer.  The
        HBox inside the viewport does not seem to respond properly to changes in its
        child's size request, so take care of that manually here.
        """
        width, height = self.da.get_size_request()
        self.innerhbox.set_size_request(width, height)

    def consViewerConfigured(self, widget, event):
        """
        Responds to ConsensusSequenceViewer size changes that are caused by
        font changes to ensure that the correct part of the viewer remains
        centered in the visible part of the window.
        """
        new_width = self.da.get_allocated_width()

        if self.rescrolldata.fontchanged == True:
            if self.rescrolldata.oldwidth != new_width:
                # Calculate the new position for the scrollbar to keep the view
                # centered around its previous location.
                adj = self.get_hadjustment()
                page_size = adj.get_page_size()
                newpos = new_width * self.rescrolldata.oldpos
                new_adjval = int(newpos - (page_size / 2))
                if new_adjval < 0:
                    new_adjval = 0
                elif new_adjval > (new_width - page_size):
                    new_adjval = new_width - page_size
        
                adj.set_value(new_adjval)

            self.rescrolldata.fontchanged = False

    def getConsensusSequenceViewer(self):
        return self.da

    def setFontDescription(self, fontdesc):
        """
        Sets a new font description for the consensus sequence display and
        tracks display size changes so that the scroll bar position can be
        ajusted to try to keep the same part of the sequence visible.
        """
        # Get the old scrollbar position information.
        adj = self.get_hadjustment()
        page_size = adj.get_page_size()
        center = adj.get_value() + (page_size / 2)

        self.rescrolldata.oldpos = float(center) / adj.get_upper()
        self.rescrolldata.oldwidth = self.da.get_allocated_width()
        self.rescrolldata.fontchanged = True

        # Set the font, which will resize the viewer.
        self.da.setFontDescription(fontdesc)

