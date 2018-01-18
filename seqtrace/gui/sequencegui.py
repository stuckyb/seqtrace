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

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('PangoCairo', '1.0')
from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import Pango
from gi.repository import PangoCairo
import cairo

# Get the Gdk.RGBA convenience functions.
from colorfuncs import parseHTMLColorStr, getInverseColor


class ConsensusSequenceViewer(Gtk.DrawingArea, Observable):
    """
    Implements a widget for displaying a raw sequence or alignment of two raw
    sequences, aligned primers, and a consensus sequence.  Also implements user
    interactions with the sequences.
    """
    def __init__(self, mod_consensseq_builder):
        Gtk.DrawingArea.__init__(self)

        # Since we do all drawing to an off-screen buffer, we don't need GTK's
        # automatic double buffering.
        self.set_double_buffered(False)

        self.cons = mod_consensseq_builder
        self.numseqs = self.cons.getNumSeqs()
        settings = self.cons.getSettings()
        self.drawprimers = settings.getForwardPrimer() != '' and settings.getReversePrimer() != ''

        self.cons.registerObserver('consensus_changed', self.consensusChanged)

        # Initialize drawing settings.
        self.basecolors = {
            'A': parseHTMLColorStr('#009000'),    # green
            'C': parseHTMLColorStr('#0000ff'),    # blue
            'G': parseHTMLColorStr('#000000'),    # black
            'T': parseHTMLColorStr('#ff0000'),    # red
            'W': parseHTMLColorStr('#804800'),    # mix of A and T
            'S': parseHTMLColorStr('#000080'),    # mix of C and G
            'M': parseHTMLColorStr('#004880'),    # mix of A and C
            'K': parseHTMLColorStr('#800000'),    # mix of G and T
            'R': parseHTMLColorStr('#004800'),    # mix of A and G
            'Y': parseHTMLColorStr('#800080'),    # mix of C and T
            'B': parseHTMLColorStr('#550055'),    # mix of C, G, and T
            'D': parseHTMLColorStr('#553000'),    # mix of A, G, and T
            'H': parseHTMLColorStr('#553055'),    # mix of A, C, and T
            'V': parseHTMLColorStr('#003055'),    # mix of A, C, and G
            'N': parseHTMLColorStr('#999'),       # gray
            '-': parseHTMLColorStr('#000'),       # black
            ' ': parseHTMLColorStr('#999')
        }
        self.bgcolors = {
            # These are mostly lighter versions of the foreground colors above.
            'A': parseHTMLColorStr('#cfc'),
            'C': parseHTMLColorStr('#ccf'),
            'G': parseHTMLColorStr('#ccc'),
            'T': parseHTMLColorStr('#fcc'),
            'W': parseHTMLColorStr('#DFD1BF'),    # mix of A and T
            'S': parseHTMLColorStr('#BFBFDF'),    # mix of C and G
            'M': parseHTMLColorStr('#BFD1DF'),    # mix of A and C
            'K': parseHTMLColorStr('#DFBFBF'),    # mix of G and T
            'R': parseHTMLColorStr('#BFD1BF'),    # mix of A and G
            'Y': parseHTMLColorStr('#DFBFDF'),    # mix of C and T
            'B': parseHTMLColorStr('#D5BFD5'),    # mix of C, G, and T
            'D': parseHTMLColorStr('#D5CBBF'),    # mix of A, G, and T
            'H': parseHTMLColorStr('#D5CBD5'),    # mix of A, C, and T
            'V': parseHTMLColorStr('#BFCBD5'),    # mix of A, C, and G
            'N': parseHTMLColorStr('#fff'),
            '-': parseHTMLColorStr('#ff9')
        }

        # Calculate inverses of the main colors for drawing
        # selected/highlighted bases.
        self.basecolors_inv = {}
        for base in self.basecolors:
            self.basecolors_inv[base] = getInverseColor(self.basecolors[base])
        self.bgcolors_inv = {}
        for base in self.bgcolors:
            self.bgcolors_inv[base] = getInverseColor(self.bgcolors[base])

        # The space before the top of the alignment and after the bottom of the
        # consensus sequence.
        self.margins = 6

        # The space between the alignment and the consensus sequence.
        self.padding = 6

        # The location of the top of the alignment.
        self.al_top = self.margins

        self.txtlayout = Pango.Layout(self.create_pango_context())
        self.fontdesc = self.txtlayout.get_context().get_font_description().copy()

        self.setFontSize(10)

        # The index of the currently highlighted position in the alignment.
        self.lastx = -1
        # The index of the currently selected (and highlighted) position in the
        # alignment.
        self.highlighted = -1

        # Keep track of location of an active selection on the consensus
        # sequence. The values are interpreted such that the lower value (which
        # could be either start or end) is the first selected position, and the
        # higher value is 1 beyond the last selected position.
        self.consselect_start = -1
        self.consselect_end = -1
        # keep track of where a selection highlight has been drawn on the consensus sequence
        self.chl_start = -1
        self.chl_end = -1
        # indicates if the user is actively making a selection on the consensus sequence
        self.selecting_active = False

        # Set up event handling.
        self.connect('destroy', self.onDestroy)
        self.connect('draw', self.onDraw)
        self.connect('configure-event', self.onConfigure)

        self.set_events(
            Gdk.EventMask.BUTTON_PRESS_MASK | Gdk.EventMask.BUTTON_RELEASE_MASK
            | Gdk.EventMask.POINTER_MOTION_MASK
            | Gdk.EventMask.POINTER_MOTION_HINT_MASK
            | Gdk.EventMask.LEAVE_NOTIFY_MASK
        )
        self.connect('button-press-event', self.mouseClick)
        self.connect('button-release-event', self.mouseRelease)
        self.connect('motion-notify-event', self.mouseMove)
        self.connect('leave-notify-event', self.mouseLeave)

        # A cairo surface to use as an off-screen buffer for all drawing
        # operations.
        self.surface = None

        self.clickable_cursor = Gdk.Cursor.new(Gdk.CursorType.HAND2)
        self.text_cursor = Gdk.Cursor.new(Gdk.CursorType.XTERM)
        self.curr_cursor = None

        # initialize the observable events for this class
        self.defineObservableEvents([
            'alignment_clicked',
            'consensus_clicked',
            'selection_state'  # triggered when the selection state changes from no selection to one or more bases selected
            ])

    def onDestroy(self, widget):
        # unregister this object as an observer of the consensus sequence
        self.cons.unregisterObserver('consensus_changed', self.consensusChanged)

    def getConsensSeqBuilder(self):
        return self.cons

    def getSelection(self):
        """
        Returns the start and end indexes of the currently active consensus
        sequence selection.  Both indexes are included in the selection.
        """
        start = self.consselect_start
        end = self.consselect_end
        if end < start:
            tmp = start
            start = end
            end = tmp

        return (start, end - 1)

    def mouseClick(self, da, event):
        #numbases = len(self.cons.getAlignedSequence(1))
        alend = self.fheight*self.numseqs + self.al_top
        consend = alend + self.padding + self.fheight
        
        # Calculate the index of the base corresponding to the mouse click.
        bindex = int(event.x / self.fwidth)

        if event.button == 1:
            if (event.y > self.al_top) and (event.y < alend):
                # The mouse is over the alignment display.
                if event.y > (self.al_top + self.fheight):
                    seqnum = 1
                else:
                    seqnum = 0
    
                seq1index = self.cons.getActualSeqIndex(0, bindex)
                if self.numseqs == 2:
                    seq2index = self.cons.getActualSeqIndex(1, bindex)
                else:
                    seq2index = -1
    
                if (self.highlighted != -1) and (self.highlighted != bindex):
                    # Unhighlight the previously selected alignment position.
                    self.highlightAlignment(self.highlighted, False)

                self.highlighted = bindex
                self.notifyObservers('alignment_clicked', (seqnum, seq1index, seq2index))
            elif (event.y > (alend + self.padding)) and (event.y < consend):
                # The mouse was clicked on the consensus sequence display, so
                # initiate a new consensus selection.

                # Determine if the click was on the left or right side of the
                # character.
                if (event.x % self.fwidth) < (self.fwidth / 2):
                    # on the left
                    sel_index = bindex
                else:
                    # on the right
                    sel_index = bindex + 1

                self.updateConsSelection(sel_index, True)

        elif event.button == 3:
            if (event.y > (alend + self.padding)) and (event.y < consend):
                # the mouse is over the consensus sequence display and was right clicked
                self.notifyObservers(
                    'consensus_clicked', (self.consselect_start, self.consselect_end, event)
                )

    def mouseRelease(self, da, event):
        if (event.button == 1) and self.selecting_active:
            self.selecting_active = False

    def mouseLeave(self, da, event):
        # if we just left the window, make sure we erased the highlight
        if (self.lastx != -1) and (self.lastx != self.highlighted):
            self.highlightAlignment(self.lastx, False)
            self.lastx = -1
            return

    def mouseMove(self, da, event):
        index = int(event.x) / self.fwidth

        if self.selecting_active:
            # We are in the process of selecting bases from the consensus
            # sequence.

            # determine if the event was on the left or right side of the character
            if (event.x % self.fwidth) < (self.fwidth / 2):
                # on the left
                s_index = index
            else:
                # on the right
                s_index = index + 1

            self.updateConsSelection(s_index, False)
            #print 'AFTER start, end, index:', self.consselect_start, self.consselect_end, index 

        # Check if the mouse pointer is on the alignment display.
        if (event.y > self.al_top) and (event.y < (self.fheight*self.numseqs + self.al_top)):
            # change the cursor, if necessary
            self.setCursor(self.clickable_cursor)
            
            # draw the highlight and erase the old one, if necessary
            if self.lastx != index:
                if (self.lastx != self.highlighted) or (self.highlighted == -1):
                    self.highlightAlignment(self.lastx, False)
                self.lastx = index
                if index != self.highlighted:
                    self.highlightAlignment(index, True)
        else:
            # not on the alignment, so just erase the old highlight, if necessary
            if (self.lastx != -1) and (self.lastx != self.highlighted):
                self.highlightAlignment(self.lastx, False)
                self.lastx = -1

            alend = self.fheight*self.numseqs + self.al_top
            consend = alend + self.padding + self.fheight
            if (event.y > (alend + self.padding)) and (event.y < consend):
                # the mouse is over the consensus sequence display
                self.setCursor(self.text_cursor)
            else:
                # not on the consensus display, so change back the cursor to the default
                self.setCursor(None)

    def updateConsSelection(self, index, is_new):
        """
        Updates the active consensus sequence selection.

        index: The alignment position corresponding to the mouse selection
            event.
        is_new: If True, this update should initiate a new selection process.
        """
        oldstart = self.consselect_start
        oldend = self.consselect_end

        # This check is necessary because mouse event coordinates can extend
        # outside the DrawingArea display window.
        cons = self.cons.getConsensus()
        if index > len(cons):
            index = len(cons)

        if is_new:
            if self.consselect_start != self.consselect_end:
                # There was a previous selection, so send notification that it
                # is cleared.
                self.notifyObservers('selection_state', (False,))

            self.consselect_start = self.consselect_end = index
            self.selecting_active = True

        elif self.consselect_end != index:
            # An existing selection has changed.

            if self.consselect_start == index:
                # No bases are selected.
                self.consselect_end = self.consselect_start
                self.notifyObservers('selection_state', (False,))

            else:
                # At least one base was selected or unselected and an active
                # selection remains.
                if self.consselect_end == self.consselect_start:
                    # This is a new selection.
                    self.notifyObservers('selection_state', (True,))
                self.consselect_end = index

        if (oldstart != self.consselect_start) or (oldend != self.consselect_end):
            self.updateConsSelDisplay(
                oldstart, oldend, self.consselect_start, self.consselect_end
            )

    def updateConsSelDisplay(self, oldstart, oldend, newstart, newend):
        """
        Updates the consensus sequence selection display.

        oldstart, oldend: The indexes of the old selection.
        newstart, newend: The indexes of the new selection.
        """
        alend = self.fheight*self.numseqs + self.al_top

        # Order the indexes so start <= end.
        if oldend < oldstart:
            tmp = oldstart
            oldstart = oldend
            oldend = tmp
        if newend < newstart:
            tmp = newstart
            newstart = newend
            newend = tmp

        # Calculate which positions in the old selection need to be
        # unhighlighted and which in the new selection need to be highlighted.

        # Initialize two lists to accumulate regions (stored as pairs of
        # indexes) that need to be highlighted or unhighlighted.
        unhl = []
        hl = []
        if (oldend < newstart) or (newend < oldstart):
            # No overlap between the old and new selections, so unhighlight the
            # entire old selection and highlight the entire new selection (if
            # there is one).
            unhl.append((oldstart, oldend))
            if (newstart != newend):
                hl.append((newstart, newend))
        else:
            # There is at least some overlap, so calculate the changed regions.
            if oldstart < newstart:
                unhl.append((oldstart, newstart))
            elif newstart < oldstart:
                hl.append((newstart, oldstart))
            if newend < oldend:
                unhl.append((newend, oldend))
            elif oldend < newend:
                hl.append((oldend, newend))

        cr = cairo.Context(self.surface)
        cons = self.cons.getConsensus()

        # Draw the newly unhighlighted regions.
        for coords in unhl:
            start = coords[0]
            end = coords[1]
            for index in range(start, end):
                self.drawConsensusBase(
                    cons[index], index*self.fwidth, alend+self.padding, cr, False
                )

            self.queue_draw_area(
                start*self.fwidth, alend+self.padding,
                self.fwidth*(end-start), self.fheight
            )

        # Draw the newly highlighted regions.
        for coords in hl:
            start = coords[0]
            end = coords[1]
            for index in range(start, end):
                self.drawConsensusBase(
                    cons[index], index*self.fwidth, alend+self.padding, cr, True
                )

            self.queue_draw_area(
                start*self.fwidth, alend+self.padding,
                self.fwidth*(end-start), self.fheight
            )

    def setCursor(self, cursor):
        if self.curr_cursor != cursor:
            self.get_window().set_cursor(cursor)
            self.curr_cursor = cursor
        
    def highlightAlignment(self, index, highlight=True):
        """
        Highlights or unhighlights a position in the alignment display.

        index: An index in the alignment.
        highlight: If True, the position will be highlighted.  If False, the
            position will be unhighlighted.
        """
        align1 = self.cons.getAlignedSequence(0)
        base = align1[index]

        cr = cairo.Context(self.surface)

        x = index*self.fwidth

        # Update the alignment on the off-screen buffer, then invalidate the
        # corresponding region on the DrawingArea window.

        self.drawAlignmentBase(base, x, self.al_top, cr, highlight)

        if self.numseqs == 2:
            align2 = self.cons.getAlignedSequence(1)
            self.drawAlignmentBase(
                align2[index], x, self.al_top + self.fheight, cr, highlight
            )

        self.queue_draw_area(
            x, self.al_top, self.fwidth, self.fheight * self.numseqs
        )

    def setFontSize(self, size):
        """
        Sets the font size to use for drawing sequences, calculates the character
        size in pixels, and resizes the DrawingArea to fit the sequence(s).  Note
        that for most fonts, the character "W" will actually be slightly wider than
        the character width calculated by this method.  However, "W"s are uncommon
        in trace data, and sizing the character to fit "W"s makes the other characters
        too far apart (in my opinion!).
        """
        # set up sequence font properties
        self.fontdesc.set_size(size*Pango.SCALE)
        self.txtlayout.set_font_description(self.fontdesc)
        self.txtlayout.set_text('G', 1)
        self.fheight = self.txtlayout.get_pixel_size()[1]
        self.fwidth = self.txtlayout.get_pixel_size()[0]

        self.setDrawingSize()

    def getSizeRequirements(self):
        """
        Calculates the total size requirements in pixels in order to view the
        consensus sequence object, including the alignment and primers, if they
        are provided, given the current font metrics.  The size is returned as
        (width, height).
        """
        settings = self.cons.getSettings()
        haveprimers = settings.getForwardPrimer() != '' and settings.getReversePrimer() != ''
        
        totalheight = self.fheight*(self.numseqs+1) + self.margins*2 + self.padding
        if haveprimers:
            totalheight += self.fheight

        return (self.fwidth*len(self.cons.getAlignedSequence(0)), totalheight)

    def setDrawingSize(self):
        """
        Sets the size request for the viewer to accomodate all displayable components
        of the consensus sequence object.  The total size is determined by the method
        getSizeRequirements().  Also updates the location of the top of the alignment
        and the flag indicating whether primers should be displayed.
        """
        # Determine whether primers should be drawn.
        settings = self.cons.getSettings()
        self.drawprimers = settings.getForwardPrimer() != '' and settings.getReversePrimer() != ''

        # Set the location of the top of the alignment.
        self.al_top = self.margins
        if self.drawprimers:
            self.al_top += self.fheight

        # Set the size request.
        width, height = self.getSizeRequirements()
        self.set_size_request(width, height)

    def consensusChanged(self, start, end):
        # Check if any size requirements for the drawing area have changed,
        # and update the size request if needed.
        oldwidth, oldheight = self.get_size_request()
        newwidth, newheight = self.getSizeRequirements()
        if oldwidth != newwidth or oldheight != newheight:
            self.setDrawingSize()

        cr = cairo.Context(self.surface)
        self.drawConsensus(start, end, cr)

        alend = self.fheight*self.numseqs + self.al_top
        x = start*self.fwidth
        dwidth = (end - start + 1) * self.fwidth
        self.queue_draw_area(x, alend+self.padding, dwidth, self.fheight)        

    def onConfigure(self, widget, event):
        # Note that the Python cairo bindings do not expose
        # cairo_surface_destroy() because this functionality is handled
        # automatically by the Python library.

        self.surface = self.get_window().create_similar_surface(
            cairo.CONTENT_COLOR, self.get_allocated_width(),
            self.get_allocated_height()
        )

        startindex = 0
        endindex = len(self.cons.getAlignedSequence(0)) - 1

        cr = cairo.Context(self.surface)

        if self.drawprimers:
            self.drawPrimers(startindex, endindex, cr)
        self.drawAlignment(startindex, endindex, cr)
        self.drawConsensus(startindex, endindex, cr)

        return True

    def onDraw(self, da, cr):
        # Drawing is simple: we just copy the region that needs to be painted
        # from the off-screen buffer.
        cr.set_source_surface(self.surface, 0, 0)
        cr.paint()

        return False

    def drawPrimers(self, startindex, endindex, cr):
        dwin = self.window
        gc = dwin.new_gc(function=Gdk.COPY)

        self.erasePrimers(dwin, gc, startindex, endindex)
        self.drawPrimers(dwin, gc, startindex, endindex)

    def erasePrimers(self, dwin, gc, startindex, endindex):
        startx = startindex*self.fwidth
        rwidth = (endindex-startindex+1)*self.fwidth

        # Draw the background for the primer sequences.
        gc.set_rgb_fg_color(Gdk.color_parse('#d8d8bb'))
        gc.set_rgb_fg_color(Gdk.color_parse('#dbdbdb'))
        dwin.draw_rectangle(gc, True, startx, self.margins, rwidth, self.fheight)

    def drawPrimers(self, dwin, gc, startindex, endindex):
        palign = self.cons.getAlignedPrimers()

        y = self.al_top + self.fheight*self.numseqs
        gc.set_rgb_fg_color(Gdk.color_parse('#888'))
        dwin.draw_line(gc, startindex*self.fwidth, self.margins-1, (endindex+1)*self.fwidth, self.margins-1)

        for index in range(startindex, endindex+1):
            x = index * self.fwidth
            y = self.margins

            # Draw the primer base, if there is one.
            if palign[index] != ' ':
                self.drawAlignmentBase(dwin, gc, palign[index], x, y)

    def drawAlignment(self, startindex, endindex, cr):
        """
        Draws the alignment from alignment positions startindex to endindex,
        inclusive.
        """
        x = startindex * self.fwidth
        rwidth = (endindex-startindex+1)*self.fwidth

        # Draw the gray background for the alignment.
        cr.set_source_rgba(*parseHTMLColorStr('#d2d2d2'))
        cr.rectangle(x, 0, rwidth, self.margins + self.fheight*self.numseqs + self.padding/2+1)
        cr.fill()

        align1 = self.cons.getAlignedSequence(0)
        if self.numseqs == 2:
            align2 = self.cons.getAlignedSequence(1)

        # Draw the border lines for the alignment.
        y = self.al_top + self.fheight*self.numseqs
        cr.set_source_rgba(0, 0, 0)
        cr.set_line_width(1)
        cr.move_to(startindex*self.fwidth, self.al_top-0.5)
        cr.line_to((endindex+1)*self.fwidth, self.al_top-0.5)
        cr.move_to(startindex*self.fwidth, y+0.5)
        cr.line_to((endindex+1)*self.fwidth, y+0.5)
        cr.stroke()

        # Draw the alignment.
        for index in range(startindex, endindex+1):
            x = index * self.fwidth
            y = self.margins

            # Draw the base from the first aligned sequence.
            self.drawAlignmentBase(align1[index], x, self.al_top, cr)

            # Draw the base from the second aligned sequence, if present.
            if self.numseqs == 2:
                self.drawAlignmentBase(
                    align2[index], x, self.al_top + self.fheight, cr
                )

        # Restore the alignment selection, if any.
        if (self.highlighted >= startindex) and (self.highlighted <= endindex):
            self.highlightAlignment(self.highlighted, True, cr)

    def drawAlignmentBase(self, base, x, y, cr, invert=False):
        if invert:
            cr.set_source_rgba(*self.bgcolors_inv[base])
        else:
            cr.set_source_rgba(*self.bgcolors[base])
        cr.rectangle(x, y, self.fwidth, self.fheight)
        cr.fill()

        if invert:
            cr.set_source_rgba(*self.basecolors_inv[base])
        else:
            cr.set_source_rgba(*self.basecolors[base])
        self.txtlayout.set_text(base, 1)
        tw = self.txtlayout.get_pixel_size()[0]
        cr.move_to(x + (self.fwidth-tw)/2, y)
        PangoCairo.layout_path(cr, self.txtlayout)
        cr.fill()

    def drawConsensus(self, startindex, endindex, cr):
        """
        Draws the consensus sequence from alignment positions startindex to
        endindex, inclusive.
        """
        startx = startindex*self.fwidth
        rwidth = (endindex-startindex+1)*self.fwidth

        # calculate the y-coordinate of the top of the working sequence ribbon
        y = self.al_top + self.fheight*self.numseqs + self.padding

        # draw the gray background
        cr.set_source_rgba(*parseHTMLColorStr('#d2d2d2'))
        cr.rectangle(startx, y - self.padding/2, rwidth,
                self.fheight + self.padding/2 + self.margins)
        cr.fill()

        # draw the white background for the sequence characters
        cr.set_source_rgba(1.0, 1.0, 1.0)
        cr.rectangle(startx, y, rwidth, self.fheight)
        cr.fill()

        cons = self.cons.getConsensus()
        cons_sel = self.getSelection()

        # Draw the consensus sequence.
        for index in range(startindex, endindex+1):
            x = index * self.fwidth

            # Draw the base from the consensus sequence, highlighting it if it
            # is part of an active selection.
            highlight = False
            if (index >= cons_sel[0]) and (index <= cons_sel[1]):
                highlight = True

            base = cons[index]
            self.drawConsensusBase(base, x, y, cr, highlight)

    def drawConsensusBase(self, base, x, y, cr, invert=False):
        if invert:
            cr.set_source_rgba(0.2, 0.2, 0.2)
        else:
            cr.set_source_rgba(1.0, 1.0, 1.0)

        cr.rectangle(x, y, self.fwidth, self.fheight)
        cr.fill()

        if invert:
            cr.set_source_rgba(*self.basecolors_inv[base])
        else:
            cr.set_source_rgba(*self.basecolors[base])

        self.txtlayout.set_text(base, 1)
        tw = self.txtlayout.get_pixel_size()[0]
        cr.move_to(x + (self.fwidth-tw)/2, y)
        PangoCairo.layout_path(cr, self.txtlayout)
        cr.fill()


class ScrolledConsensusSequenceViewer(Gtk.ScrolledWindow):
    def __init__(self, mod_consensseq_builder):
        Gtk.ScrolledWindow.__init__(self)

        self.da = ConsensusSequenceViewer(mod_consensseq_builder)
        self.innerhbox = Gtk.HBox(False)
        self.innerhbox.pack_start(self.da, False, False, 0)
        self.set_policy(Gtk.PolicyType.ALWAYS, Gtk.PolicyType.NEVER)
        self.add_with_viewport(self.innerhbox)

        #self.da.connect('size-request', self.consViewerResized)

    def consViewerResized(self, widget, req):
        """
        Respond to size request changes by the child ConsensusSequenceViewer.  The
        HBox inside the viewport does not seem to respond properly to changes in its
        child's size request, so take care of that manually here.
        """
        width, height = self.da.get_size_request()
        self.innerhbox.set_size_request(width, height)

    def getConsensusSequenceViewer(self):
        return self.da
