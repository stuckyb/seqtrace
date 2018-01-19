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


from seqtrace.core import sequencetrace
from seqtrace.core import seqwriter

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('PangoCairo', '1.0')
from gi.repository import Gtk
from gi.repository import Gdk
import cairo
from gi.repository import Pango, PangoCairo
import os.path

# Get the Gdk.RGBA convenience functions.
from colorfuncs import parseHTMLColorStr, colorFromHSV


class SequenceTraceViewer:
    def __init__(self, sequencetrace):
        self.min_height = 100
        self.preferred_height = 200

        self.drawingarea = Gtk.DrawingArea()
        self.drawingarea.set_size_request(-1, self.min_height)

        self.seqt = sequencetrace

        # Initialize drawing settings.
        self.tracecolors = {
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
            'N': parseHTMLColorStr('#999')        # gray
        }
        # Set up colors with an alpha channel to use for the lines from
        # the base calls to the trace peaks.
        self.pklinecolors = {}
        self.pklinecolors['A'] = (
            self.tracecolors['A'].red, self.tracecolors['A'].green,
            self.tracecolors['A'].blue, 0.84
        )
        self.pklinecolors['C'] = (
            self.tracecolors['C'].red, self.tracecolors['C'].green,
            self.tracecolors['C'].blue, 0.6
        )
        self.pklinecolors['G'] = (
            self.tracecolors['G'].red, self.tracecolors['G'].green,
            self.tracecolors['G'].blue, 0.6
        )
        self.pklinecolors['T'] = (
            self.tracecolors['T'].red, self.tracecolors['T'].green,
            self.tracecolors['T'].blue, 0.68
        )

        self.bottom_margin = 2
        self.bcpadding = 4

        self.show_confidence = True

        self.sigmax = sequencetrace.getMaxTraceVal() + (sequencetrace.getMaxTraceVal() / 12)

        self.bclayout = Pango.Layout(self.drawingarea.create_pango_context())

        # Get the default font used by Gtk+ and use it as the default for the
        # trace display.
        fontstr = Gtk.Settings.get_default().props.gtk_font_name
        default_font = Pango.FontDescription.from_string(fontstr)
        self.setFontDescription(default_font)

        self.drawingarea.connect('draw', self.doDraw)

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

        self.drawingarea.queue_draw()

    def setShowConfidence(self, newval):
        """
        Toggles the display of the confidence bars and scores.
        """
        self.show_confidence = newval

        self.drawingarea.queue_draw()

    def setFontDescription(self, fontdesc):
        # Set up the base call font properties.
        self.bcfontdesc = fontdesc.copy()
        #self.bcfontdesc.set_size(20*Pango.SCALE)
        self.bclayout.set_font_description(self.bcfontdesc)
        self.bclayout.set_text('A', 1)
        self.bcheight = self.bclayout.get_pixel_size()[1] + (self.bcpadding*2)

    def doDraw(self, da, cr):
        clipr = cr.clip_extents()
        #print clipr
        startx = clipr[0]
        dwidth = clipr[2] - clipr[0]
        height = self.drawingarea.get_allocated_height()
        #print 'startx: {0}, dwidth: {1}, height: {2}'.format(startx, dwidth, height)
        if startx > 0:
            # Becase the Cairo coordinates are shifted by +0.5 for the trace
            # drawing, make sure that we have sufficient overlap with previous
            # drawing operations so that we don't get breaks in the
            # antialiasing.
            startx -= 1
            dwidth += 1

        cr.set_antialias(cairo.ANTIALIAS_DEFAULT)
        cr.set_line_join(cairo.LINE_JOIN_ROUND)

        drawhighlight = False
        rect = None
        # Check if a highlight is active.
        if self.highlighted != self.seqt.getNumBaseCalls():
            # Check if the highlight is within the clip region.
            rect = self.getHighlightRectangle(self.highlighted)
            if not(
                (rect[0] > startx + dwidth) or (rect[0] + rect[2] < startx)
            ):
                drawhighlight = True

        self.drawBackground(startx, dwidth, cr)

        if drawhighlight:
            # Draw the "under" highlight as a solid color.
            self.drawHighlight(rect, 1.0, cr);

        self.drawBaseCalls(startx, dwidth, cr)
        self.drawTrace(startx, dwidth, cr)

        if drawhighlight:
            # Draw the "over" highlight with transparency.
            self.drawHighlight(rect, 0.4, cr);

    def drawBackground(self, startx, dwidth, cr):
        cr.set_source_rgba(1.0, 1.0, 1.0)
        cr.paint()

    def drawTrace(self, startx, dwidth, cr):
        """
        Draw the trace lines using Cairo.  Note that because we are drawing
        1-pixel width lines, 0.5 is added to the x and y coordinates, which
        guarantees that the lines are drawn in the same position as with
        the regular GTK drawing routines and also ensures that vertical and
        horizontal lines are exactly 1 pixel wide.

        startx: The x position at which to start drawing.
        dwidth: The width (in pixels) to draw.  If dwidth is 0, the entire
            surface will be drawn.
        """
        width = self.drawingarea.get_allocated_width()
        height = self.drawingarea.get_allocated_height()
        if dwidth == 0:
            dwidth = width

        drawheight = height - self.bottom_margin - self.bcheight

        cr.set_line_width(1)

        samps = self.seqt.getTraceLength()
        startsamp = int(startx * samps) / width
        endsamp = int((float(startx+dwidth) * samps) / width + 0.5)
        if endsamp < (samps-1):
            endsamp += 2

        yscale = float(drawheight) / self.sigmax
        xscale = float(width) / samps

        for base in ('A','C','G','T'):
            cr.set_source_rgba(*self.tracecolors[base])
            data = self.seqt.getTraceSamples(base)

            oldx = int(startsamp * xscale)
            oldy = int((self.sigmax - data[startsamp]) * yscale + 0.5)
            for cnt in range(startsamp, endsamp):
                x = int(cnt * xscale)
                y = int((self.sigmax - data[cnt]) * yscale + 0.5)
                cr.move_to(oldx+0.5, oldy+0.5)
                cr.line_to(x+0.5, y+0.5)
                oldx = x
                oldy = y
            cr.stroke()

    def drawBaseCalls(self, startx, dwidth, cr):
        """
        Draws the base calls, confidence scores and bars, and lines from
        the base calls to the trace peaks.

        startx: The x position at which to start drawing.
        dwidth: The width (in pixels) to draw.  If dwidth is 0, the entire
            surface will be drawn.
        """
        width = self.drawingarea.get_allocated_width()
        height = self.drawingarea.get_allocated_height()
        if dwidth == 0:
            dwidth = width

        # Save the Cairo context settings.
        cr.save()
        cr.set_dash((1,1))
        cr.set_line_width(1)

        # Calculate the confidence bar dimensions.
        drawheight = height - self.bottom_margin - self.bcheight
        confbarmax = drawheight / 4
        self.bclayout.set_text('30', -1)
        confbarwidth = self.bclayout.get_pixel_size()[0] * 0.8
        conf_hue_best = 0.68
        conf_hue_worst = 1.0

        samps = self.seqt.getTraceLength()
        startsamp = int(startx * samps) / width
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

        confbarcolor = Gdk.RGBA()
        confbarcolor.parse('#c8c8c8')

        for index in range(startbcindex, endbcindex):
            # Get the base and position.
            base = self.seqt.getBaseCall(index)
            pos = self.seqt.getBaseCallPos(index)

            x = int(pos * xscale)

            if self.show_confidence:
                # Draw the confidence bar.
                bcconf = self.seqt.getBaseCallConf(index)
                cr.set_source_rgba(*confbarcolor)
                #hue = float(bcconf) * (conf_hue_best - conf_hue_worst) / 61 + conf_hue_worst
                #cr.set_source_rgba(*colorFromHSV(hue, 0.34, 1.0))
                cr.rectangle(x-(confbarwidth / 2), 6, confbarwidth, (confbarmax*bcconf)/61)
                cr.fill()

                # Draw the confidence score.
                hue = float(bcconf) * (conf_hue_best - conf_hue_worst) / 61 + conf_hue_worst
                cr.set_source_rgba(*colorFromHSV(hue, 1.0, 0.9))
                self.bclayout.set_text(str(bcconf), -1)
                txtwidth = self.bclayout.get_pixel_size()[0]
                cr.move_to(x - (txtwidth/2), 6)
                PangoCairo.layout_path(cr, self.bclayout)
                cr.fill()

            # Draw the base.
            cr.set_source_rgba(*self.tracecolors[base])
            self.bclayout.set_text(base, 1)
            txtwidth = self.bclayout.get_pixel_size()[0]
            cr.move_to(x - (txtwidth/2), y)
            PangoCairo.layout_path(cr, self.bclayout)
            cr.fill()

            # Calculate the y coordinate of the trace location for this base and draw a line to
            # it from the base call.  It only makes sense to do this for non-ambiguous bases.
            if base in ('A', 'T', 'G', 'C'):
                traceval = self.seqt.getTraceSample(base, pos)
                ysamp = int((self.sigmax - traceval) * yscale + 0.5)

                # Draw the line to the trace.
                # As with drawing the trace lines, add 0.5 to the x coordinates to ensure
                # the lines appear in the "correct" location (with reference to the standard
                # GTK drawing routines and that they are exactly 1 pixel wide.
                cr.set_source_rgba(*self.pklinecolors[base])
                cr.move_to(x+0.5, ysamp)
                cr.line_to(x+0.5, y-(self.bcpadding/2))
                cr.stroke()

        # Restore the old Cairo context settings.
        cr.restore()

    def highlightBase(self, bindex):
        """
        Highlights a base call position or gap on the trace, and erases the old
        highlight (if there is one).
        """
        # Draw the highlight, if needed.
        if bindex != self.highlighted:
            oldhighlight = self.highlighted
            self.highlighted = bindex

            if oldhighlight != self.seqt.getNumBaseCalls():
                # Erase the old highlight.
                rect = self.getHighlightRectangle(oldhighlight)
                self.drawingarea.queue_draw_area(*rect)

            # Draw the new highlight.
            rect = self.getHighlightRectangle(bindex)
            self.drawingarea.queue_draw_area(*rect)

    def getHighlightRectangle(self, bindex):
        """
        Given an alignment index, returns the location and size of the
        corresponding highlight rectangle as (x, y, width, height).
        """
        width = self.drawingarea.get_allocated_width()
        height = self.drawingarea.get_allocated_height()
        drawheight = height - self.bottom_margin - self.bcheight

        samps = self.seqt.getTraceLength()
        xscale = float(width) / samps
        yscale = float(drawheight) / self.sigmax
        y = drawheight + self.bcpadding

        # Check if we got a gap location.
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

        if bindex < 0:
            # Highlight size for a gap.
            return (x - 2, 0, 5, height)
        else:
            # Highlight size for a base call.
            return (x - 6, 0, 12, height)

    def drawHighlight(self, rect, alpha, cr):
        cr.set_source_rgba(1.0, 1.0, 0, alpha)

        cr.rectangle(*rect)
        cr.fill()

