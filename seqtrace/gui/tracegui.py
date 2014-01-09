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

import pygtk
pygtk.require('2.0')
import gtk
import pango

import os.path



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
