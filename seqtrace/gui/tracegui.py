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


from seqtrace.core import sequencetrace
from seqtrace.core import seqwriter
from seqtrace.core.observable import Observable

from seqtrace.gui.dialgs import CommonDialogs, EntryDialog
from seqtrace.gui.statusbar import ConsensSeqStatusBar

import seqtrace.gui.pyperclip as pyperclip

import pygtk
pygtk.require('2.0')
import gtk
import pango
import xml.sax.saxutils

import os.path



class ConsensusSequenceViewer(gtk.DrawingArea, Observable):
    def __init__(self, mod_consensseq_builder):
        gtk.DrawingArea.__init__(self)

        self.cons = mod_consensseq_builder
        self.numseqs = self.cons.getNumSeqs()
        self.cons.registerObserver('consensus_changed', self.consensusChanged)
        self.connect('destroy', self.onDestroy)

        # initialize drawing settings
        self.basecolors = {'A': gtk.gdk.color_parse('#009000'),
                'C': gtk.gdk.color_parse('blue'),
                'G': gtk.gdk.color_parse('black'),
                'T': gtk.gdk.color_parse('red'),
                '-': gtk.gdk.color_parse('black'),
                'N': gtk.gdk.color_parse('#999'),
                ' ': gtk.gdk.color_parse('#999')}
        self.bgcolors = {'A': gtk.gdk.color_parse('#cfc'),
                'C': gtk.gdk.color_parse('#ccf'),
                'G': gtk.gdk.color_parse('#ccc'),
                'T': gtk.gdk.color_parse('#fcc'),
                '-': gtk.gdk.color_parse('#ff9'),
                'N': gtk.gdk.color_parse('#fff')}
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


