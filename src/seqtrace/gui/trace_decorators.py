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

from seqtrace.core.observable import Observable


class SequenceTraceViewerDecorator(object):
    """
    Base class for all SequenceTraceViewer decorators.  This class is not
    abstract, but it does not add any functionality to a SequenceTraceViewer.
    """
    def __init__(self, sequencetraceviewer):
        """
        sequencetraceviewer: An instance of SequenceTraceViewer or
            SequenceTraceViewerDecorator.
        """
        self.viewer = sequencetraceviewer

    def getViewer(self):
        return self.viewer

    def setViewer(self, sequencetraceviewer):
        self.viewer = sequencetraceviewer

    # delegate all other operations to the decorated object
    def __getattr__(self, attr):
        return getattr(self.viewer, attr)


class FwdRevSTVDecorator(SequenceTraceViewerDecorator):
    """
    Adds a label to the left of a SequenceTraceViewer or a
    SequenceTraceViewerDecorator (i.e., a decorated SequenceTraceViewer) that
    indicates whether it is a forward or reverse sequencing trace.
    """
    def __init__(self, sequencetraceviewer):
        """
        sequencetraceviewer: An instance of SequenceTraceViewer or
            SequenceTraceViewerDecorator (i.e., a decorated
            SequenceTraceViewer).
        """
        SequenceTraceViewerDecorator.__init__(self, sequencetraceviewer)

        self.hbox = Gtk.HBox()

        label = Gtk.Label()
        label.set_angle(90)

        if (sequencetraceviewer.getSequenceTrace().isReverseComplemented()):
            labeltxt = 'Reverse'
        else:
            labeltxt = 'Forward'

        label.set_markup(labeltxt)

        frame = Gtk.Frame()
        frame.set_shadow_type(Gtk.ShadowType.IN)
        #frame.add(label)

        self.hbox.pack_start(label, False, True, 0)
        self.hbox.pack_start(self.viewer.getWidget(), True, True, 0)

        self.hbox.show_all()

    def getWidget(self):
        return self.hbox


class _STVRescrollData:
    """
    A simple struct-like class used by ScrollAndZoomSTVDecorator to store size
    and scroll state information to properly handle zoom events or font changes
    that change the size of the underlying SequenceTraceViewer's DrawingArea.
    """
    def __init__(self):
        # The old allocated width of the SequenceTraceViewer's DrawingArea.
        self.oldwidth = 0

        # A float between 0 and 1.0 that specifies the x position (as a
        # proportion of total width) of the SequenceTraceViewer's DrawingArea
        # to center in the visible part of the scrolled view.
        self.oldpos = 0.0

        # Indicates whether the scroll position should be updated.
        self.updatescroll = False


