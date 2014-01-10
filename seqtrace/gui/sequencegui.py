#!/usr/bin/python
# Copyright (C) 2012 Brian J. Stucky
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

import pygtk
pygtk.require('2.0')
import gtk
import pango



class ConsensusSequenceViewer(gtk.DrawingArea, Observable):
    def __init__(self, mod_consensseq_builder):
        gtk.DrawingArea.__init__(self)

        self.cons = mod_consensseq_builder
        self.numseqs = self.cons.getNumSeqs()
        self.cons.registerObserver('consensus_changed', self.consensusChanged)
        self.connect('destroy', self.onDestroy)

        # Initialize drawing settings.
        self.basecolors = {
                'A': gtk.gdk.color_parse('#009000'),    # green
                'C': gtk.gdk.color_parse('#0000ff'),    # blue
                'G': gtk.gdk.color_parse('#000000'),    # black
                'T': gtk.gdk.color_parse('#ff0000'),    # red
                'W': gtk.gdk.color_parse('#804800'),    # mix of A and T
                'S': gtk.gdk.color_parse('#000080'),    # mix of C and G
                'M': gtk.gdk.color_parse('#004880'),    # mix of A and C
                'K': gtk.gdk.color_parse('#800000'),    # mix of G and T
                'R': gtk.gdk.color_parse('#004800'),    # mix of A and G
                'Y': gtk.gdk.color_parse('#800080'),    # mix of C and T
                'N': gtk.gdk.color_parse('#999'),       # gray
                '-': gtk.gdk.color_parse('#000'),       # black
                ' ': gtk.gdk.color_parse('#999')}
        self.bgcolors = {
                # These are almost all lighter versions of the foreground colors above.
                'A': gtk.gdk.color_parse('#cfc'),
                'C': gtk.gdk.color_parse('#ccf'),
                'G': gtk.gdk.color_parse('#ccc'),
                'T': gtk.gdk.color_parse('#fcc'),
                'W': gtk.gdk.color_parse('#DFD1BF'),    # mix of A and T
                'S': gtk.gdk.color_parse('#BFBFDF'),    # mix of C and G
                'M': gtk.gdk.color_parse('#BFD1DF'),    # mix of A and C
                'K': gtk.gdk.color_parse('#DFBFBF'),    # mix of G and T
                'R': gtk.gdk.color_parse('#BFD1BF'),    # mix of A and G
                'Y': gtk.gdk.color_parse('#DFBFDF'),    # mix of C and T
                'N': gtk.gdk.color_parse('#fff'),
                '-': gtk.gdk.color_parse('#ff9')}
        self.margins = 6
        self.padding = 6

        self.txtlayout = pango.Layout(self.create_pango_context())
        self.fontdesc = self.txtlayout.get_context().get_font_description().copy()

        self.setFontSize(10)

        self.lastx = -1
        self.highlighted = -1
        # keep track of location of an active selection on the consensus sequence
        self.consselect_start = -1
        self.consselect_end = -1
        # keep track of where a selection highlight has been drawn on the consensus sequence
        self.chl_start = -1
        self.chl_end = -1
        # indicates if the user is actively making a selection on the consensus sequence
        self.selecting_active = False

        # set up event handling
        self.connect('expose-event', self.updatedisplay)
        self.set_events(gtk.gdk.BUTTON_PRESS_MASK | gtk.gdk.BUTTON_RELEASE_MASK | gtk.gdk.POINTER_MOTION_MASK
                | gtk.gdk.POINTER_MOTION_HINT_MASK | gtk.gdk.LEAVE_NOTIFY_MASK)
        self.connect('button-press-event', self.mouseClick)
        self.connect('button-release-event', self.mouseRelease)
        self.connect('motion-notify-event', self.mouseMove)
        self.connect('leave-notify-event', self.mouseLeave)

        self.clickable_cursor = gtk.gdk.Cursor(gtk.gdk.HAND2)
        self.text_cursor = gtk.gdk.Cursor(gtk.gdk.XTERM)
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
        start = self.consselect_start
        end = self.consselect_end
        if end < start:
            tmp = start
            start = end
            end = tmp

        return (start, end - 1)

    def mouseClick(self, da, event):
        #numbases = len(self.cons.getAlignedSequence(1))
        alend = self.fheight*self.numseqs + self.margins
        consend = alend + self.padding + self.fheight
        
        # calculate the index of the base corresponding to the mouse click
        bindex = int(event.x / self.fwidth)

        if event.button == 1:
            if (event.y > self.margins) and (event.y < alend):
                # the mouse is over the alignment display
                if event.y > (self.margins + self.fheight):
                    seqnum = 1
                else:
                    seqnum = 0
    
                seq1index = self.cons.getActualSeqIndex(0, bindex)
                if self.numseqs == 2:
                    seq2index = self.cons.getActualSeqIndex(1, bindex)
                else:
                    seq2index = -1
    
                if self.highlighted != bindex:
                    self.highlightAlignmentInternal(self.highlighted)
                self.highlighted = bindex
                self.notifyObservers('alignment_clicked', (seqnum, seq1index, seq2index))
            elif (event.y > (alend + self.padding)) and (event.y < consend):
                # the mouse is over the consensus sequence display

                # see if there was a previous selection
                if self.consselect_start != self.consselect_end:
                    # there was a previous selection, so send notification that it is cleared
                    self.notifyObservers('selection_state', (False,))

                # determine if the click was on the left or right side of the character
                if (event.x % self.fwidth) < (self.fwidth / 2):
                    # on the left
                    self.consselect_start = self.consselect_end = bindex
                else:
                    # on the right
                    self.consselect_start = self.consselect_end = bindex + 1

                self.selecting_active = True
                self.updateConsensusHighlight()

        elif event.button == 3:
            if (event.y > (alend + self.padding)) and (event.y < consend):
                # the mouse is over the consensus sequence display and was right clicked
                self.notifyObservers('consensus_clicked', (self.consselect_start, self.consselect_end, event))

    def mouseRelease(self, da, event):
        if (event.button == 1) and self.selecting_active:
            self.selecting_active = False

    def mouseLeave(self, da, event):
        dwin = self.window
        # if we just left the window, make sure we erased the highlight
        if (self.lastx != -1) and (self.lastx != self.highlighted):
            self.highlightAlignmentInternal(self.lastx)
            self.lastx = -1
            return

    def mouseMove(self, da, event):
        index = int(event.x) / self.fwidth

        if self.selecting_active:
            # we are in the process of selecting bases from the consensus sequence
            #print 'BEFORE start, end, index:', self.consselect_start, self.consselect_end, index

            # determine if the event was on the left or right side of the character
            if (event.x % self.fwidth) < (self.fwidth / 2):
                # on the left
                s_index = index
            else:
                # on the right
                s_index = index + 1

            if self.consselect_start == s_index:
                # no bases are selected
                self.consselect_end = self.consselect_start
                self.updateConsensusHighlight()
                self.notifyObservers('selection_state', (False,))
            elif self.consselect_end != s_index:
                # at least one new base was selected
                if self.consselect_end == self.consselect_start:
                    self.notifyObservers('selection_state', (True,))
                self.consselect_end = s_index
                self.updateConsensusHighlight()
            #print 'AFTER start, end, index:', self.consselect_start, self.consselect_end, index 

        #if event.is_hint:
        #    print "hint"
        # check if the mouse pointer is on the alignment display
        if (event.y > self.margins) and (event.y < (self.fheight*self.numseqs + self.margins)):
            # change the cursor, if necessary
            self.setCursor(self.clickable_cursor)
            
            # draw the highlight and erase the old one, if necessary
            if self.lastx != index:
                if (self.lastx != self.highlighted) or (self.highlighted == -1):
                    self.highlightAlignmentInternal(self.lastx)
                self.lastx = index
                if index != self.highlighted:
                    self.highlightAlignmentInternal(index)
        else:
            # not on the alignment, so just erase the old highlight, if necessary
            if (self.lastx != -1) and (self.lastx != self.highlighted):
                self.highlightAlignmentInternal(self.lastx)
                self.lastx = -1

            alend = self.fheight*self.numseqs + self.margins
            consend = alend + self.padding + self.fheight
            if (event.y > (alend + self.padding)) and (event.y < consend):
                # the mouse is over the consensus sequence display
                self.setCursor(self.text_cursor)
            else:
                # not on the consensus display, so change back the cursor to the default
                self.setCursor(None)

    def setCursor(self, cursor):
        if self.curr_cursor != cursor:
            self.window.set_cursor(cursor)
            self.curr_cursor = cursor
        
    def highlightAlignment(self, alignx):
        if alignx != self.highlighted:
            if self.highlighted != -1:
                self.highlightAlignmentInternal(self.highlighted)
            if alignx != self.lastx:
                self.highlightAlignmentInternal(alignx)
            self.highlighted = alignx

    def highlightAlignmentInternal(self, alignx):
        alend = self.fheight*self.numseqs + self.margins

        dwin = self.window
        gc = dwin.new_gc(function=gtk.gdk.INVERT)
        dwin.draw_rectangle(gc, True, alignx*self.fwidth, self.margins, self.fwidth, self.fheight*self.numseqs)
        #dwin.draw_rectangle(gc, True, alignx*self.fwidth, alend+self.padding, self.fwidth, self.fheight)

    def updateConsensusHighlight(self):
        alend = self.fheight*self.numseqs + self.margins

        dwin = self.window
        gc = dwin.new_gc(function=gtk.gdk.INVERT)

        if (self.consselect_start == self.consselect_end):
            # no bases selected, so erase the current highlight
            start = self.chl_start
            end = self.chl_end
            self.chl_start = self.chl_end = -1
        else:
            # bases selected, so update the highlight if necessary
            if self.chl_start == -1:
                start = self.chl_start = self.consselect_start
                end = self.chl_end = self.consselect_end
            else:
                start = self.chl_end
                end = self.consselect_end
                self.chl_end = self.consselect_end

        if start < end:
            for cnt in range(start, end):
                dwin.draw_rectangle(gc, True, cnt*self.fwidth, alend+self.padding, self.fwidth, self.fheight)
        else:
            for cnt in range(end, start):
                dwin.draw_rectangle(gc, True, cnt*self.fwidth, alend+self.padding, self.fwidth, self.fheight)

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
        self.fontdesc.set_size(size*pango.SCALE)
        self.txtlayout.set_font_description(self.fontdesc)
        self.txtlayout.set_text('G')
        self.fheight = self.txtlayout.get_pixel_size()[1]
        self.fwidth = self.txtlayout.get_pixel_size()[0]

        self.set_size_request(self.fwidth*len(self.cons.getAlignedSequence(0)),
                self.fheight*(self.numseqs+1) + self.margins*2 + self.padding)

    def consensusChanged(self, start, end):
        self.redrawConsensus(start, end)

    def updatedisplay(self, da, event):
        #print '(', event.area.x, ',', event.area.y
        startx = event.area.x
        dwidth = event.area.width

        startindex = startx / self.fwidth
        endindex = (startx + dwidth) / self.fwidth
        if endindex >= len(self.cons.getAlignedSequence(0)):
            endindex -= 1

        self.redrawAlignment(startindex, endindex)
        self.redrawConsensus(startindex, endindex)

    def redrawAlignment(self, startindex, endindex):
        #self.setFontSize(14)
        dwin = self.window
        gc = dwin.new_gc(function=gtk.gdk.COPY)

        self.eraseAlignment(dwin, gc, startindex, endindex)
        self.drawAlignment(dwin, gc, startindex, endindex)

        # restore alignment selection
        if (self.highlighted >= startindex) and (self.highlighted <= endindex):
            self.highlightAlignmentInternal(self.highlighted)

    def redrawConsensus(self, startindex, endindex):
        #self.setFontSize(14)
        #print startindex, endindex
        dwin = self.window
        gc = dwin.new_gc(function=gtk.gdk.COPY)

        self.eraseConsensus(dwin, gc, startindex, endindex)
        self.drawConsensus(dwin, gc, startindex, endindex)

        # restore consensus sequence selection
        self.chl_start = self.chl_end = -1
        self.updateConsensusHighlight()

    def eraseAlignment(self, dwin, gc, startindex, endindex):
        startx = startindex*self.fwidth
        rwidth = (endindex-startindex+1)*self.fwidth

        # draw the gray background for the alignment
        gc.set_rgb_fg_color(gtk.gdk.color_parse('#d2d2d2'))
        dwin.draw_rectangle(gc, True, startx, 0, rwidth,
                self.margins + self.fheight*self.numseqs + self.padding/2+1)

    def eraseConsensus(self, dwin, gc, startindex, endindex):
        startx = startindex*self.fwidth
        rwidth = (endindex-startindex+1)*self.fwidth

        # calculate the y-coordinate of the top of the working sequence ribbon
        y = self.margins + self.fheight*self.numseqs + self.padding

        # draw the gray background
        gc.set_rgb_fg_color(gtk.gdk.color_parse('#d2d2d2'))
        dwin.draw_rectangle(gc, True, startx, y - self.padding/2, rwidth,
                self.fheight + self.padding/2 + self.margins)

        # draw the white background for the sequence characters
        gc.set_rgb_fg_color(gtk.gdk.color_parse('#fff'))
        dwin.draw_rectangle(gc, True, startx, y, rwidth, self.fheight)

    def drawAlignment(self, dwin, gc, startindex, endindex):
        align1 = self.cons.getAlignedSequence(0)
        if self.numseqs == 2:
            align2 = self.cons.getAlignedSequence(1)

        y = self.margins + self.fheight*self.numseqs
        gc.set_rgb_fg_color(gtk.gdk.color_parse('black'))
        dwin.draw_line(gc, startindex*self.fwidth, self.margins-1, (endindex+1)*self.fwidth, self.margins-1)
        dwin.draw_line(gc, startindex*self.fwidth, y, (endindex+1)*self.fwidth, y)

        for index in range(startindex, endindex+1):
            x = index * self.fwidth
            y = self.margins

            # draw the base from the first aligned sequence
            self.drawAlignmentBase(dwin, gc, align1[index], x, y)

            # draw the base from the second aligned sequence, if present
            if self.numseqs == 2:
                self.drawAlignmentBase(dwin, gc, align2[index], x, y + self.fheight)

    def drawAlignmentBase(self, dwin, gc, base, x, y):
        gc.set_rgb_fg_color(self.bgcolors[base])
        dwin.draw_rectangle(gc, True, x, y, self.fwidth, self.fheight)
        gc.set_rgb_fg_color(self.basecolors[base])
        #gc.set_rgb_fg_color(gtk.gdk.color_parse('#bbb'))
        self.txtlayout.set_text(base)
        tw = self.txtlayout.get_pixel_size()[0]
        dwin.draw_layout(gc, x + (self.fwidth-tw)/2, y, self.txtlayout)

    def drawConsensus(self, dwin, gc, startindex, endindex):
        cons = self.cons.getConsensus()

        y = self.margins + self.fheight*self.numseqs + self.padding

        for index in range(startindex, endindex+1):
            x = index * self.fwidth

            # draw the base from the consensus sequence
            base = cons[index]
            gc.set_rgb_fg_color(self.basecolors[base])
            self.txtlayout.set_text(base)
            tw = self.txtlayout.get_pixel_size()[0]
            dwin.draw_layout(gc, x + (self.fwidth-tw)/2, y, self.txtlayout)


class ScrolledConsensusSequenceViewer(gtk.ScrolledWindow):
    def __init__(self, mod_consensseq_builder):
        gtk.ScrolledWindow.__init__(self)

        self.da = ConsensusSequenceViewer(mod_consensseq_builder)
        innerhbox = gtk.HBox(False)
        innerhbox.pack_start(self.da, expand=False, fill=False)
        self.set_policy(gtk.POLICY_ALWAYS, gtk.POLICY_NEVER)
        self.add_with_viewport(innerhbox)

    def getConsensusSequenceViewer(self):
        return self.da