class SequenceTraceViewer:
    def __init__(self, sequencetrace):
        self.min_height = 100
        self.preferred_height = 200

        self.drawingarea = gtk.DrawingArea()
        self.drawingarea.set_size_request(-1, self.min_height)

        self.seqt = sequencetrace

        # initialize drawing settings
        self.tracecolors = {'A': gtk.gdk.color_parse('#009000'),
                'C': gtk.gdk.color_parse('blue'),
                'G': gtk.gdk.color_parse('black'),
                'T': gtk.gdk.color_parse('red'),
                'N': gtk.gdk.color_parse('#999')}
        self.bottom_margin = 2
        self.bcpadding = 4

        self.show_confidence = True

        self.sigmax = sequencetrace.getMaxTraceVal() + (sequencetrace.getMaxTraceVal() / 12)

        self.bclayout = pango.Layout(self.drawingarea.create_pango_context())
        self.bcfontdesc = self.bclayout.get_context().get_font_description().copy()
        self.setFontSize(10)

        self.drawingarea.connect('expose-event', self.updatedisplay)

        self.highlighted = self.seqt.getNumBaseCalls()

    def getDefaultHeight(self):
        return self.min_height

    def getPreferredHeight(self):
        return self.preferred_height

    def getSequenceTrace(self):
        return self.seqt

    def getWidget(self):
        return self.drawingarea

    def getYScaleMax(self):
        return self.sigmax

    def setYScaleMax(self, new_yscalemax):
        if new_yscalemax <= 0:
            raise Exception

        self.sigmax = new_yscalemax

        # queue a redraw of the visible part of the drawing area
        #vis_region = self.window.get_visible_region()
        #print vis_region.get_clipbox()
        #self.window.invalidate_region(vis_region, False)

        # the following methods also work, and it appears that GTK is able to automatically
        # clip the update region to only the visible portion of the widget
        width, height = self.drawingarea.window.get_size()
        #print width, height
        self.drawingarea.window.invalidate_rect(gtk.gdk.Rectangle(0, 0, width, height), False)
        #self.queue_draw_area(0, 0, width, height)

    def setShowConfidence(self, newval):
        self.show_confidence = newval

        # queue a redraw of the window
        width, height = self.drawingarea.window.get_size()
        self.drawingarea.window.invalidate_rect(gtk.gdk.Rectangle(0, 0, width, height), False)

    def setFontSize(self, size):
        # set up base call font properties
        self.bcfontdesc.set_size(size*pango.SCALE)
        self.bclayout.set_font_description(self.bcfontdesc)
        self.bclayout.set_text('A')
        self.bcheight = self.bclayout.get_pixel_size()[1] + (self.bcpadding*2)

    def updatedisplay(self, da, event):
        dwin = self.drawingarea.window
        gc = dwin.new_gc(function=gtk.gdk.COPY)

        #print '(', event.area.x, ',', event.area.y
        startx = event.area.x
        dwidth = event.area.width
        #print startx, dwidth

        self.eraseda(dwin, gc, startx=startx, dwidth=dwidth)
        self.drawBaseCalls(dwin, gc, startx=startx, dwidth=dwidth)
        self.drawTrace(dwin, gc, startx=startx, dwidth=dwidth)
        if self.highlighted != self.seqt.getNumBaseCalls():
            self.highlightBaseInternal(self.highlighted);

    def eraseda(self, dwin, gc, startx=0, dwidth=0):
        width, height = dwin.get_size()
        if dwidth == 0:
            dwidth = width

        gc.set_rgb_fg_color(gtk.gdk.color_parse('#ffffff'))
        dwin.draw_rectangle(gc, True, startx, 0, dwidth, height)

    def drawTrace(self, dwin, gc, startx=0, dwidth=0):
        width, height = dwin.get_size()
        if dwidth == 0:
            dwidth = width

        drawheight = height - self.bottom_margin - self.bcheight

        gc.set_line_attributes(0, gtk.gdk.LINE_SOLID, gtk.gdk.CAP_BUTT, gtk.gdk.JOIN_MITER)

        samps = self.seqt.getTraceLength()
        startsamp = (startx * samps) / width
        endsamp = int((float(startx+dwidth) * samps) / width + 0.5)
        if endsamp < (samps-1):
            endsamp += 2

        yscale = float(drawheight) / self.sigmax
        xscale = float(width) / samps

        for base in ['A','C','G','T']:
            gc.set_rgb_fg_color(self.tracecolors[base])
            data = self.seqt.getTraceSamples(base)

            oldx = int(startsamp * xscale)
            oldy = int((self.sigmax - data[startsamp]) * yscale + 0.5)
            for cnt in range(startsamp, endsamp):
                x = int(cnt * xscale)
                y = int((self.sigmax - data[cnt]) * yscale + 0.5)
                dwin.draw_line(gc, oldx, oldy, x, y)
                oldx = x
                oldy = y

    def drawBaseCalls(self, dwin, gc, startx=0, dwidth=0):
        width, height = dwin.get_size()
        if dwidth == 0:
            dwidth = width

        drawheight = height - self.bottom_margin - self.bcheight
        confbarmax = drawheight / 4
        conf_hue_best = 0.68
        conf_hue_worst = 1.0

        samps = self.seqt.getTraceLength()
        startsamp = (startx * samps) / width
        endsamp = int((float(startx+dwidth) * samps) / width + 0.5)
        if endsamp < (samps-1):
            endsamp += 2

        startbcindex = self.seqt.getPrevBaseCallIndex(startsamp)
        #print startbcindex
        endbcindex = self.seqt.getNextBaseCallIndex(endsamp)
        if endbcindex < self.seqt.getNumBaseCalls():
            endbcindex += 1
        #print endbcindex

        xscale = float(width) / samps
        yscale = float(drawheight) / self.sigmax
        y = drawheight + self.bcpadding

        gc.set_line_attributes(0, gtk.gdk.LINE_ON_OFF_DASH, gtk.gdk.CAP_BUTT, gtk.gdk.JOIN_MITER)
        gc.set_dashes(0, (1,1))

        for index in range(startbcindex, endbcindex):
            # get the base and position
            base = self.seqt.getBaseCall(index)
            pos = self.seqt.getBaseCallPos(index)

            x = int(pos * xscale)

            if self.show_confidence:
                # draw the confidence bar
                bcconf = self.seqt.getBaseCallConf(index)
                gc.set_rgb_fg_color(gtk.gdk.color_parse('#c8c8c8'))
                #hue = float(bcconf) * (conf_hue_best - conf_hue_worst) / 61 + conf_hue_worst
                #gc.set_rgb_fg_color(gtk.gdk.color_from_hsv(hue, 0.34, 1.0))
                dwin.draw_rectangle(gc, True, x-6, 6, 12, (confbarmax*bcconf)/61)

                # draw the confidence score
                hue = float(bcconf) * (conf_hue_best - conf_hue_worst) / 61 + conf_hue_worst
                gc.set_rgb_fg_color(gtk.gdk.color_from_hsv(hue, 1.0, 0.9))
                self.bclayout.set_text(str(bcconf))
                txtwidth = self.bclayout.get_pixel_size()[0]
                dwin.draw_layout(gc, x - (txtwidth/2), 6, self.bclayout)

            # draw the base
            gc.set_rgb_fg_color(self.tracecolors[base])
            self.bclayout.set_text(base)
            txtwidth = self.bclayout.get_pixel_size()[0]
            dwin.draw_layout(gc, x - (txtwidth/2), y, self.bclayout)

            # calculate the y coordinate of the trace location for this base
            if base != 'N':
                traceval = self.seqt.getTraceSample(base, pos)
                ysamp = int((self.sigmax - traceval) * yscale + 0.5)

                # draw the line to the trace
                dwin.draw_line(gc, x, ysamp, x, y-(self.bcpadding/2))

    def highlightBase(self, bindex):
        # draw the highlight, if needed
        if bindex != self.highlighted:
            if self.highlighted != self.seqt.getNumBaseCalls():
                self.highlightBaseInternal(self.highlighted)
            self.highlightBaseInternal(bindex)
            self.highlighted = bindex  
        #dwin.draw_rectangle(gc, True, x - 6, y, 12, self.bcheight)

    def highlightBaseInternal(self, bindex):
        dwin = self.drawingarea.window
        #gc = dwin.new_gc(function=gtk.gdk.INVERT)
        gc = dwin.new_gc(function=gtk.gdk.XOR)
        
        # yellow
        gc.set_rgb_fg_color(gtk.gdk.color_parse('#00f'))
        # light blue
        #gc.set_rgb_fg_color(gtk.gdk.color_parse('#f00'))

        width, height = dwin.get_size()
        drawheight = height - self.bottom_margin - self.bcheight

        samps = self.seqt.getTraceLength()
        xscale = float(width) / samps
        yscale = float(drawheight) / self.sigmax
        y = drawheight + self.bcpadding

        # check if we got a gap location
        if bindex < 0:
            if bindex == -1:
                pos = 0
            elif (bindex+1) * -1 == self.seqt.getNumBaseCalls():
                pos = samps
            else:
                p1 = self.seqt.getBaseCallPos((bindex+1) * -1)
                p2 = self.seqt.getBaseCallPos((bindex+2) * -1)
                pos = (p1 + p2) / 2
        else:
            pos = self.seqt.getBaseCallPos(bindex)
        x = int(pos * xscale)

        # draw the highlight
        if bindex < 0:
            dwin.draw_rectangle(gc, True, x - 2, 0, 5, height)
        else:
            dwin.draw_rectangle(gc, True, x - 6, 0, 12, height)
        
        #dwin.draw_rectangle(gc, True, x - 6, y, 12, self.bcheight)