class ScrollAndZoomSTVDecorator(SequenceTraceViewerDecorator, Observable):
    """
    Adds scroll and zoom functionality to a SequenceTraceViewer.  Also manages
    font changes and associated rescaling.
    """
    def __init__(self, sequencetraceviewer):
        """
        sequencetraceviewer: An instance of SequenceTraceViewer.
        """
        SequenceTraceViewerDecorator.__init__(self, sequencetraceviewer)

        self.scrolledwin = Gtk.ScrolledWindow()

        seqt = self.viewer.getSequenceTrace()

        self.zoom_100 = self.calcZoom100ScaleFactor()
        self.zoom_level = 100

        oldwidth, oldheight = self.viewer.getWidget().get_size_request()
        #oldheight = 200
        self.viewer.getWidget().set_size_request(
            int(seqt.getTraceLength() * self.zoom_100), oldheight
        )
        innerhbox = Gtk.HBox(False)
        innerhbox.pack_start(self.viewer.getWidget(), False, False, 0)
        self.scrolledwin.set_policy(Gtk.PolicyType.ALWAYS, Gtk.PolicyType.NEVER)
        self.scrolledwin.add_with_viewport(innerhbox)

        self.rescrolldata = _STVRescrollData()

        self.viewer.getWidget().connect(
            'configure-event', self.traceViewerConfigured
        )

        # Define an event that is triggered when the trace viewport is
        # externally scrolled; that is, when it is not auto-scrolled by code in
        # this class (e.g., as part of a zoom event).
        self.defineObservableEvents(['scroll_external'])
        self.internal_scroll = False

        self.scrolledwin.get_hadjustment().connect(
            'value_changed', self.adjustmentChanged
        )

    def getWidget(self):
        return self.scrolledwin

    def adjustmentChanged(self, adj):
        if self.internal_scroll:
            self.internal_scroll = False
        else:
            self.notifyObservers('scroll_external', (adj,))

        # Allow this event to propagate to other handlers.
        return False

    def calcZoom100ScaleFactor(self):
        """
        Calculate the scale factor for 100% zoom.  This is based on a value of
        2.6 for Droid Sans 11, for which the pixel width of the string '30' is
        16 px and the width of a confidence bar is 12.8.  2.6 gives a visually
        appealing presentation at that font size.  It can be shown
        mathematically that, given a starting font size and drawing width, with
        a new font size it is impossible to find a new drawing width that
        preserves the original spaces between all base calls if they are not
        all evenly spaced.  (Any new drawing width can, at best, preserve a
        single spacing value.)  Thus, the best solution (that I have found,
        anyway), is to use simple proportional scaling according to the
        relative size of the new font and confidence bars, with a scaling
        factor of 2.6 with Droid Sans 11 as a reference.  This ensures that the
        relative spaces between base call confidence bars will remain the same
        across all font sizes.
        """
        cbarwidth = self.viewer.getConfBarWidth()

        return 2.6 * (cbarwidth / 12.8)

    def setFontDescriptionAndRescale(self, fontdesc, adjust_scroll=True):
        """
        Sets the font description that the underlying SequenceTraceViewer
        should use and rescaled the view window to match the new font metrics.

        fontdesc: A Pango.FontDescription object.
        adjust_scroll: If True, the scroll bar position will be adjusted to
            keep the same part of the trace centered in the viewport (if
            possible).
        """
        self.viewer.setFontDescription(fontdesc)

        new_zoom_100 = self.calcZoom100ScaleFactor()
        if new_zoom_100 != self.zoom_100:
            # We need to rescale the window, so use the zoom() method to handle
            # the rescale.
            self.zoom_100 = new_zoom_100
            self.zoom(self.zoom_level, adjust_scroll)
        else:
            # No need to rescale, so just force a repaint of the trace viewer's
            # drawing area.
            self.viewer.getWidget().queue_draw()

    def traceViewerConfigured(self, widget, event):
        """
        Responds to size changes of the DrawingArea of the underlying
        SequenceTraceViewer to ensure that the correct part of the viewer
        remains centered in the visible part of the window.
        """
        if self.rescrolldata.updatescroll:
            new_width = self.viewer.getWidget().get_allocated_width()

            if self.rescrolldata.oldwidth != new_width:
                # Calculate the new position for the scrollbar to keep the view
                # centered around its previous location.
                adj = self.scrolledwin.get_hadjustment()
                page_size = adj.get_page_size()
    
                newpos = new_width * self.rescrolldata.oldpos
                new_adjval = int(newpos - (page_size / 2))
                if new_adjval < 0:
                    new_adjval = 0
                elif new_adjval > (new_width - page_size):
                    new_adjval = new_width - page_size

                self.internal_scroll = True
                adj.set_value(new_adjval)

            self.rescrolldata.updatescroll = False

    def zoom(self, level, adjust_scroll=True):
        """
        adjust_scroll: If True, the scroll bar position will be adjusted to
            keep the same part of the trace centered in the viewport (if
            possible).
        """
        z_scale = float(level) / 100 * self.zoom_100

        da = self.viewer.getWidget()

        # Calculate the new width for the sequence trace viewer.
        new_width = int(self.viewer.getSequenceTrace().getTraceLength() * z_scale)

        if adjust_scroll:
            # Get the old scrollbar position information.
            adj = self.scrolledwin.get_hadjustment()
            page_size = adj.get_page_size()
            center = adj.get_value() + (page_size / 2)

            self.rescrolldata.oldpos = float(center) / adj.get_upper()
            self.rescrolldata.oldwidth = da.get_allocated_width()
            self.rescrolldata.updatescroll = True

        # Resize the sequence trace viewer.
        oldwidth, oldheight = da.get_size_request()
        if oldwidth != new_width:
            self.viewer.getWidget().set_size_request(new_width, oldheight)

        self.zoom_level = level

    def scrollTo(self, basenum):
        adj = self.scrolledwin.get_hadjustment()
        seqt = self.viewer.getSequenceTrace()

        page_size = adj.get_page_size()
        scend = adj.get_upper() - page_size
        # check if we got a gap position
        if basenum < 0:
            if basenum == -1:
                bpos = 0
            elif (basenum+1) * -1 == seqt.getNumBaseCalls():
                bpos = seqt.getTraceLength() - 1
            else:
                p1 = seqt.getBaseCallPos((basenum+1) * -1)
                p2 = seqt.getBaseCallPos((basenum+2) * -1)
                bpos = (p1 + p2) / 2
        else:
            bpos = seqt.getBaseCallPos(basenum)
        tlen = seqt.getTraceLength()
        x = bpos * scend / tlen
        offset = x * page_size / scend
        x = x + offset - page_size/2
        if x < 0:
            x = 0
        elif x > scend:
            x = scend

        #print adj.lower, adj.upper, adj.value
        self.internal_scroll = True
        adj.set_value(x)

