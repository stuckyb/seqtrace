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
from seqtrace.core.consens import ConsensSeqBuilder
from seqtrace.core.observable import Observable

from seqtrace.gui.dialgs import CommonDialogs, EntryDialog
from seqtrace.gui.sequencegui import ScrolledConsensusSequenceViewer
from seqtrace.gui.tracegui import SequenceTraceViewer
from seqtrace.gui.tracelayout import SequenceTraceLayout
from seqtrace.gui.trace_decorators import (
    ScrollAndZoomSTVDecorator, FwdRevSTVDecorator
)
from seqtrace.gui.statusbar import ConsensSeqStatusBar

import xml.sax.saxutils
import os
import re

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk



class TraceFileInfoWin(Gtk.Window):
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
        Gtk.Window.__init__(self, Gtk.WindowType.TOPLEVEL)

        self.seqtraces = seqtraces

        self.set_title('File Information')

        self.vbox = Gtk.VBox(False, 6)
        self.vbox.set_border_width(6)
        self.add(self.vbox)

        # set up the tabs ("notebook") object
        nb = Gtk.Notebook()
        nb.set_tab_pos(Gtk.PositionType.TOP)

        for seqtr in seqtraces:
            label = self.makeInfoLabel(seqtr)
            nb.append_page(label, Gtk.Label(label=seqtr.getFileName()))

        self.vbox.pack_start(nb, True, True, 0)

        # create the 'Close' button
        bbox = Gtk.HButtonBox()
        bbox.set_layout(Gtk.ButtonBoxStyle.END)
        button = Gtk.Button('Close', Gtk.STOCK_CLOSE)
        button.connect('clicked', self.closeWindow)
        bbox.add(button)
        self.vbox.pack_start(bbox, True, True, 0)

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
            
        label = Gtk.Label()
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