class SequenceTraceViewerDecorator:
    def __init__(self, sequencetraceviewer):
        self.viewer = sequencetraceviewer

    def getViewer(self):
        return self.viewer

    def setViewer(self, sequencetraceviewer):
        self.viewer = sequencetraceviewer

    # delegate all other operations to the decorated object
    def __getattr__(self, attr):
        return getattr(self.viewer, attr)


class FwdRevSTVDecorator(SequenceTraceViewerDecorator):
    def __init__(self, sequencetraceviewer):
        SequenceTraceViewerDecorator.__init__(self, sequencetraceviewer)

        self.hbox = gtk.HBox()

        label = gtk.Label()
        label.set_angle(90)

        if (sequencetraceviewer.getSequenceTrace().isReverseComplemented()):
            labeltxt = 'Reverse'
        else:
            labeltxt = 'Forward'

        label.set_markup(labeltxt)

        frame = gtk.Frame()
        frame.set_shadow_type(gtk.SHADOW_IN)
        #frame.add(label)

        self.hbox.pack_start(label, False)
        self.hbox.pack_start(self.viewer.getWidget())

        self.hbox.show_all()

    def getWidget(self):
        return self.hbox


class ScrollAndZoomSTVDecorator(SequenceTraceViewerDecorator):
    def __init__(self, sequencetraceviewer):
        SequenceTraceViewerDecorator.__init__(self, sequencetraceviewer)

        self.scrolledwin = gtk.ScrolledWindow()

        seqt = self.viewer.getSequenceTrace()

        self.zoom_100 = 2.4

        oldwidth, oldheight = self.viewer.getWidget().get_size_request()
        #oldheight = 200
        self.viewer.getWidget().set_size_request(int(seqt.getTraceLength() * self.zoom_100), oldheight)
        innerhbox = gtk.HBox(False)
        innerhbox.pack_start(self.viewer.getWidget(), expand=False, fill=False)
        self.scrolledwin.set_policy(gtk.POLICY_ALWAYS, gtk.POLICY_NEVER)
        self.scrolledwin.add_with_viewport(innerhbox)

    def getWidget(self):
        return self.scrolledwin

    def zoom(self, level):
        z_scale = float(level) / 100 * self.zoom_100

        # calculate the new width for the sequence trace viewer
        new_width = int(self.viewer.getSequenceTrace().getTraceLength() * z_scale)

        # calculate the new position for the scrollbar to keep the view centered
        # around its current location
        adj = self.scrolledwin.get_hadjustment()
        center = adj.get_value() + (adj.page_size / 2)
        pos = float(center) / adj.upper
        newpos = new_width * pos
        new_adjval = int(newpos - (adj.page_size / 2))
        if new_adjval < 0:
            new_adjval = 0
        elif new_adjval > (new_width - adj.page_size):
            new_adjval = new_width - adj.page_size

        # resize the sequence trace viewer
        oldwidth, oldheight = self.viewer.getWidget().get_size_request()
        self.viewer.getWidget().set_size_request(new_width, oldheight)

        # allow the resize to complete before repositioning the scrollbar
        while gtk.events_pending():
           gtk.main_iteration(False)
        adj.set_value(new_adjval)

    def scrollTo(self, basenum):
        adj = self.scrolledwin.get_hadjustment()
        seqt = self.viewer.getSequenceTrace()

        scend = adj.upper - adj.page_size
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
        offset = x * adj.page_size / scend
        x = x + offset - adj.page_size/2
        if x < 0:
            x = 0
        elif x > scend:
            x = scend
        #print adj.lower, adj.upper, adj.value
        adj.set_value(x)


