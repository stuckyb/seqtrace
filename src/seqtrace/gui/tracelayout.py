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


class SequenceTraceLayout(Gtk.VBox):
    """
    Manages the layout of one or two scrollable sequence trace viewers and a
    scrollable consensus sequence viewer.  Handles communication among these
    two or three components, such as navigating the trace views by clicking on
    the consensus view and synchronized scrolling of the two trace viewers.
    Also provides a toolbar to manage the appearance of the trace viewers.
    """
    def __init__(self, scrolled_cons_viewer, seqt_viewers):
        Gtk.VBox.__init__(self)
        self.consv = scrolled_cons_viewer

        self.seqt_viewers = seqt_viewers
        self.selected_seqtv = 0

        self.zoom_levels = [25, 50, 75, 100, 125, 150, 200, 300, 400]
        self.curr_zoom = 3

        # save the starting y-scale max values for each viewer
        self.start_yscalemax = []
        for viewer in self.seqt_viewers:
            self.start_yscalemax.append(viewer.getYScaleMax())

        self.toolbar = self.createTraceToolBar()
        #self.pack_start(toolbar, False, False)

        for viewer in self.seqt_viewers:
            self.pack_start(viewer.getWidget(), True, True, 0)
        self.pack_start(self.consv, False, True, 0)

        # If there are two trace viewers, initialize synchronized scrolling.
        self.scroll_locked = False
        if len(self.seqt_viewers) == 2:
            # Initialize the synchronized scrolling when the VBox requests to
            # be mapped to the display so that we get the correct adjustment
            # values.
            self.connect('map', self.initializeLockedScrolling)

        # Register callbacks for the consensus sequence viewer.
        self.consv.getConsensusSequenceViewer().registerObserver(
            'alignment_clicked', self.alignmentClicked
        )

        self.connect('destroy', self.destroyed)

    def getFontDescription(self):
        """
        Returns the font description used by the layout components.  (Actually,
        returns only the font description used by the first
        SequenceTraceViewer, which should be the same as for the other
        components.)
        """
        return self.seqt_viewers[0].getFontDescription()

    def setFontDescription(self, fontdesc, adjust_scroll=True):
        """
        Sets the font description to be used by the layout components
        (SequenceTraceViewer(s) and the ScrolledConsensusSequenceViewer).

        fontdesc: A Pango.FontDescription object.
        adjust_scroll: If True, the scroll bar positions of the trace and
            sequence viewers will be adjusted.
        """
        # If there are two trace viewers and their scrolling is synchronized,
        # unlock them before changing the font.
        relock = self.scroll_locked
        if self.scroll_locked:
            self.unlockScrolling()

        for viewer in self.seqt_viewers:
            viewer.setFontDescriptionAndRescale(fontdesc, adjust_scroll)

        # Relock the scrollbars, if needed.
        if relock:
            self.lockScrolling()

        self.consv.setFontDescription(fontdesc, adjust_scroll)

    def alignmentClicked(self, seqnum, seq1index, seq2index):
        # If there are two trace viewers and their scrolling is synchronized,
        # unlock them before jumping to the clicked position in the alignment.
        relock = self.scroll_locked
        if self.scroll_locked:
            self.unlockScrolling()

        #print seqnum, seq1index, seq2index
        self.seqt_viewers[0].scrollTo(seq1index)
        self.seqt_viewers[0].getViewer().highlightBase(seq1index)
        if len(self.seqt_viewers) == 2:
            self.seqt_viewers[1].scrollTo(seq2index)
            self.seqt_viewers[1].getViewer().highlightBase(seq2index)

        # If scroll synchronization was initially enabled, relock the scrollbars.
        if relock:
            self.lockScrolling()

    def initializeLockedScrolling(self, widget):
        """
        Initializes synchronized scrolling for two trace viewers.  Initially locks
        the traces at the location of the first shared position in the alignment.
        This does not result in perfect matching throughout the traces, but is still
        more useful than initially locking them both at their beginnings.
        """
        # Create lists for the scroll adjustments and signal handler IDs.
        self.adjs = []
        self.adj_hids = []

        # Retrieve the scroll adjustments and set up the event handlers.
        self.adjs.append(self.seqt_viewers[0].scrolledwin.get_hadjustment())
        self.adj_hids.append(self.adjs[0].connect('value_changed', self.traceScrolled, 0))

        self.adjs.append(self.seqt_viewers[1].scrolledwin.get_hadjustment())
        self.adj_hids.append(self.adjs[1].connect('value_changed', self.traceScrolled, 1))

        # A list to track the offsets between the two scroll adjustments when
        # they are locked together.
        self.adj_offsets = [0.0, 0.0]

        csb = self.consv.getConsensusSequenceViewer().getConsensSeqBuilder()
        seq0 = csb.getAlignedSequence(0)
        seq1 = csb.getAlignedSequence(1)

        # Get the positions of the first overlapping bases in the alignment
        # (i.e., the start of the left end gap).
        lgindex = csb.getLeftEndGapStart()

        # Verify that there is actually a left end gap and overlapping bases.
        if lgindex > 0 and seq0[lgindex] != '-' and seq1[lgindex] != '-':
            # Figure out which trace has the left end gap.
            if seq0[lgindex - 1] == '-':
                seq0index = 0
                seq1index = lgindex
            else:
                seq0index = lgindex
                seq1index = 0
                
            seqt0 = self.seqt_viewers[0].getSequenceTrace()
            seqt1 = self.seqt_viewers[1].getSequenceTrace()

            # Get the locations of the bases in each trace.
            bpos0 = (
                float(seqt0.getBaseCallPos(seq0index)) /
                seqt0.getTraceLength() * self.adjs[0].get_upper()
            )
            bpos1 = (
                float(seqt1.getBaseCallPos(seq1index)) /
                seqt1.getTraceLength() * self.adjs[1].get_upper()
            )
        else:
            # Either there is no left end gap or no overlapping bases, so just
            # set the offsets to 0.
            bpos0 = bpos1 = 0

        # Set the starting offsets.
        self.adj_offsets[0] = bpos0 - bpos1
        self.adj_offsets[1] = bpos1 - bpos0
        #self.adj_offsets = [0.0, 0.0]

        self.scroll_locked = True

    def lockScrolling(self):
        if self.scroll_locked:
            return

        self.adjs[0].handler_unblock(self.adj_hids[0])
        self.adjs[1].handler_unblock(self.adj_hids[1])

        # Save the offsets between the positions of the two adjustments.
        self.adj_offsets[0] = self.adjs[0].get_value() - self.adjs[1].get_value()
        self.adj_offsets[1] = self.adjs[1].get_value() - self.adjs[0].get_value()

        self.scroll_locked = True

    def unlockScrolling(self):
        if not(self.scroll_locked):
            return

        self.adjs[0].handler_block(self.adj_hids[0])
        self.adjs[1].handler_block(self.adj_hids[1])

        self.scroll_locked = False

    def traceScrolled(self, adj, index):
        #print 'min', index, adj.get_lower()
        #print 'max:', adj.get_upper()
        #print 'page size:', adj.get_page_size()
        #print adj.get_value()

        # Get the index of the other (non event-triggering) adjustment.
        index2 = (index + 1) % 2

        # Avoid triggering a cascade of events.
        self.adjs[index2].handler_block(self.adj_hids[index2])

        # Calculate the position of the other scrollbar adjustment.
        value2 = adj.get_value() - self.adj_offsets[index]

        # Update the other scroll adjustment if we're not outside of its bounds.
        if value2 >= 0.0 and value2 <= (self.adjs[index2].get_upper() - self.adjs[index2].get_page_size()):
            self.adjs[index2].set_value(value2)

        # Re-enable the signal handler for the adjustment.
        self.adjs[index2].handler_unblock(self.adj_hids[index2])

    def getTraceToolBar(self):
        return self.toolbar

    def createTraceToolBar(self):
        toolbar = Gtk.Toolbar()
        #toolbar.set_orientation(Gtk.Orientation.VERTICAL)
        #toolbar.set_icon_size(Gtk.IconSize.MENU)
        toolbar.set_icon_size(Gtk.IconSize.LARGE_TOOLBAR)
        toolbar.set_style(Gtk.ToolbarStyle.ICONS)
        toolbar.set_show_arrow(False)

        # build the zoom controls
        self.zoomin_button = Gtk.ToolButton(Gtk.STOCK_ZOOM_IN)
        self.zoomin_button.set_homogeneous(False)
        self.zoomin_button.set_tooltip_text('Zoom in')
        self.zoomin_button.connect('clicked', self.zoomButtons, 1)
        toolbar.insert(self.zoomin_button, -1)

        self.zoomout_button = Gtk.ToolButton(Gtk.STOCK_ZOOM_OUT)
        self.zoomout_button.set_homogeneous(False)
        self.zoomout_button.set_tooltip_text('Zoom out')
        self.zoomout_button.connect('clicked', self.zoomButtons, -1)
        toolbar.insert(self.zoomout_button, -1)

        self.zoom_combo = Gtk.ComboBoxText()
        for zoom in self.zoom_levels:
            self.zoom_combo.append_text(str(zoom) + '%')
        self.zoom_combo.set_active(self.curr_zoom)
        self.zoom_combo.connect('changed', self.zoomComboBox)

        # place the combo box in a VButtonBox to prevent it from expanding vertically
        vbox = Gtk.VButtonBox()
        vbox.pack_start(self.zoom_combo, False, True, 0)
        t_item = Gtk.ToolItem()
        t_item.add(vbox)
        t_item.set_tooltip_text('Adjust the zoom level')
        t_item.set_expand(False)
        toolbar.insert(t_item, -1)

        toolbar.insert(Gtk.SeparatorToolItem(), -1)

        # build the y scale adjustment slider
        t_item = Gtk.ToolItem()
        t_item.add(Gtk.Label(label='Y:'))
        toolbar.insert(t_item, -1)

        self.vscale_adj = Gtk.Adjustment(0, 0, 0)
        # It appears that there is currently no Python-style constructor
        # available for Gtk.Scale(), so instead of the commented-out line
        # below, we have to explicitly use the C constructor.
        hslider = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=self.vscale_adj)
        #hslider = Gtk.Scale.new(Gtk.Orientation.HORIZONTAL, self.vscale_adj)
        hslider.set_draw_value(False)
        self.initYScaleSlider(self.selected_seqtv)

        sizereq = hslider.get_size_request()
        hslider.set_size_request(60, sizereq.height)

        self.y_slider = Gtk.ToolItem()
        self.y_slider.add(hslider)
        self.y_slider.set_tooltip_text('Adjust the Y scale of the trace view')
        toolbar.insert(self.y_slider, -1)

        self.vscale_adj.connect('value_changed', self.yScaleChanged)

        toolbar.insert(Gtk.SeparatorToolItem(), -1)

        # build the toggle button for phred scores
        toggle = Gtk.CheckButton()
        toggle.set_label('conf. scores')
        toggle.set_active(True)
        toggle.connect('toggled', self.showConfToggled)

        # place the toggle button in a VButtonBox to prevent it from expanding vertically
        vbox = Gtk.VButtonBox()
        vbox.pack_start(toggle, False, True, 0)
        t_item = Gtk.ToolItem()
        t_item.add(vbox)
        t_item.set_tooltip_text('Turn the display of phred scores on or off')
        t_item.set_expand(False)
        toolbar.insert(t_item, -1)

        # if we got two sequences, build a combo box to choose between them
        if len(self.seqt_viewers) == 2:
            trace_combo = Gtk.ComboBoxText()

            # see if the forward trace is first or second
            if self.seqt_viewers[0].getSequenceTrace().isReverseComplemented():
                trace_combo.append_text('Reverse:')
                trace_combo.append_text('Forward:')
            else:
                trace_combo.append_text('Forward:')
                trace_combo.append_text('Reverse:')
            trace_combo.append_text('Both:')
            trace_combo.set_active(0)
            trace_combo.connect('changed', self.traceComboBox)

            # place the combo box in a VButtonBox to prevent it from expanding vertically
            vbox = Gtk.VButtonBox()
            vbox.pack_start(trace_combo, False, True, 0)
            t_item = Gtk.ToolItem()
            t_item.add(vbox)
            #t_item.set_tooltip_text('Adjust the zoom level')
            toolbar.insert(t_item, 0)

            trace_combo.set_active(2)

        return toolbar
    
    def traceComboBox(self, trace_combo):
        self.selected_seqtv = trace_combo.get_active()

        if self.selected_seqtv == len(self.seqt_viewers):
            self.y_slider.set_sensitive(False)
        else:
            # set up the y-scale slider
            self.y_slider.set_sensitive(True)
            self.initYScaleSlider(self.selected_seqtv)

    def initYScaleSlider(self, viewer_index):
        curr_smax = self.seqt_viewers[viewer_index].getYScaleMax()
        smin = 100
        if curr_smax < smin:
            smin = curr_smax
        self.vscale_adj.set_lower(smin)
        self.vscale_adj.set_upper(self.start_yscalemax[viewer_index])
        self.vscale_adj.set_value(curr_smax)

    def yScaleChanged(self, adj):
        val = adj.get_value()
        self.seqt_viewers[self.selected_seqtv].setYScaleMax(val)

    def showConfToggled(self, toggle):
        if self.selected_seqtv == len(self.seqt_viewers):
            for viewer in self.seqt_viewers:
                viewer.setShowConfidence(toggle.get_active())
        else:
            self.seqt_viewers[self.selected_seqtv].setShowConfidence(toggle.get_active())

    def zoomButtons(self, button, increment):
        """
        Handles clicks on the "+"/"-" zoom buttons by translating them to changes
        of the zoom level combo box, which manages the actual zooming.
        """
        self.zoom_combo.set_active(self.curr_zoom + increment)

    def zoomComboBox(self, combobox):
        """
        Responds to changes of the zoom level combo box by enabling or disabling
        the "+"/"-" zoom buttons as appropriate and triggering the change in zoom
        level on the selected trace viewer(s).
        """
        self.curr_zoom = self.zoom_combo.get_active()

        # Check if we need to enable or disable any of the zoom buttons.
        if self.curr_zoom == (len(self.zoom_levels) - 1):
            self.zoomin_button.set_sensitive(False)
        elif not(self.zoomin_button.get_sensitive()):
            self.zoomin_button.set_sensitive(True)

        if self.curr_zoom == 0:
            self.zoomout_button.set_sensitive(False)
        elif not(self.zoomout_button.get_sensitive()):
            self.zoomout_button.set_sensitive(True)

        # If there are two trace viewers and their scrolling is synchronized,
        # unlock them before triggering the zoom.
        relock = self.scroll_locked
        if self.scroll_locked:
            self.unlockScrolling()

        # Zoom the trace viewer(s).
        if self.selected_seqtv == len(self.seqt_viewers):
            for viewer in self.seqt_viewers:
                viewer.zoom(self.zoom_levels[self.curr_zoom])
        else:
            self.seqt_viewers[self.selected_seqtv].zoom(self.zoom_levels[self.curr_zoom])

        # If scroll synchronization was initially enabled, relock the scrollbars.
        if relock:
            self.lockScrolling()

    def destroyed(self, widget):
        # Unregister this widget as an observer of the consensus sequence viewer.
        self.consv.getConsensusSequenceViewer().unregisterObserver('alignment_clicked', self.alignmentClicked)