class TraceWindow(Gtk.Window, CommonDialogs, Observable):
    def __init__(self, mod_consseq_builder, is_mainwindow=False, id_num=-1):
        Gtk.Window.__init__(self, Gtk.WindowType.TOPLEVEL)

        self.is_mainwindow = is_mainwindow
        self.id_num = id_num
        self.cons = mod_consseq_builder
        self.infowin = None

        # initialize the observable events for this class
        self.defineObservableEvents(['consensus_saved'])

        # initialize the window GUI elements and event handlers
        self.connect('destroy', self.destroyWindow)

        self.vbox = Gtk.VBox(False, 0)
        self.add(self.vbox)

        # create the menus and toolbar
        menuxml = '''<menubar name="menubar">
        <menu action="File">
            <menuitem action="Save_Consens" />
            <separator />
            <menuitem action="Export_Alignment" />
            <menuitem action="Export_Raw" />
            <menuitem action="Export_Consensus" />
            <separator />
            <menuitem action="File_Info" />
            <separator />
            <menuitem action="Close" />
        </menu>
        <menu action="Edit">
            <menuitem action="Undo" />
            <menuitem action="Redo" />
            <separator />
            <menuitem action="Copy_Alignment" />
            <menuitem action="Copy_Raw" />
            <menuitem action="Copy_Consens" />
            <separator />
            <menuitem action="Copy" />
            <menuitem action="Delete" />
            <menuitem action="Modify" />
            <separator />
            <menuitem action="Recalc_Consens" />
        </menu>
        <menu action="View">
            <menuitem action="Select_Font" />
            <menuitem action="Scroll_Lock" />
        </menu>
        </menubar>
        <popup name="editpopup">
            <menuitem action="Copy_Consens" />
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

        # These actions are (usually) always enabled.
        self.main_ag = Gtk.ActionGroup('main_actions')
        self.main_ag.add_actions([
            ('File', None, '_File'),
            ('Save_Consens', Gtk.STOCK_SAVE, '_Save working sequence to project', None, 'Save the working sequence to the project', self.saveConsensus),
            ('Export_Consensus', None, 'Export w_orking sequence...', None, 'Export the working sequence to a file', self.exportConsensus),
            ('Export_Raw', None, 'Export _raw sequence(s)...', None, 'Export the un-edited sequence(s) to a file', self.exportRawSequence),
            ('File_Info', Gtk.STOCK_INFO, '_Information...', None, 'View detailed information about the file(s)', self.fileInfo),
            ('Close', Gtk.STOCK_CLOSE, '_Close', None, 'Close this window', self.closeWindow),
            ('Edit', None, '_Edit'),
            ('Copy_Consens', None, 'C_opy working sequence', None, 'Copy the working sequence to the clipboard', self.copyFullConsensus),
            ('Copy_Raw', None, 'Co_py raw sequence(s)', None, 'Copy the raw sequence(s) to the clipboard', self.copyRawSequences),
            ('Recalc_Consens', None, '_Recalculate working seq.', None, 'Recalculate the working sequence', self.recalcConsensus),
            ('View', None, '_View'),
            ('Select_Font', None, 'Select _font...', None, 'Select the font to use for the sequencing trace display', self.selectFont)
        ])

        # These actions are enabled only when there are two sequencing traces
        # in the window.
        self.twotrace_ag = Gtk.ActionGroup('twotrace_actions')
        self.twotrace_ag.add_actions([
            ('Export_Alignment', None, 'Export _alignment...', None, 'Export the aligned forward and reverse sequences', self.exportAlignment),
            ('Copy_Alignment', None, 'Cop_y alignment', None, 'Copy the forward/reverse alignment to the clipboard', self.copyAlignment)
        ])
        self.twotrace_ag.add_toggle_actions([
            ('Scroll_Lock', None, '_Synchronize trace scrolling', None, 'Synchronizes the scrolling of the forward and reverse traces', self.lockScrolling, True)
        ])

        # These actions are for common edit commands.
        self.edit_ag = Gtk.ActionGroup('edite_actions')
        self.edit_ag.add_actions([
            ('Undo', Gtk.STOCK_UNDO, '_Undo', '<ctl>z', 'Undo the last change to the working sequence', self.undoConsChange),
            ('Redo', Gtk.STOCK_REDO, '_Redo', '<ctl>y', 'Redo the last change to the working sequence', self.redoConsChange)
        ])

        # These actions are only enabled when there is an active selection.
        self.sel_edit_ag = Gtk.ActionGroup('selected_edit_actions')
        self.sel_edit_ag.add_actions([
            ('Copy', Gtk.STOCK_COPY, '_Copy selected base(s)', '<ctl>c', 'Copy the selected base(s) to the system clipboard', self.copyConsBases),
            ('Delete', Gtk.STOCK_DELETE, '_Delete selected base(s)', None, 'Delete the selected base(s) from the working sequence', self.deleteConsBases),
            ('Modify', Gtk.STOCK_EDIT, '_Modify selected base(s)...', None, 'Edit the selected base(s)', self.editConsBases)
        ])

        self.uim = Gtk.UIManager()
        self.add_accel_group(self.uim.get_accel_group())
        self.uim.insert_action_group(self.main_ag, 0)
        self.uim.insert_action_group(self.twotrace_ag, 0)
        self.uim.insert_action_group(self.edit_ag, 0)
        self.uim.insert_action_group(self.sel_edit_ag, 0)
        self.uim.add_ui_from_string(menuxml)
        self.vbox.pack_start(self.uim.get_widget('/menubar'), False, False, 0)

        toolbar_hbox = Gtk.HBox()
        self.uim.get_widget('/toolbar').set_show_arrow(False)
        self.uim.get_widget('/toolbar').set_icon_size(Gtk.IconSize.LARGE_TOOLBAR)
        self.uim.get_widget('/toolbar').set_style(Gtk.ToolbarStyle.ICONS)
        toolbar_hbox.pack_start(self.uim.get_widget('/toolbar'), False, False, 0)
        self.vbox.pack_start(toolbar_hbox, False, False, 0)

        # disable some menus/toolbar buttons by default
        self.edit_ag.get_action('Undo').set_sensitive(False)
        self.edit_ag.get_action('Redo').set_sensitive(False)
        self.sel_edit_ag.set_sensitive(False)

        self.loadSequenceTraces()

        # If there is only one trace file, disable the actions that require two traces.
        if self.numseqs < 2:
            self.twotrace_ag.set_sensitive(False)

        # get the trace file(s) toolbar
        trace_tb = self.stlayout.getTraceToolBar()
        for cnt in range(0, 2):
            blank = Gtk.SeparatorToolItem()
            blank.set_draw(False)
            #self.uim.get_widget('/toolbar').insert(blank, 0)
            trace_tb.insert(blank, 0)
        toolbar_hbox.pack_start(trace_tb, True, True, 0)

        # add a consensus sequence status bar at the bottom of the window
        sbar = ConsensSeqStatusBar(self.cons)
        self.vbox.pack_start(sbar, False, True, 0)

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
        self.set_position(Gtk.WindowPosition.CENTER)

    def setSaveEnabled(self, state):
        self.main_ag.get_action('Save_Consens').set_sensitive(state)
        
    def registerObserver(self, event_name, handler):
        """
        Extends the registerObserver() method in Observable to allow GUI elements to respond
        to observer registration.
        """
        Observable.registerObserver(self, event_name, handler)

        if event_name == 'consensus_saved':
            # Show the "Save_Consens" action UI elements since someone's actually listening for this signal.
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
        self.vbox.pack_start(self.stlayout, True, True, 0)

        # Register callbacks for the consensus sequence viewer.
        self.consview.getConsensusSequenceViewer().registerObserver(
            'consensus_clicked', self.consensusSeqClicked
        )
        self.consview.getConsensusSequenceViewer().registerObserver(
            'selection_state', self.selectStateChange
        )

        # register callbacks for the consensus sequence model
        self.cons.registerObserver('undo_state_changed', self.undoStateChanged)
        self.cons.registerObserver('redo_state_changed', self.redoStateChanged)

        title = 'Trace View: ' + self.seqt1.getFileName()
        if self.numseqs == 2:
            title += ', ' + self.seqt2.getFileName()
        self.set_title(title)

    def selectFont(self, widget):
        """
        Displays a font chooser dialog and sets the chosen font as the new font
        for the trace display.
        """
        fdiag = Gtk.FontChooserDialog(title='Font Selection', parent=self)
        fdiag.set_font_desc(self.stlayout.getFontDescription())
        fdiag.set_preview_text('A T G C')

        result = fdiag.run()
        if result == Gtk.ResponseType.OK:
            newfont = fdiag.get_font_desc()
            self.stlayout.setFontDescription(newfont)

        fdiag.destroy()

    def lockScrolling(self, widget):
        """
        Responds to clicks on the synchronize scrolling checkbox menu item.
        """
        if widget.get_active():
            self.stlayout.lockScrolling()
        else:
            self.stlayout.unlockScrolling()

    def consensusSeqClicked(self, select_start, select_end, event):
        if event.button == 3:
            self.uim.get_widget('/editpopup').popup(
                None, None, None, None, event.button, event.time
            )

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

    def copyAlignment(self, widget):
        """
        Copies the aligned raw sequences to the clipboard in basic FASTA
        format.
        """
        copy_text = ''
        for cnt in range(0, self.numseqs):
            if cnt > 0:
                copy_text += '\n'

            copy_text += '>' + self.cons.getSequenceTrace(cnt).getFileName()
            if self.cons.getSequenceTrace(cnt).isReverseComplemented():
                copy_text += ' (reverse complemented)'

            copy_text += '\n' + self.cons.getAlignedSequence(cnt)

        clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        clipboard.set_text(copy_text, -1)

    def copyFullConsensus(self, widget):
        """
        Copies the consensus sequence to the clipboard.
        """
        seq = self.cons.getConsensus()

        clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        clipboard.set_text(seq, -1)

    def copyRawSequences(self, widget):
        """
        Copies the raw base calls from the source trace file(s) to the
        clipboard in basic FASTA format.
        """
        copy_text = ''
        for cnt in range(0, self.numseqs):
            if cnt > 0:
                copy_text += '\n'

            copy_text += '>' + self.cons.getSequenceTrace(cnt).getFileName()
            if self.cons.getSequenceTrace(cnt).isReverseComplemented():
                copy_text += ' (reverse complemented)'

            copy_text += '\n' + self.cons.getSequenceTrace(cnt).getBaseCalls()

        clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        clipboard.set_text(copy_text, -1)

    def copyConsBases(self, widget):
        """
        Copies bases from the consensus sequence that are part of an active
        selection to the clipboard.
        """
        csv = self.consview.getConsensusSequenceViewer()
        sel = csv.getSelection()
        seq = self.cons.getConsensus(sel[0], sel[1])

        clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        clipboard.set_text(seq, -1)

    def deleteConsBases(self, widget):
        csv = self.consview.getConsensusSequenceViewer()
        sel = csv.getSelection()
        self.cons.deleteBases(sel[0], sel[1])
        self.setSaveEnabled(True)

    def editConsBases(self, widget):
        csv = self.consview.getConsensusSequenceViewer()
        sel = csv.getSelection()
        seq = self.cons.getConsensus(sel[0], sel[1])

        # Create a text-entry dialog to allow the user to modify the selected base(s).
        diag = EntryDialog(self, 'Edit Sequence',
                'You may make changes to the selected base(s) below.\n\nOriginal sequence: {0} ({1} bases)\n'.format(seq, len(seq)),
                seq, 50)

        # Build a regular expression object for checking if the characters in the new
        # string are all valid bases.
        reo = re.compile('[' + ''.join(ConsensSeqBuilder.allbases) + ' ]*')

        # Display the dialog until the user presses cancel, closes the dialog, or submits
        # an acceptable string.
        stringok = False
        while not(stringok):
            response = diag.run()
            if (response == Gtk.ResponseType.CANCEL) or (response == Gtk.ResponseType.DELETE_EVENT):
                break

            newseq = diag.get_text().upper()
            match = reo.match(newseq)

            # Verify that newseq is of the correct length and only contains valid bases.
            if len(newseq) != len(seq):
                self.showMessage('The number of bases in the edited sequence must match the the selection.')
            elif match.end() - match.start() != len(newseq):
                self.showMessage('The edited sequence contains invalid characters.  You may only use IUPAC nucleotide codes or spaces.')
            else:
                stringok = True

        diag.destroy()
        if response == Gtk.ResponseType.OK:
            self.cons.modifyBases(sel[0], sel[1], newseq)

        self.setSaveEnabled(True)

    def recalcConsensus(self, widget):
        response = self.showYesNoDialog('Are you sure you want to recalculate the working sequence?  This will overwrite any edits you have made.')
        if response != Gtk.ResponseType.YES:
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
        fc.set_current_folder(os.getcwd())
        response = fc.run()
        fname = fc.get_filename()
        fformat = fc.getFileFormat()
        fc.destroy()
        if response != Gtk.ResponseType.OK:
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
        fc.set_current_folder(os.getcwd())
        response = fc.run()
        fname = fc.get_filename()
        fformat = fc.getFileFormat()
        fc.destroy()
        if response != Gtk.ResponseType.OK:
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
        fc.set_current_folder(os.getcwd())
        response = fc.run()
        fname = fc.get_filename()
        fformat = fc.getFileFormat()
        fc.destroy()
        if response != Gtk.ResponseType.OK:
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

        # Unregister this window as an observer of the consensus sequence viewer.
        self.consview.getConsensusSequenceViewer().unregisterObserver('consensus_clicked', self.consensusSeqClicked)
        self.consview.getConsensusSequenceViewer().unregisterObserver('selection_state', self.selectStateChange)

        # Unregister this window as an observer of the consensus sequence.
        self.cons.unregisterObserver('undo_state_changed', self.undoStateChanged)
        self.cons.unregisterObserver('redo_state_changed', self.redoStateChanged)

        if self.is_mainwindow:
            Gtk.main_quit()
            



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
    Gtk.main()