class SequenceTraceLayout(gtk.VBox):
    def __init__(self, scrolled_cons_viewer, seqt_viewers):
        gtk.VBox.__init__(self)
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
            self.pack_start(viewer.getWidget(), expand=True, fill=True)
        self.pack_start(self.consv, expand=False, fill=True)

    def getTraceToolBar(self):
        return self.toolbar

    def createTraceToolBar(self):
        toolbar = gtk.Toolbar()
        #toolbar.set_orientation(gtk.ORIENTATION_VERTICAL)
        #toolbar.set_icon_size(gtk.ICON_SIZE_MENU)
        toolbar.set_icon_size(gtk.ICON_SIZE_LARGE_TOOLBAR)
        toolbar.set_style(gtk.TOOLBAR_ICONS)
        toolbar.set_show_arrow(False)

        # build the zoom controls
        self.zoomin_button = gtk.ToolButton(gtk.STOCK_ZOOM_IN)
        self.zoomin_button.set_homogeneous(False)
        self.zoomin_button.set_tooltip_text('Zoom in')
        self.zoomin_button.connect('clicked', self.zoomButtons, 1)
        toolbar.insert(self.zoomin_button, -1)

        self.zoomout_button = gtk.ToolButton(gtk.STOCK_ZOOM_OUT)
        self.zoomout_button.set_homogeneous(False)
        self.zoomout_button.set_tooltip_text('Zoom out')
        self.zoomout_button.connect('clicked', self.zoomButtons, -1)
        toolbar.insert(self.zoomout_button, -1)

        self.zoom_combo = gtk.combo_box_new_text()
        for zoom in self.zoom_levels:
            self.zoom_combo.append_text(str(zoom) + '%')
        self.zoom_combo.set_active(self.curr_zoom)
        self.zoom_combo.connect('changed', self.zoomComboBox)

        # place the combo box in a VButtonBox to prevent it from expanding vertically
        vbox = gtk.VButtonBox()
        vbox.pack_start(self.zoom_combo, False)
        t_item = gtk.ToolItem()
        t_item.add(vbox)
        t_item.set_tooltip_text('Adjust the zoom level')
        t_item.set_expand(False)
        toolbar.insert(t_item, -1)

        toolbar.insert(gtk.SeparatorToolItem(), -1)

        # build the y scale adjustment slider
        t_item = gtk.ToolItem()
        t_item.add(gtk.Label('Y:'))
        toolbar.insert(t_item, -1)

        self.vscale_adj = gtk.Adjustment(0, 0, 0)
        hslider = gtk.HScale(self.vscale_adj)
        hslider.set_draw_value(False)
        self.initYScaleSlider(self.selected_seqtv)

        sizereq = hslider.size_request()
        #hslider.set_size_request(sizereq[0], 100)
        hslider.set_size_request(60, sizereq[1])

        self.y_slider = gtk.ToolItem()
        self.y_slider.add(hslider)
        self.y_slider.set_tooltip_text('Adjust the Y scale of the trace view')
        toolbar.insert(self.y_slider, -1)

        self.vscale_adj.connect('value_changed', self.yScaleChanged)

        toolbar.insert(gtk.SeparatorToolItem(), -1)

        # build the toggle button for phred scores
        toggle = gtk.CheckButton()
        toggle.set_label('conf. scores')
        toggle.set_active(True)
        toggle.connect('toggled', self.showConfToggled)

        # place the toggle button in a VButtonBox to prevent it from expanding vertically
        vbox = gtk.VButtonBox()
        vbox.pack_start(toggle, False)
        t_item = gtk.ToolItem()
        t_item.add(vbox)
        t_item.set_tooltip_text('Turn the display of phred scores on or off')
        t_item.set_expand(False)
        toolbar.insert(t_item, -1)

        # if we got two sequences, build a combo box to choose between them
        if len(self.seqt_viewers) == 2:
            trace_combo = gtk.combo_box_new_text()

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
            vbox = gtk.VButtonBox()
            vbox.pack_start(trace_combo, False)
            t_item = gtk.ToolItem()
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
        self.zoom_combo.set_active(self.curr_zoom + increment)

    def zoomComboBox(self, combobox):
        self.curr_zoom = self.zoom_combo.get_active()

        if self.curr_zoom == (len(self.zoom_levels) - 1):
            self.zoomin_button.set_sensitive(False)
        elif not(self.zoomin_button.get_sensitive()):
            self.zoomin_button.set_sensitive(True)

        if self.curr_zoom == 0:
            self.zoomout_button.set_sensitive(False)
        elif not(self.zoomout_button.get_sensitive()):
            self.zoomout_button.set_sensitive(True)

        if self.selected_seqtv == len(self.seqt_viewers):
            for viewer in self.seqt_viewers:
                viewer.zoom(self.zoom_levels[self.curr_zoom])
        else:
            self.seqt_viewers[self.selected_seqtv].zoom(self.zoom_levels[self.curr_zoom])


class TraceFileInfoWin(gtk.Window):
    keydesc = {
            'NAME': 'Sample name',
            'LANE': 'Lane',
            'SIGN': 'Dye signal strengths',
            'SPAC': 'Mean peak spacing',
            'RUND': 'Run dates and times',
            'DATE': 'Run dates and times',
            'DYEP': 'Mobility file name',
            'MACH': 'Machine name and serial no.',
            'MODL': 'Machine model',
            'BCAL': 'Basecaller name',
            'VER1': 'Data coll. software ver.',
            'VER2': 'Basecaller version'
            }

    disp_order = ['MACH', 'MODL', 'VER1', 'BCAL', 'VER2', 'DYEP', 'RUND', 'DATE', 'NAME', 'LANE', 'SIGN', 'SPAC']

    def __init__(self, seqtraces):
        gtk.Window.__init__(self, gtk.WINDOW_TOPLEVEL)

        self.seqtraces = seqtraces

        self.set_title('File Information')

        self.vbox = gtk.VBox(False, 6)
        self.vbox.set_border_width(6)
        self.add(self.vbox)

        # set up the tabs ("notebook") object
        nb = gtk.Notebook()
        nb.set_tab_pos(gtk.POS_TOP)

        for seqtr in seqtraces:
            label = self.makeInfoLabel(seqtr)
            nb.append_page(label, gtk.Label(seqtr.getFileName()))

        self.vbox.pack_start(nb)

        # create the 'Close' button
        bbox = gtk.HButtonBox()
        bbox.set_layout(gtk.BUTTONBOX_END)
        button = gtk.Button('Close', gtk.STOCK_CLOSE)
        button.connect('clicked', self.closeWindow)
        bbox.add(button)
        self.vbox.pack_start(bbox)

        self.vbox.show_all()
        self.show()
    
    def makeInfoLabel(self, seqtr):
        labelstr = ''

        comments = seqtr.getComments()

        # get all the comments we have a specified sort order for
        for key in self.disp_order:
            if key in comments:
                labelstr += ('<b>{0}:</b>  {1}\n').format(self.getKeyDesc(key), comments[key])

        # get any remaining comments
        for key, value in sorted(comments.iteritems()):
            value = xml.sax.saxutils.escape(value)
            if key not in self.disp_order:
                labelstr += ('<b>{0}:</b>  {1}\n').format(self.getKeyDesc(key), value)

        # remove the extra '\n' at the end of the label string
        labelstr = labelstr[:-1]
            
        label = gtk.Label()
        label.set_alignment(0, 0)
        label.set_padding(12, 8)
        label.set_selectable(True)
        label.set_markup(labelstr)

        return label

    def getKeyDesc(self, key):
        if key in self.keydesc:
            return self.keydesc[key]
        else:
            return key

    def closeWindow(self, widget):
        self.destroy()


class TraceWindow(gtk.Window, CommonDialogs, Observable):
    def __init__(self, mod_consseq_builder, is_mainwindow=False, id_num=-1):
        gtk.Window.__init__(self, gtk.WINDOW_TOPLEVEL)

        self.is_mainwindow = is_mainwindow
        self.id_num = id_num
        self.cons = mod_consseq_builder
        self.infowin = None

        # initialize the observable events for this class
        self.defineObservableEvents(['consensus_saved'])

        # initialize the window GUI elements and event handlers
        self.connect('destroy', self.destroyWindow)

        self.vbox = gtk.VBox(False, 0)
        self.add(self.vbox)

        # create the menus and toolbar
        menuxml = '''<menubar name="menubar">
        <menu action="File">
            <menuitem action="Save_Consens" />
            <separator />
            <menuitem action="Export_Alignment" />
            <menuitem action="Export_Consensus" />
            <menuitem action="Export_Raw" />
            <separator />
            <menuitem action="File_Info" />
            <separator />
            <menuitem action="Close" />
        </menu>
        <menu action="Edit">
            <menuitem action="Undo" />
            <menuitem action="Redo" />
            <separator />
            <menuitem action="Copy" />
            <menuitem action="Delete" />
            <menuitem action="Modify" />
            <separator />
            <menuitem action="Recalc_Consens" />
        </menu>
        </menubar>
        <popup name="editpopup">
            <menuitem action="Copy" />
            <menuitem action="Delete" />
            <menuitem action="Modify" />
            <separator />
            <menuitem action="Recalc_Consens" />
        </popup>
        <toolbar name="toolbar">
            <toolitem action="File_Info" />
            <separator />
            <toolitem action="Save_Consens" />
            <separator />
            <toolitem action="Undo" />
            <toolitem action="Redo" />
            <separator />
            <toolitem action="Copy" />
            <toolitem action="Delete" />
            <toolitem action="Modify" />
        </toolbar>'''

        # these actions are (usually) always enabled
        self.main_ag = gtk.ActionGroup('main_actions')
        self.main_ag.add_actions([
            ('File', None, '_File'),
            ('Save_Consens', gtk.STOCK_SAVE, '_Save working sequence to project', None, 'Save the working sequence to the project', self.saveConsensus),
            ('Export_Alignment', None, 'Export _alignment...', None, 'Export the aligned forward and reverse sequences', self.exportAlignment),
            ('Export_Consensus', None, 'Export w_orking sequence...', None, 'Export the working sequence to a file', self.exportConsensus),
            ('Export_Raw', None, 'Export _raw sequence(s)...', None, 'Export the un-edited sequence(s) to a file', self.exportRawSequence),
            ('File_Info', gtk.STOCK_INFO, '_Information...', None, 'View detailed information about the file(s)', self.fileInfo),
            ('Close', gtk.STOCK_CLOSE, '_Close', None, 'Close this window', self.closeWindow),
            ('Edit', None, '_Edit'),
            ('Recalc_Consens', None, '_Recalculate working seq.', None, 'Recalculate the working sequence', self.recalcConsensus)])

        # these actions are for common edit commands
        self.edit_ag = gtk.ActionGroup('edit_actions')
        self.edit_ag.add_actions([
            ('Undo', gtk.STOCK_UNDO, '_Undo', '<ctl>z', 'Undo the last change to the working sequence', self.undoConsChange),
            ('Redo', gtk.STOCK_REDO, '_Redo', '<ctl>y', 'Redo the last change to the working sequence', self.redoConsChange)])

        # these actions are only enabled when there is an active selection
        self.sel_edit_ag = gtk.ActionGroup('selected_edit_actions')
        self.sel_edit_ag.add_actions([
            ('Copy', gtk.STOCK_COPY, '_Copy selected base(s) to clipboard', None, 'Copy the selected base(s) to the system clipboard', self.copyConsBases),
            ('Delete', gtk.STOCK_DELETE, '_Delete selected base(s)', None, 'Delete the selected base(s) from the working sequence', self.deleteConsBases),
            ('Modify', gtk.STOCK_EDIT, '_Modify selected base(s)...', None, 'Edit the selected base(s)', self.editConsBases)])

        self.uim = gtk.UIManager()
        self.add_accel_group(self.uim.get_accel_group())
        self.uim.insert_action_group(self.main_ag, 0)
        self.uim.insert_action_group(self.edit_ag, 0)
        self.uim.insert_action_group(self.sel_edit_ag, 0)
        self.uim.add_ui_from_string(menuxml)
        self.vbox.pack_start(self.uim.get_widget('/menubar'), expand=False, fill=False)

        toolbar_hbox = gtk.HBox()
        self.uim.get_widget('/toolbar').set_show_arrow(False)
        self.uim.get_widget('/toolbar').set_icon_size(gtk.ICON_SIZE_LARGE_TOOLBAR)
        self.uim.get_widget('/toolbar').set_style(gtk.TOOLBAR_ICONS)
        toolbar_hbox.pack_start(self.uim.get_widget('/toolbar'), expand=False, fill=False)
        self.vbox.pack_start(toolbar_hbox, expand=False, fill=False)

        # disable some menus/toolbar buttons by default
        self.edit_ag.get_action('Undo').set_sensitive(False)
        self.edit_ag.get_action('Redo').set_sensitive(False)
        self.sel_edit_ag.set_sensitive(False)

        self.loadSequenceTraces()

        # if there is only one trace file, disable the "export alignment" action
        if self.numseqs < 2:
            self.main_ag.get_action('Export_Alignment').set_sensitive(False)

        # get the trace file(s) toolbar
        trace_tb = self.stlayout.getTraceToolBar()
        for cnt in range(0, 2):
            blank = gtk.SeparatorToolItem()
            blank.set_draw(False)
            #self.uim.get_widget('/toolbar').insert(blank, 0)
            trace_tb.insert(blank, 0)
        toolbar_hbox.pack_start(trace_tb, True, True)

        # add a consensus sequence status bar at the bottom of the window
        sbar = ConsensSeqStatusBar(self.cons)
        self.vbox.pack_start(sbar, False)

        self.vbox.show_all()
        self.vbox.show()

        # by default, do not show the "Save_Consens" action UI elements
        self.main_ag.get_action('Save_Consens').set_visible(False)

        self.setDefaultGeometry()

        self.show()
        self.set_focus(None)

    def setDefaultGeometry(self):
        #print self.get_size()
        width, height = self.get_size()

        screen = self.get_screen()

        # calculate the default width based on the screen size
        new_width = (screen.get_width() * 5) / 6

        # calculate the default height based on the preferred size of the sequence trace viewers
        v_height = self.viewers[0].getDefaultHeight()
        v_pref_height = self.viewers[0].getPreferredHeight()
        diff = v_pref_height - v_height

        new_height = height + self.numseqs * diff

        #print new_width, new_height
        self.set_default_size(new_width, new_height)
        self.set_position(gtk.WIN_POS_CENTER)

    def setSaveEnabled(self, state):
        self.main_ag.get_action('Save_Consens').set_sensitive(state)
        
    def registerObserver(self, event_name, handler):
        """ Extends the registerObserver() method in Observable to allow GUI elements to respond
        to observer registration. """

        Observable.registerObserver(self, event_name, handler)

        if event_name == 'consensus_saved':
            # show the "Save_Consens" action UI elements since someone's actually listening for this signal
            self.main_ag.get_action('Save_Consens').set_visible(True)

    def saveConsensus(self, widget):
        self.notifyObservers('consensus_saved',
                (self, self.cons.getCompactConsensus(), self.cons.getConsensus()))

    def getIdNum(self):
        return self.id_num

    def loadSequenceTraces(self):
        self.numseqs = self.cons.getNumSeqs()
        self.seqt1 = self.cons.getSequenceTrace(0)
        if self.numseqs == 2:
            self.seqt2 = self.cons.getSequenceTrace(1)
        else:
            self.seqt2 = None

        viewer = ScrollAndZoomSTVDecorator(SequenceTraceViewer(self.seqt1))
        if self.numseqs == 2:
            viewer = FwdRevSTVDecorator(viewer)
        self.viewers = [ viewer ]
        if self.seqt2 != None:
            viewer = ScrollAndZoomSTVDecorator(SequenceTraceViewer(self.seqt2))
            self.viewers.append(FwdRevSTVDecorator(viewer))

        self.consview = ScrolledConsensusSequenceViewer(self.cons)

        # add the sequence trace layout to the window
        self.stlayout = SequenceTraceLayout(self.consview, self.viewers)
        self.vbox.pack_start(self.stlayout, expand=True, fill=True)

        # register callbacks for the consensus sequence viewer
        self.consview.getConsensusSequenceViewer().registerObserver('alignment_clicked', self.alignmentClicked)
        self.consview.getConsensusSequenceViewer().registerObserver('consensus_clicked', self.consensusSeqClicked)
        self.consview.getConsensusSequenceViewer().registerObserver('selection_state', self.selectStateChange)

        # register callbacks for the consensus sequence model
        self.cons.registerObserver('undo_state_changed', self.undoStateChanged)
        self.cons.registerObserver('redo_state_changed', self.redoStateChanged)

        title = 'Trace View: ' + self.seqt1.getFileName()
        if self.numseqs == 2:
            title += ', ' + self.seqt2.getFileName()
        self.set_title(title)

    def alignmentClicked(self, seqnum, seq1index, seq2index):
        #print seqnum, seq1index, seq2index
        self.viewers[0].scrollTo(seq1index)
        self.viewers[0].getViewer().highlightBase(seq1index)
        if self.numseqs == 2:
            self.viewers[1].scrollTo(seq2index)
            self.viewers[1].getViewer().highlightBase(seq2index)

    def consensusSeqClicked(self, select_start, select_end, event):
        if event.button == 3:
            self.uim.get_widget('/editpopup').popup(None, None, None, event.button, event.time)

    def selectStateChange(self, selection_exists):
        if selection_exists:
            self.sel_edit_ag.set_sensitive(True)
        else:
            self.sel_edit_ag.set_sensitive(False)

    def undoStateChanged(self, has_undo):
        if has_undo:
            self.edit_ag.get_action('Undo').set_sensitive(True)
        else:
            self.edit_ag.get_action('Undo').set_sensitive(False)

    def redoStateChanged(self, has_redo):
        if has_redo:
            self.edit_ag.get_action('Redo').set_sensitive(True)
        else:
            self.edit_ag.get_action('Redo').set_sensitive(False)

    def undoConsChange(self, widget):
        self.cons.undo()
        self.setSaveEnabled(True)

    def redoConsChange(self, widget):
        self.cons.redo()
        self.setSaveEnabled(True)

    def copyConsBases(self, widget):
        csv = self.consview.getConsensusSequenceViewer()
        sel = csv.getSelection()
        seq = self.cons.getConsensus(sel[0], sel[1])

        pyperclip.copy(seq)

    def deleteConsBases(self, widget):
        csv = self.consview.getConsensusSequenceViewer()
        sel = csv.getSelection()
        self.cons.deleteBases(sel[0], sel[1])
        self.setSaveEnabled(True)

    def editConsBases(self, widget):
        csv = self.consview.getConsensusSequenceViewer()
        sel = csv.getSelection()
        seq = self.cons.getConsensus(sel[0], sel[1])

        # display a text-entry dialog to allow the user to modify the selected base(s)
        diag = EntryDialog(self, 'Edit Sequence',
                'You may make changes to the selected base(s) below.\n\nOriginal sequence: {0} ({1} bases)\n'.format(seq, len(seq)),
                seq, 50)

        # display the dialog until the user presses cancel, closes the dialog, or submits an acceptable string
        newseq = ''
        while len(newseq) != len(seq):
            response = diag.run()
            if (response == gtk.RESPONSE_CANCEL) or (response == gtk.RESPONSE_DELETE_EVENT):
                break
            newseq = diag.get_text().upper()
            if len(newseq) != len(seq):
                self.showMessage('The number of bases in the edited sequence must match the the selection.')

        diag.destroy()
        if response == gtk.RESPONSE_OK:
            self.cons.modifyBases(sel[0], sel[1], newseq)

        self.setSaveEnabled(True)

    def recalcConsensus(self, widget):
        response = self.showYesNoDialog('Are you sure you want to recalculate the working sequence?  This will overwrite any edits you have made.')
        if response != gtk.RESPONSE_YES:
            return

        self.cons.recalcConsensusSequence()
        self.setSaveEnabled(True)

    def fileInfo(self, widget):
        seqtraces = list()

        self.numseqs = self.cons.getNumSeqs()
        seqtraces.append(self.cons.getSequenceTrace(0))
        if self.numseqs == 2:
            seqtraces.append(self.cons.getSequenceTrace(1))

        if self.infowin != None:
            self.infowin.present()
        else:
            self.infowin = TraceFileInfoWin(seqtraces)
            self.infowin.connect('destroy', self.fileInfoDestroyed)

    def fileInfoDestroyed(self, win):
        self.infowin = None

    def exportConsensus(self, widget):
        # create a file chooser dialog to get a file name and format from the user
        fc = seqwriter.SeqWriterFileDialog(self, 'Export Consensus Sequence')
        response = fc.run()
        fname = fc.get_filename()
        fformat = fc.getFileFormat()
        fc.destroy()
        if response != gtk.RESPONSE_OK:
            return

        # write out the sequence
        sw = seqwriter.SequenceWriterFactory.getSequenceWriter(fformat)
        try:
            sw.open(fname)
        except IOError:
            self.showMessage('The file "' + fname + '" could not be opened for writing.  ' +
                    'Verify that you have permission to write to the specified file and directory.')
            return

        desc = 'consensus'
        seqfname = self.cons.getSequenceTrace(0).getFileName()
        if self.numseqs == 2:
            seqfname += ', ' + self.cons.getSequenceTrace(1).getFileName()
        sw.addUnalignedSequence(self.cons.getCompactConsensus(), seqfname, desc)

        sw.write()

    def exportRawSequence(self, widget):
        # create a file chooser dialog to get a file name and format from the user
        fc = seqwriter.SeqWriterFileDialog(self, 'Export Raw Sequence(s)')
        response = fc.run()
        fname = fc.get_filename()
        fformat = fc.getFileFormat()
        fc.destroy()
        if response != gtk.RESPONSE_OK:
            return

        # write out the sequence
        sw = seqwriter.SequenceWriterFactory.getSequenceWriter(fformat)
        try:
            sw.open(fname)
        except IOError:
            self.showMessage('The file "' + fname + '" could not be opened for writing.  ' +
                    'Verify that you have permission to write to the specified file and directory.')
            return

        for cnt in range(0, self.numseqs):
            seqfname = self.cons.getSequenceTrace(cnt).getFileName()
            desc = 'raw sequence'
            if self.cons.getSequenceTrace(cnt).isReverseComplemented():
                desc += ' (reverse complemented)'
            sw.addUnalignedSequence(self.cons.getSequenceTrace(cnt).getBaseCalls(), seqfname, desc)

        sw.write()

    def exportAlignment(self, widget):
        # create a file chooser dialog to get a file name and format from the user
        fc = seqwriter.SeqWriterFileDialog(self, 'Export Alignment')
        response = fc.run()
        fname = fc.get_filename()
        fformat = fc.getFileFormat()
        fc.destroy()
        if response != gtk.RESPONSE_OK:
            return

        # write out the sequences
        sw = seqwriter.SequenceWriterFactory.getSequenceWriter(fformat)
        try:
            sw.open(fname)
        except IOError:
            self.showMessage('The file "' + fname + '" could not be opened for writing.  ' +
                    'Verify that you have permission to write to the specified file and directory.')
            return

        for cnt in range(0, self.numseqs):
            seqfname = self.cons.getSequenceTrace(cnt).getFileName()
            desc = 'sequence ' + str(cnt)
            if self.cons.getSequenceTrace(cnt).isReverseComplemented():
                desc += ' (reverse complemented)'
            sw.addAlignedSequence(self.cons.getAlignedSequence(cnt), seqfname, desc)

        sw.write()

    def closeWindow(self, widget):
        self.destroy()

    def destroyWindow(self, widget, data=None):
        # close the file information window, if it exists
        if self.infowin != None:
            self.infowin.destroy()

        # unregister this window as an observer of the consensus sequence viewer
        self.consview.getConsensusSequenceViewer().unregisterObserver('alignment_clicked', self.alignmentClicked)
        self.consview.getConsensusSequenceViewer().unregisterObserver('consensus_clicked', self.consensusSeqClicked)
        self.consview.getConsensusSequenceViewer().unregisterObserver('selection_state', self.selectStateChange)

        # unregister this window as an observer of the consensus sequence
        self.cons.unregisterObserver('undo_state_changed', self.undoStateChanged)
        self.cons.unregisterObserver('redo_state_changed', self.redoStateChanged)

        if self.is_mainwindow:
            gtk.main_quit()
            



if __name__ == '__main__':
    #print sequencetrace.SequenceTraceFactory.getTraceFileType('forward.ztr')

    #seqt1 = sequencetrace.ZTRSequenceTrace()
    #seqt1.loadFile('forward.ztr')
    seqt1 = sequencetrace.ABISequenceTrace()
    seqt1.loadFile('forward.ab1')
    #seqt1.reverseComplement()
    #seqt2 = sequencetrace.ZTRSequenceTrace()
    #seqt2.loadFile('reverse.ztr')
    #seqt2.reverseComplement()

    #seqt1 = sequencetrace.SequenceTraceFactory.loadTraceFile('forward.scf')


    from seqtrace.core import consens
    cons = consens.ModifiableConsensSeqBuilder((seqt1,))
    #cons = ModifiableConsensSeqBuilder((seqt1, seqt2))

    mainwin = TraceWindow(cons, is_mainwindow=True)
    gtk.main()

