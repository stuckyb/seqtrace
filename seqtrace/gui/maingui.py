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
from seqtrace.core.consens import ConsensSeqBuilder, ModifiableConsensSeqBuilder
from seqtrace.core import stproject
from seqtrace.core import seqwriter
from seqtrace.core.stproject import SequenceTraceProject, ConsensSeqSettings
from seqtrace.core.observable import Observable

from seqtrace.gui.tracegui import TraceWindow
import seqtrace.gui.dialgs as dialgs
from seqtrace.gui.dialgs import CommonDialogs, EntryDialog, ProgressBarDialog
from seqtrace.gui.statusbar import ProjectStatusBar

import pygtk
pygtk.require('2.0')
import gtk
import pango

import sys
import os.path



class ProjectSettings(gtk.Dialog, CommonDialogs):
    def __init__(self, project):
        gtk.Dialog.__init__(self, 'Project Settings', None, gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                (gtk.STOCK_OK, gtk.RESPONSE_OK, gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))
        self.set_default_response(gtk.RESPONSE_OK)

        self.project = project

        mainvb = gtk.VBox(False, 30)
        mainvb.set_border_width(20)

        tracevb = gtk.VBox(False, 20)
        tracevb.set_border_width(10)

        # set up UI components for the trace file location
        vb = gtk.VBox()
        tf_hb1 = gtk.HBox()
        tf_hb1.pack_start(gtk.Label('Location of trace files:'), False)
        tf_hb2 = gtk.HBox()
        self.fc_entry = gtk.Entry()
        self.fc_entry.set_width_chars(40)
        self.fc_entry.set_text(self.project.getTraceFileDir())
        tf_hb2.pack_start(self.fc_entry)

        # use the STOCK_DIRECTORY icon for the button
        gtk.stock_add([('choose_dir', 'C_hoose...', 0, 0, None)])
        icfact = gtk.IconFactory()
        icfact.add_default()
        icfact.add('choose_dir', self.get_style().lookup_icon_set(gtk.STOCK_DIRECTORY))
        fc_button = gtk.Button(stock='choose_dir')
        fc_button.connect('clicked', self.chooseDirectory, self.fc_entry)

        #fc_button.set_label('Choose...')
        tf_hb2.pack_start(fc_button)
        vb.pack_start(tf_hb1)
        vb.pack_start(tf_hb2)

        self.fc_checkbox = gtk.CheckButton('use relative folder path')
        if os.path.isabs(self.project.getTraceFileDir()):
            self.fc_checkbox.set_active(False)
        else:
            self.fc_checkbox.set_active(True)
        self.fc_checkbox.connect('toggled', self.useRelPathToggled)
        vb.pack_start(self.fc_checkbox)

        tracevb.pack_start(vb)

        # set up UI components for the forward/reverse trace file search strings
        vb = gtk.VBox()
        tfs_hb1 = gtk.HBox()
        tfs_hb1.pack_start(gtk.Label('Search strings for identifying forward and reverse trace files:'), False)

        # create a layout table for the labels and text entries
        table = gtk.Table(2, 2)

        self.tfs_fwd_entry = gtk.Entry()
        self.tfs_fwd_entry.set_width_chars(6)
        self.tfs_fwd_entry.set_text(self.project.getFwdTraceSearchStr())
        table.attach(gtk.Label('Forward: '), 0, 1, 0, 1, xoptions=0)
        table.attach(self.tfs_fwd_entry, 1, 2, 0, 1, xoptions=0)
        
        self.tfs_rev_entry = gtk.Entry()
        self.tfs_rev_entry.set_width_chars(6)
        self.tfs_rev_entry.set_text(self.project.getRevTraceSearchStr())
        table.attach(gtk.Label('Reverse: '), 0, 1, 1, 2, xoptions=0)
        table.attach(self.tfs_rev_entry, 1, 2, 1, 2, xoptions=0)

        vb.pack_start(tfs_hb1)
        vb.pack_start(table)

        tracevb.pack_start(vb)

        frame = gtk.Frame('Trace files settings')
        frame.add(tracevb)
        mainvb.pack_start(frame)

        # get the consensus sequence settings
        cssettings = self.project.getConsensSeqSettings()

        # set up UI components for choosing the phred score cutoff value
        vb = gtk.VBox(False, 20)
        vb.set_border_width(10)
        hb1 = gtk.HBox()
        hb1.pack_start(gtk.Label('Min. confidence score:  '), False)

        self.ph_adj = gtk.Adjustment(cssettings.getMinConfScore(), 0, 61, 1)
        spin = gtk.SpinButton(self.ph_adj)
        hb1.pack_start(spin, False, False)

        vb.pack_start(hb1)

        # set up UI components for sequence trimming settings
        vb_trim = gtk.VBox()
        self.autotrim_checkbox = gtk.CheckButton('automatically trim sequence ends')
        self.autotrim_checkbox.connect('toggled', self.autoTrimToggled)
        vb_trim.pack_start(self.autotrim_checkbox)

        autotrim_winsize, autotrim_basecnt = cssettings.getAutoTrimParams()

        hb2 = gtk.HBox()
        hb2.pack_start(gtk.Label('Trim until at least '), False)
        self.autotrim_basecnt_adj = gtk.Adjustment(autotrim_basecnt, 1, autotrim_winsize, 1)
        self.autotrim_basecnt_spin = gtk.SpinButton(self.autotrim_basecnt_adj)
        hb2.pack_start(self.autotrim_basecnt_spin, False, False)

        hb2.pack_start(gtk.Label(' out of '), False)
        self.autotrim_winsize_adj = gtk.Adjustment(autotrim_winsize, 1, 20, 1)
        self.autotrim_winsize_spin = gtk.SpinButton(self.autotrim_winsize_adj)
        hb2.pack_start(self.autotrim_winsize_spin, False, False)
        self.autotrim_winsize_adj.connect('value_changed', self.autoTrimWinSizeChanged)

        hb2.pack_start(gtk.Label(' bases are correctly called.'), False)
        vb_trim.pack_start(hb2)

        self.trimgaps_checkbox = gtk.CheckButton('trim alignment end gaps')
        self.trimgaps_checkbox.set_active(cssettings.getTrimEndGaps())
        vb_trim.pack_start(self.trimgaps_checkbox)

        self.autotrim_checkbox.set_active(cssettings.getDoAutoTrim())
        self.autotrim_checkbox.toggled()

        vb.pack_start(vb_trim)
        frame = gtk.Frame('Sequence settings')
        frame.add(vb)

        mainvb.pack_start(frame)

        self.vbox.pack_start(mainvb)

        self.vbox.show_all()

    def getFwdTraceSearchStr(self):
        return self.tfs_fwd_entry.get_text().strip()

    def getRevTraceSearchStr(self):
        return self.tfs_rev_entry.get_text().strip()

    def getMinConfScore(self):
        return int(self.ph_adj.get_value())

    def getTraceFileFolder(self):
        return self.fc_entry.get_text()

    def checkSettingsValues(self):
        settings_valid = True

        tffpath = os.path.abspath(
                os.path.join(self.project.getProjectDir(), self.getTraceFileFolder())
                )
        if not(os.path.isdir(tffpath)):
            self.showMessage('The trace file location "' + self.getTraceFileFolder() +
                    '" is not valid.  Verify that the specified directory exists and that you have permission to read it.')
            settings_valid = False
        elif self.getFwdTraceSearchStr() == '':
            self.showMessage('You must specify a search string for identifying forward sequencing trace files.')
            settings_valid = False
        elif self.getRevTraceSearchStr() == '':
            self.showMessage('You must specify a search string for identifying reverse sequencing trace files.')
            settings_valid = False

        return settings_valid

    def updateProjectSettings(self):
        # trace file settings
        self.project.setTraceFileDir(self.getTraceFileFolder())
        self.project.setFwdTraceSearchStr(self.getFwdTraceSearchStr())
        self.project.setRevTraceSearchStr(self.getRevTraceSearchStr())

        cssettings = self.project.getConsensSeqSettings()

        # set all consensus sequence settings at once to only trigger a single
        # update event for any listeners
        cssettings.setAll(
                self.getMinConfScore(),
                self.autotrim_checkbox.get_active(),
                (int(self.autotrim_winsize_adj.get_value()), int(self.autotrim_basecnt_adj.get_value())),
                self.trimgaps_checkbox.get_active()
                )

    def chooseDirectory(self, widget, entry):
        # create a file chooser dialog to get a directory name from the user
        fc = gtk.FileChooserDialog('Choose Trace Files Location', None, gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER,
                (gtk.STOCK_OK, gtk.RESPONSE_OK, gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))
        fc.set_current_folder(self.project.getAbsTraceFileDir())
        response = fc.run()
        fname = fc.get_filename()
        fc.destroy()
        if response != gtk.RESPONSE_OK:
            return

        if self.fc_checkbox.get_active():
            fname = os.path.relpath(fname, self.project.getProjectDir())
        entry.set_text(fname)

    def useRelPathToggled(self, button):
        # toggle the display of the currently-selected trace file folder, making sure that paths
        # are always relative to the location of the project file
        if self.fc_checkbox.get_active():
            self.fc_entry.set_text(os.path.relpath(self.fc_entry.get_text(), self.project.getProjectDir()))
        else:
            self.fc_entry.set_text(os.path.abspath(
                os.path.join(self.project.getProjectDir(), self.fc_entry.get_text())
                ))

    def autoTrimToggled(self, button):
        if self.autotrim_checkbox.get_active():
            self.autotrim_basecnt_spin.set_sensitive(True)
            self.autotrim_winsize_spin.set_sensitive(True)
            self.trimgaps_checkbox.set_sensitive(True)
        else:
            self.autotrim_basecnt_spin.set_sensitive(False)
            self.autotrim_winsize_spin.set_sensitive(False)
            self.trimgaps_checkbox.set_sensitive(False)

    def autoTrimWinSizeChanged(self, adj):
        winsize = self.autotrim_winsize_adj.get_value()

        if self.autotrim_basecnt_adj.get_value() > winsize:
            self.autotrim_basecnt_adj.set_value(winsize)

        self.autotrim_basecnt_adj.set_upper(winsize)


class TraceWindowManager:
    def __init__(self):
        self.tracewindows = {}
        self.last_id = 0

    def newTraceWindow(self, mod_cons_seq, project_rowid=-1):
        newwin = TraceWindow(mod_cons_seq, is_mainwindow=False, id_num=self.last_id)
        newwin.connect('destroy', self.traceWindowDestroyed)

        self.tracewindows[self.last_id] = (newwin, project_rowid)
        self.last_id += 1

        return newwin

    def findByItemId(self, rowid):
        for tw_id in self.tracewindows.keys():
            if self.tracewindows[tw_id][1] == rowid:
                return self.tracewindows[tw_id][0]

        return None

    def getItemId(self, tracewindow):
        tw_id = tracewindow.getIdNum()

        return self.tracewindows[tw_id][1]

    def closeByItemId(self, rowid):
        tw = self.findByItemId(rowid)

        if tw != None:
            tw.destroy()

    def closeProjectTraceWindows(self):
        # close all project-related trace windows that are still open
        idnums = self.tracewindows.keys()
        for idnum in idnums:
            if self.tracewindows[idnum][1] != -1:
                self.tracewindows[idnum][0].destroy()

    def closeAllTraceWindows(self):
        # close any trace windows that are still open
        idnums = self.tracewindows.keys()
        for idnum in idnums:
            self.tracewindows[idnum][0].destroy()

    def traceWindowDestroyed(self, window):
        idnum = window.getIdNum()
        #print idnum
        del self.tracewindows[idnum]


# Another way to detect if the forward/reverse arrow in the treeview is clicked.  I'm not sure which
# approach is better, or "more correct".  For now, the method of testing the x/y coords of clicks on
# the treeview itself is used, because it was simpler to integrate with already-existing code.
#class CellRendererPixbufClickable(gtk.CellRendererPixbuf):
#    def __init__(self):
#        gtk.CellRendererPixbuf.__init__(self)
#        self.set_property('mode', gtk.CELL_RENDERER_MODE_ACTIVATABLE)
#
#    def do_activate(self, event, widget, path, background_area, cell_area, flags):
#        if (event.x > cell_area.x) and (event.x < (cell_area.x + cell_area.width)):
#            print 'clicked'
#import gobject
#gobject.type_register(CellRendererPixbufClickable)


class ProjectViewer(gtk.ScrolledWindow, Observable):
    # set location of the supporting image files
    images_folder = os.path.dirname(__file__) + '/images'

    def __init__(self, project):
        gtk.ScrolledWindow.__init__(self)

        self.project = project

        # initialize the TreeView
        self.treeview = gtk.TreeView(self.project.getTreeStore())
        self.treeview.set_enable_tree_lines(True)
        self.treeview.set_grid_lines(gtk.TREE_VIEW_GRID_LINES_NONE)
        self.treeview.set_rules_hint(True)

        # first column: for item name and forward/reverse icons
        self.col1 = gtk.TreeViewColumn('Trace Files')
        self.col1.set_expand(True)
        self.col1.set_resizable(True)
        #self.col1.set_clickable(True)
        #self.col1.connect('clicked', self.colHeadClicked, stproject.FILE_NAME)
        self.col1.set_sort_column_id(stproject.FILE_NAME)

        # set up cell renderer for forward/reverse icons
        self.isfwdrev_both = gtk.gdk.pixbuf_new_from_file(self.images_folder + '/isfwdrev_both.png')
        self.isfwdrev_fwd = gtk.gdk.pixbuf_new_from_file(self.images_folder + '/isfwdrev_fwd.png')
        self.isfwdrev_rev = gtk.gdk.pixbuf_new_from_file(self.images_folder + '/isfwdrev_rev.png')
        self.isrev_ren = gtk.CellRendererPixbuf()
        self.col1.pack_start(self.isrev_ren, False)
        self.col1.set_cell_data_func(self.isrev_ren, self.showFrwdRev)

        # set up cell renderer for item name
        nameren = gtk.CellRendererText()
        nameren.connect('edited', self.nameEdited)
        self.col1.pack_start(nameren)
        self.col1.add_attribute(nameren, 'text', stproject.FILE_NAME)
        self.col1.set_cell_data_func(nameren, self.isRowFile)
        self.treeview.append_column(self.col1)

        # second column: for description/notes
        notesren = gtk.CellRendererText()
        notesren.connect('edited', self.notesEdited)
        notesren.set_property('editable', True)
        self.col2 = gtk.TreeViewColumn('Notes/Description', notesren, text=stproject.NOTES)
        self.col2.set_expand(True)
        self.col2.set_resizable(True)
        self.col2.set_sort_column_id(stproject.NOTES)
        self.treeview.append_column(self.col2)

        # third column: for has sequence icons
        hasseqren = gtk.CellRendererPixbuf()
        self.hasseq_no = gtk.gdk.pixbuf_new_from_file(self.images_folder + '/hasseq_no.png')
        self.hasseq_yes = gtk.gdk.pixbuf_new_from_file(self.images_folder + '/hasseq_yes.png')
        col3 = gtk.TreeViewColumn('Seq. Saved', hasseqren)
        col3.set_cell_data_func(hasseqren, self.renderHasSeq)
        col3.set_sort_column_id(stproject.HAS_CONS)
        self.treeview.append_column(col3)

        # fourth column: for use sequence checkbox
        useseqren = gtk.CellRendererToggle()
        useseqren.set_property('activatable', True)
        useseqren.connect('toggled', self.useseqToggled)
        col4 = gtk.TreeViewColumn('Use Seq.', useseqren, active=stproject.USE_CONS)
        col4.set_cell_data_func(useseqren, self.renderUseSeq)
        col4.set_sort_column_id(stproject.USE_CONS)
        self.treeview.append_column(col4)

        self.treeview.get_selection().set_mode(gtk.SELECTION_MULTIPLE)

        # add the treeview to the scrolled window
        self.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.add(self.treeview)

        # connect to treeview signals
        self.treeview.connect('button_press_event', self.mouseClick)
        self.treeview.get_selection().connect('changed', self.selectChanged)

        # initialize observable events
        self.defineObservableEvents(['right_clicked', 'isfwdrew_clicked', 'item_renamed', 'notes_edited',
                'selection_changed', 'useseq_changed'])

    def useseqToggled(self, cell, path):
        item = self.project.getItemByPath(path)
        self.notifyObservers('useseq_changed', (item,))

    def showFrwdRev(self, col, renderer, model, node):
        item = self.project.getItemByTsiter(node)

        if item.isFile():
            renderer.set_property('visible', True)
            if item.getIsReverse():
                renderer.set_property('pixbuf', self.isfwdrev_rev)
            else:
                renderer.set_property('pixbuf', self.isfwdrev_fwd)
        else:
            renderer.set_property('pixbuf', self.isfwdrev_both)
            #renderer.set_property('visible', False)

    def isRowFile(self, col, renderer, model, node):
        item = self.project.getItemByTsiter(node)

        if item.isFile():
            renderer.set_property('editable', False)
        else:
            renderer.set_property('editable', True)

    def renderHasSeq(self, col, renderer, model, node):
        item = self.project.getItemByTsiter(node)
        self.setSeqRendererVisible(renderer, item)

        if item.hasSequence():
            renderer.set_property('pixbuf', self.hasseq_yes)
        else:
            renderer.set_property('pixbuf', self.hasseq_no)

    def renderUseSeq(self, col, renderer, model, node):
        item = self.project.getItemByTsiter(node)
        self.setSeqRendererVisible(renderer, item)

    def setSeqRendererVisible(self, renderer, item):
        if item.hasParent():
            renderer.set_property('visible', False)
        else:
            renderer.set_property('visible', True)

    def expandAll(self):
        self.treeview.expand_all()

    def collapseAll(self):
        self.treeview.collapse_all()

    def requestEditSelectedRowName(self):
        model, paths = self.treeview.get_selection().get_selected_rows()
        if len(paths) != 1:
            return

        self.treeview.set_cursor(paths[0], self.col1, True)

    def requestEditSelectedRowNotes(self):
        model, paths = self.treeview.get_selection().get_selected_rows()
        if len(paths) != 1:
            return

        self.treeview.set_cursor(paths[0], self.col2, True)

    def nameEdited(self, cell, path, new_text):
        item = self.project.getItemByPath(path)

        self.notifyObservers('item_renamed', (item, new_text))

    def notesEdited(self, cell, path, new_text):
        item = self.project.getItemByPath(path)

        self.notifyObservers('notes_edited', (item, new_text))

    def mouseClick(self, viewer, event):
        x = int(event.x)
        y = int(event.y)

        # make sure an actual row was clicked
        pathinfo = self.treeview.get_path_at_pos(x, y)
        if pathinfo == None:
            return

        path = pathinfo[0]
        item = self.project.getItemByPath(path)

        # left click
        if event.button == 1:
            # see if the click was on the forward/reverse arrow cell renderer
            if pathinfo[1] == self.col1:
                # cell_area contains the coordinates (relative to the treeview widget) of the actual content of the cell
                # (including both cell renderers), ignoring any space in the cell outside of the renderers (such as area
                # for the tree expanders).  renderer_width is the width the specified renderer occupies inside of the cell_area.
                cell_area = self.treeview.get_cell_area(path, self.col1)
                renderer_width = pathinfo[1].cell_get_position(self.isrev_ren)[1]
                if (x > cell_area.x) and (x < (cell_area.x + renderer_width)):
                    self.notifyObservers('isfwdrew_clicked', (item, event))

        # right click
        elif event.button == 3:
            self.treeview.set_cursor(path)
            self.notifyObservers('right_clicked', (item, event))

    def getSelection(self):
        model, paths = self.treeview.get_selection().get_selected_rows()

        return self.project.getItemsByPaths(paths)

    def selectChanged(self, selection):
        sel_cnt = selection.count_selected_rows()

        self.notifyObservers('selection_changed', (sel_cnt,))


class MainWindow(gtk.Window, CommonDialogs):
    def __init__(self):
        gtk.Window.__init__(self, gtk.WINDOW_TOPLEVEL)

        self.project = SequenceTraceProject()
        self.project_open = False

        self.tw_manager = TraceWindowManager()

        self.fextension = '.str'
        self.wintitle = 'SeqTrace'
        self.project.registerObserver('save_state_change', self.projSaveStateChanged)
        self.project.registerObserver('project_filename_change', self.projFilenameChanged)
        self.project.getConsensSeqSettings().registerObserver('settings_change', self.consSeqSettingsChanged)

        # initialize the window GUI elements
        self.connect('delete-event', self.deleteEvent)
        self.vbox = gtk.VBox(False, 0)
        self.add(self.vbox)

        # create the menus and toolbar
        menuxml = '''<menubar name="menubar">
        <menu action="File">
            <menuitem action="Open" />
            <menuitem action="New" />
            <menuitem action="Close" />
            <separator />
            <menuitem action="Save" />
            <menuitem action="Save_As" />
            <separator />
            <menuitem action="Revert_To_Saved" />
            <separator />
            <menuitem action="Open_Trace" />
            <separator />
            <menuitem action="Project_Settings" />
            <separator />
            <menuitem action="Exit" />
        </menu>
        <menu action="Trace_Files">
            <menuitem action="View_File" />
            <separator />
            <menuitem action="Add_File" />
            <menuitem action="Remove_File" />
            <separator />
            <menuitem action="Find_FwdRev" />
            <separator />
            <menuitem action="Associate_Files" />
            <menuitem action="Dissociate_Files" />
            <menu action="Auto_Associate">
                <menuitem action="Auto_Associate_All" />
                <menuitem action="Auto_Associate_Selected" />
            </menu>
            <separator />
            <menuitem action="View_Expand_All" />
            <menuitem action="View_Collapse_All" />
        </menu>
        <menu action="Sequences">
            <menu action="Export">
                <menuitem action="Export_Selected" />
                <menuitem action="Export_All" />
            </menu>
            <separator />
            <menu action="Generate">
                <menuitem action="Generate_Selected" />
                <menuitem action="Generate_All" />
            </menu>
            <separator />
            <menu action="Delete">
                <menuitem action="Delete_Sel_Seqs" />
                <menuitem action="Delete_All_Seqs" />
            </menu>
        </menu>
        <menu action="Help">
            <menuitem action="About" />
        </menu></menubar>
        <popup name="projview_popup">
            <menuitem action="Popup_Rename_Row" />
            <menuitem action="Popup_Edit_Notes" />
            <separator />
            <menuitem action="Dissociate_Files" />
            <separator />
            <menuitem action="Popup_Remove_File" />
            <separator />
            <menuitem action="Popup_Delete_Sel_Seqs" />
        </popup>
        <toolbar name="toolbar">
            <toolitem action="Open" />
            <toolitem action="New" />
            <toolitem action="Save" />
            <separator />
            <toolitem action="Project_Settings" />
            <separator />
            <toolitem action="View_File" />
            <toolitem action="Add_File" />
            <separator />
            <toolitem action="Export_All" />
        </toolbar>'''
        # these actions are always enabled
        self.main_ag = gtk.ActionGroup('main_actions')
        self.main_ag.add_actions([
            ('File', None, '_File'),
            ('Open', gtk.STOCK_OPEN, '_Open project...', None, 'Open a project file', self.openProjectAction),
            ('New', gtk.STOCK_NEW, '_New project...', None, 'Create a new project', self.newProject),
            ('Open_Trace', None, 'Open _trace file...', None, 'Open a trace file without adding it to the current project',
                self.actionOpenTraceFile),
            ('Exit', gtk.STOCK_QUIT, 'E_xit', None, 'Exit the program', self.deleteEvent),
            ('Sequences', None, '_Sequences'),
            ('Trace_Files', None, '_Traces'),
            ('Help', None, '_Help'),
            ('About', gtk.STOCK_ABOUT, '_About...', None, 'Display information about this program', self.showAbout)])

        # these actions are generally only enabled when a project is open
        self.main_proj_ag = gtk.ActionGroup('project_actions')
        self.main_proj_ag.add_actions([
            ('Close', gtk.STOCK_CLOSE, '_Close project', None, 'Close the current project', self.closeProject),
            ('Save', gtk.STOCK_SAVE, '_Save project', None, 'Save the current project', self.saveProject),
            ('Save_As', gtk.STOCK_SAVE_AS, '_Save project as...', None, 'Save as a new project', self.saveProjectAs),
            ('Revert_To_Saved', gtk.STOCK_REVERT_TO_SAVED, '_Reload project', None,
                'Reload the project from the last saved version', self.revertToSaved),
            ('Export', gtk.STOCK_CONVERT, '_Export sequences', None, 'Export sequences to a file'),
            ('Export_All', gtk.STOCK_CONVERT, 'From _all trace files...', None, 'Export all in-use sequences', self.exportAll),
            ('Delete', None, '_Delete saved sequences', None),
            ('Delete_All_Seqs', None, 'For _all trace files', None, 'Deleted all saved sequences', self.deleteAllSeqs),
            ('Project_Settings', gtk.STOCK_PREFERENCES, '_Project Settings...', None,
                'View and change the settings for the current project', self.projectSettings),
            ('Add_File', gtk.STOCK_ADD, '_Add trace file(s)...', None, 'Add trace files to the project', self.projectAddFiles),
            ('Auto_Associate', None, '_Auto-group trace files'),
            ('Auto_Associate_All', None, 'Auto-group all trace files', None,
                'Automatically recognize and group forward/reverse trace files', self.projectAssociateAllFiles),
            ('View_Expand_All', None, 'Expand all groups', None,
                'Expand the view of all forward/reverse groups', lambda widget: self.projview.expandAll()),
            ('View_Collapse_All', None, 'Collapse all groups', None,
                'Collapse the view of all forward/reverse groups', lambda widget: self.projview.collapseAll()),
            ('Generate', None, '_Generate finished sequences'),
            ('Generate_All', None, 'For _all trace files', None, 'Calculated finished sequences for all trace files',
                self.generateAllSequences)
            ])

        # these actions are only enabled when one or more trace files in the project are selected
        self.sel_proj_ag = gtk.ActionGroup('project_actions_selected')
        self.sel_proj_ag.add_actions([
            ('Export_Selected', None, 'From _selected trace files...', None, 'Export all selected in-use sequences',
                self.exportSelected),
            ('Delete_Sel_Seqs', None, 'For _selected trace files', None, 'Deleted all saved sequences in selection',
                self.deleteSelSeqs),
            ('View_File', gtk.STOCK_FIND, '_View selected trace file(s)...', None, 'View the selected trace file(s)',
                self.projectViewFiles),
            ('Remove_File', gtk.STOCK_DELETE, '_Remove selected trace file(s)', None,
                'Remove the selected trace file(s) from the project', self.projectRemoveFiles),
            ('Find_FwdRev', None, '_Find and mark forward/reverse', None,
                'Identify the selected trace files as forward or reverse reads, if possible', self.findFwdRev),
            ('Associate_Files', None, '_Group selected forward/reverse files', None,
                'Associate the selected trace files as complementary forward/reverse traces', self.projectAssociateFiles),
            ('Dissociate_Files', None, '_Ungroup forward/reverse files', None,
                'Remove the selected forward/reverse trace file associations', self.projectDissociateFiles),
            ('Auto_Associate_Selected', None, 'Auto-group selected trace files', None,
                'Automatically recognize and group forward/reverse trace files', self.projectAssociateSelectedFiles),
            ('Generate_Selected', None, 'For _selected trace files', None, 'Calculated finished sequences for selected trace files',
                self.generateSelectedSequences)
            ])

        # these actions are specific to the project viewer context popup menu
        self.popup_proj_ag = gtk.ActionGroup('project_actions_popup')
        self.popup_proj_ag.add_actions([
            ('Popup_Remove_File', gtk.STOCK_REMOVE, '_Remove trace file', None, 'Remove the selected trace file from the project',
                self.projectRemoveFiles),
            ('Popup_Delete_Sel_Seqs', None, 'Delete saved sequence', None, 'Deleted the saved consensus sequence', self.deleteSelSeqs),
            ('Popup_Rename_Row', None, 'Rename', None, 'Rename the forward/reverse group', self.popupRenameRow),
            ('Popup_Edit_Notes', gtk.STOCK_EDIT, 'Edit notes', None, 'Edit the notes/description for this item', self.popupEditNotes)
            ])

        # build the UIManager
        self.uim = gtk.UIManager()
        self.add_accel_group(self.uim.get_accel_group())
        self.uim.insert_action_group(self.main_ag)
        self.uim.insert_action_group(self.main_proj_ag)
        self.uim.insert_action_group(self.sel_proj_ag)
        self.uim.insert_action_group(self.popup_proj_ag)
        self.uim.add_ui_from_string(menuxml)

        # add the menu bar to the window
        self.vbox.pack_start(self.uim.get_widget('/menubar'), expand=False, fill=False)

        # set the toolbar appearance and add it to the window
        self.uim.get_widget('/toolbar').set_icon_size(gtk.ICON_SIZE_LARGE_TOOLBAR)
        self.uim.get_widget('/toolbar').set_style(gtk.TOOLBAR_ICONS)
        self.vbox.pack_start(self.uim.get_widget('/toolbar'), expand=False, fill=False)

        # disable the project-specific menus/toolbar buttons by default
        self.main_proj_ag.set_sensitive(False)
        self.sel_proj_ag.set_sensitive(False)

        # initialize the project viewer
        self.projview = ProjectViewer(self.project)
        self.projview.registerObserver('selection_changed', self.projViewSelectChanged)
        self.projview.registerObserver('right_clicked', self.projViewRightClicked)
        self.projview.registerObserver('isfwdrew_clicked', self.projViewIsfwdrevClicked)
        self.projview.registerObserver('item_renamed', self.projViewNameEdited)
        self.projview.registerObserver('notes_edited', self.projViewNotesEdited)
        self.projview.registerObserver('useseq_changed', self.projViewUseseqChanged)
        self.view_has_selection = False
        self.vbox.pack_start(self.projview)

        # add a status bar for the project
        self.statusbar = ProjectStatusBar(self.project)
        self.vbox.pack_start(self.statusbar, False)

        self.vbox.show_all()
        self.vbox.show()
        self.set_title(self.wintitle)

        self.setDefaultGeometry()

        # Set the initial window position to the top left corner of the desktop to allow easier use
        # with open trace windows.
        # There is a bit of platform-specific code here.  On Windows, move() only seems to work after
        # show() has already been called.  On GNU/Linux, calling move() after calling show() can cause
        # the window to interfere with the desktop panel (in XFCE, at least), so it appears to work best
        # to call move() prior to calling show().
        if not(sys.platform.startswith('win')):
            self.move(0, 0)
            self.show()
        else:
            self.show()
            self.move(0, 0)

        self.set_focus(None)

    def setDefaultGeometry(self):
        screen = self.get_screen()

        # calculate the default height based on the screen size
        new_height = (screen.get_height() * 5) / 6
        new_width = 600

        if new_width > screen.get_width():
            new_width = screen.get_width()

        #self.resize(580, 520)
        self.set_default_size(new_width, new_height)

        #self.set_position(gtk.WIN_POS_CENTER)

    def projSaveStateChanged(self, save_state):
        if save_state:
            self.main_proj_ag.get_action('Save').set_sensitive(False)
        else:
            self.main_proj_ag.get_action('Save').set_sensitive(True)

    def projFilenameChanged(self, fname):
        self.set_title(os.path.basename(fname) + ' - ' + self.wintitle)

    def consSeqSettingsChanged(self):
        # if the project isn't empty, ask the user what to do with existing sequences
        if not(self.project.isProjectEmpty()):
            diag = gtk.MessageDialog(None, 0, gtk.MESSAGE_QUESTION, gtk.BUTTONS_OK, 'The settings for calculating consensus sequences have changed.  You might not want to use any previously-saved consensus sequences.')
            rb1 = gtk.RadioButton(None, 'Mark all saved sequences as unused.')
            rb1.set_active(True)
            rb2 = gtk.RadioButton(rb1, 'Delete all saved sequences.')
            rb3 = gtk.RadioButton(rb1, 'Do not make any changes to the project.')
            diag.vbox.pack_start(rb1, False, False)
            diag.vbox.pack_start(rb2, False, False)
            diag.vbox.pack_start(rb3, False, False)

            diag.show_all()
            diag.run()

            if rb1.get_active():
                for item in self.project:
                    item.setUseSequence(False)
                    for child in item.getChildren():
                        child.setUseSequence(False)
            elif rb2.get_active():
                for item in self.project:
                    item.deleteConsensusSequence()
                    for child in item.getChildren():
                        child.deleteConsensusSequence()

            diag.destroy()

    def projectSettings(self, widget):
        sdiag = ProjectSettings(self.project)
        response = gtk.RESPONSE_OK
        settings_valid = False

        while (response == gtk.RESPONSE_OK) and not(settings_valid):
            response = sdiag.run()
            if response != gtk.RESPONSE_OK:
                break

            settings_valid = sdiag.checkSettingsValues()

        sdiag.hide()

        if response == gtk.RESPONSE_OK:
            sdiag.updateProjectSettings()

        sdiag.destroy()

    def popupRenameRow(self, widget):
        self.projview.requestEditSelectedRowName()

    def popupEditNotes(self, widget):
        self.projview.requestEditSelectedRowNotes()

    def projViewNameEdited(self, item, new_text):
        new_text = new_text.strip()
        if new_text == '':
            return

        item.setName(new_text)

    def projViewNotesEdited(self, item, new_text):
        new_text = new_text.strip()
        item.setNotes(new_text)

    def projViewRightClicked(self, item, event):
        # enable/disable popup menu items depending upon the selected row
        if item.isFile():
            self.uim.get_widget('/projview_popup/Popup_Remove_File').set_visible(True)
            self.uim.get_widget('/projview_popup/Dissociate_Files').set_visible(False)
            self.uim.get_widget('/projview_popup/Popup_Rename_Row').set_visible(False)
        else:
            self.uim.get_widget('/projview_popup/Popup_Remove_File').set_visible(False)
            self.uim.get_widget('/projview_popup/Dissociate_Files').set_visible(True)
            self.uim.get_widget('/projview_popup/Popup_Rename_Row').set_visible(True)

        if item.hasSequence():
            self.uim.get_widget('/projview_popup/Popup_Delete_Sel_Seqs').set_visible(True)
        else:
            self.uim.get_widget('/projview_popup/Popup_Delete_Sel_Seqs').set_visible(False)
            
        self.uim.get_widget('/projview_popup').popup(None, None, None, event.button, event.time)

    def projViewIsfwdrevClicked(self, item, event):
        if item.isFile():
            item.toggleIsReverse()

    def projViewUseseqChanged(self, item):
        if item.hasSequence():
            item.toggleUseSequence()
        else:
            self.showMessage('No consensus sequence has been saved for this trace file.  You must first view the sequencing trace, then save the consensus sequence from the trace.')

    def projViewSelectChanged(self, sel_cnt):
        if sel_cnt == 0:
            # disable the selection-dependent UI elements
            self.sel_proj_ag.set_sensitive(False)

            self.view_has_selection = False
        else:
            # enable the selection-dependent UI elements, if needed
            if not(self.view_has_selection):
                self.sel_proj_ag.set_sensitive(True)
                self.view_has_selection = True

            # handle a few UI elements with more specific selection requirements
            assoc_files = self.sel_proj_ag.get_action('Associate_Files')
            if (sel_cnt == 2) and not(assoc_files.get_sensitive()):
                assoc_files.set_sensitive(True)
            elif (sel_cnt != 2) and assoc_files.get_sensitive():
                assoc_files.set_sensitive(False)

            auto_assoc = self.sel_proj_ag.get_action('Auto_Associate_Selected')
            if (sel_cnt >= 2) and not(auto_assoc.get_sensitive()):
                auto_assoc.set_sensitive(True)
            elif (sel_cnt < 2) and auto_assoc.get_sensitive():
                auto_assoc.set_sensitive(False)

    def getFileExtension(self):
        return self.fextension

    def openProjectAction(self, widget):
        # create a file chooser dialog to get a file name from the user
        fc = gtk.FileChooserDialog('Open Project', None, gtk.FILE_CHOOSER_ACTION_OPEN,
                (gtk.STOCK_OPEN, gtk.RESPONSE_OK, gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))
        fc.set_current_folder(os.getcwd())

        f1 = gtk.FileFilter()
        f1.set_name('project files')
        f1.add_pattern('*' + self.fextension)
        f2 = gtk.FileFilter()
        f2.set_name('all files')
        f2.add_pattern('*')
        fc.add_filter(f1)
        fc.add_filter(f2)
        response = fc.run()
        fname = fc.get_filename()
        fc.destroy()
        if response != gtk.RESPONSE_OK:
            return

        # if a project is already open, try to close it first
        if self.project_open:
            if not(self.closeProject(None)):
                return

        self.openProject(fname)

    def openProject(self, fname):
        try:
            self.project.loadProjectFile(fname)
        except IOError:
            self.showMessage('The project file "' + fname + '" could not be opened.  Verify that the file exists and that you have permission to read it.')
            return
        except stproject.FileDataError:
            self.showMessage('The project file "' + fname + '" is corrupt or in an unrecognized format.')
            return
        except stproject.FileFormatVersionError:
            self.showMessage('The file format version of "' + fname + '" is not supported by this version of the software.')
            return

        self.main_proj_ag.set_sensitive(True)

        self.project_file = fname
        self.set_title(os.path.basename(fname) + ' - ' + self.wintitle)
        self.project_open = True

    def actionOpenTraceFile(self, widget):
        # create a file chooser dialog to get a file name from the user
        fc = gtk.FileChooserDialog('Open Trace File', None, gtk.FILE_CHOOSER_ACTION_OPEN,
                (gtk.STOCK_OPEN, gtk.RESPONSE_OK, gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))
        fc.set_current_folder(self.project.getTraceFileDir())
        f1 = gtk.FileFilter()
        f1.set_name('trace files (*.ab1;*.scf;*.ztr)')
        f1.add_pattern('*.ztr')
        f1.add_pattern('*.ab1')
        f1.add_pattern('*.scf')
        f2 = gtk.FileFilter()
        f2.set_name('all files (*)')
        f2.add_pattern('*')
        fc.add_filter(f1)
        fc.add_filter(f2)
        response = fc.run()
        fname = fc.get_filename()
        fc.destroy()
        if response != gtk.RESPONSE_OK:
            return

        self.openTraceFile(fname)

    def openTraceFile(self, filename):
        seqt = self.openTraceFileInternal(filename)
        if seqt == None:
            return

        settings = ConsensSeqSettings()

        # if a project is open, use the consensus settings from the project
        if self.project_open:
            settings.copyFrom(self.project.getConsensSeqSettings())

        csb = ModifiableConsensSeqBuilder((seqt,), settings)

        # create a new trace window
        self.tw_manager.newTraceWindow(csb)

    def newProject(self, widget):
        # if a project is already open, try to close it first
        if self.project_open:
            if not(self.closeProject(None)):
                return

        self.project.clearProject()

        self.main_proj_ag.set_sensitive(True)

        self.project_open = True
        self.set_title('new project - ' + self.wintitle)

        # prompt the user to customize the settings for the new project
        self.projectSettings(None)

    def closeProject(self, widget, show_confirm=True):
        if not(self.project.getSaveState()) and show_confirm:
            # see if the user wants to save the project before closing it
            msg = 'Do you want to save the current project before closing it?  All unsaved changes will be lost.'
            response = self.showYesNoCancelDialog(msg)
            if response == gtk.RESPONSE_YES:
                saved = self.saveProject(None)
                if not(saved):
                    return False
            elif response != gtk.RESPONSE_NO:
                return False

        # close any project trace windows that are still open
        self.tw_manager.closeProjectTraceWindows()

        # clear all project data
        self.project.clearProject()

        self.main_proj_ag.set_sensitive(False)
        self.sel_proj_ag.set_sensitive(False)

        self.project_open = False
        self.statusbar.showNoProject()
        self.set_title(self.wintitle)

        return True

    def revertToSaved(self, widget):
        if not(self.project.getSaveState()):
            # make sure this is what the user actually wants to do
            response = self.showYesNoDialog('Are you sure you want to reload the current project?  All unsaved changes will be lost.')
            if response != gtk.RESPONSE_YES:
                return

        fname = self.project_file

        res = self.closeProject(None, False)
        if not(res):
            return

        self.openProject(fname)

    def saveProject(self, widget):
        # if the current project does not have a file name, prompt for one
        if self.project.getProjectFileName() == '':
            # create a file chooser dialog to get a file name from the user
            fc = gtk.FileChooserDialog('Save Project', None, gtk.FILE_CHOOSER_ACTION_SAVE,
                    (gtk.STOCK_SAVE, gtk.RESPONSE_OK, gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))
            fc.set_current_folder(os.getcwd())
            fc.set_do_overwrite_confirmation(True)

            f1 = gtk.FileFilter()
            f1.set_name('project files (*' + self.fextension + ')')
            f1.add_pattern('*' + self.fextension)
            f2 = gtk.FileFilter()
            f2.set_name('all files (*)')
            f2.add_pattern('*')
            fc.add_filter(f1)
            fc.add_filter(f2)
            response = fc.run()
            fname = fc.get_filename()
            fc.destroy()
            if response != gtk.RESPONSE_OK:
                return False

            # make sure the file name has the correct extension
            if not(fname.endswith(self.fextension)):
                fname += self.fextension

            self.project.setProjectFileName(fname)

        try:
            self.project.saveProjectFile()
            return True
        except IOError:
            self.showMessage('Unable to save the project file "' + self.project.getProjectFileName()
                    + '".  Verify that you have permission to write to the specified file.')
            return False

    def saveProjectAs(self, widget):
        # create a file chooser dialog to get a file name from the user
        fc = gtk.FileChooserDialog('Save Project As', None, gtk.FILE_CHOOSER_ACTION_SAVE,
                (gtk.STOCK_SAVE, gtk.RESPONSE_OK, gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))
        fc.set_current_folder(os.getcwd())
        fc.set_do_overwrite_confirmation(True)

        f1 = gtk.FileFilter()
        f1.set_name('project files (*' + self.fextension + ')')
        f1.add_pattern('*' + self.fextension)
        f2 = gtk.FileFilter()
        f2.set_name('all files (*)')
        f2.add_pattern('*')
        fc.add_filter(f1)
        fc.add_filter(f2)
        response = fc.run()
        fname = fc.get_filename()
        fc.destroy()
        if response != gtk.RESPONSE_OK:
            return

        # make sure the file name has the correct extension
        if not(fname.endswith(self.fextension)):
            fname += self.fextension

        self.project.setProjectFileName(fname)

        try:
            self.project.saveProjectFile()
        except IOError:
            self.showMessage('Unable to save the project file "' + self.project.getProjectFileName()
                    + '".  Verify that you have permission to write to the specified file.')

    def exportAll(self, widget):
        # create a file chooser dialog to get a file name and format from the user
        fc = seqwriter.SeqWriterFileDialog(self, 'Export All Sequences')
        fc.setShowOptions(True)
        fc.set_current_folder(os.getcwd())

        response = fc.run()
        fname = fc.get_filename()
        fformat = fc.getFileFormat()
        include_fnames = fc.getIncludeFileNames()
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

        for item in self.project:
            if item.getUseSequence():
                desc = item.getNotes()
                if item.isFile():
                    seqfname = item.getName()
                else:
                    children = item.getChildren()
                    seqfname = children[0].getName() + ', ' + children[1].getName()

                if not(include_fnames):
                    seqfname = ''

                sw.addUnalignedSequence(item.getCompactConsSequence(), seqfname, desc)

        try:
            sw.write()
        except seqwriter.SequenceWriterError as err:
            self.showMessage('Error: ' + str(err))

    def exportSelected(self, widget):
        # create a file chooser dialog to get a file name and format from the user
        fc = seqwriter.SeqWriterFileDialog(self, 'Export Selected Sequences')
        fc.setShowOptions(True)
        fc.set_current_folder(os.getcwd())

        response = fc.run()
        fname = fc.get_filename()
        fformat = fc.getFileFormat()
        include_fnames = fc.getIncludeFileNames()
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

        items = self.projview.getSelection()

        for item in items:
            if item.hasParent():
                continue

            if item.getUseSequence():
                desc = item.getNotes()
                if item.isFile():
                    seqfname = item.getName()
                else:
                    children = item.getChildren()
                    seqfname = children[0].getName() + ', ' + children[1].getName()

                if not(include_fnames):
                    seqfname = ''

                sw.addUnalignedSequence(item.getCompactConsSequence(), seqfname, desc)

        try:
            sw.write()
        except seqwriter.SequenceWriterError as err:
            self.showMessage('Error: ' + str(err))

    def projectViewFiles(self, widget):
        items = self.projview.getSelection()

        # if there are a lot of items selected, make sure the user wants to proceed
        if len(items) > 4:
            response = self.showYesNoDialog('This will open ' + str(len(items)) + ' trace file windows.  Do you want to continue?')
            if response != gtk.RESPONSE_YES:
                return

        for item in items:
            idnum = item.getId()
            fullcons = item.getFullConsSequence()
            loaded_fullcons = False

            searchres = self.tw_manager.findByItemId(idnum)
            if searchres == None:
                seqtraces = self.getSeqTraces(item)
                if seqtraces == None:
                    continue

                csb = ModifiableConsensSeqBuilder(seqtraces, self.project.getConsensSeqSettings())

                # try to load the saved consensus sequence, if it exists
                if fullcons != '':
                    try:
                        csb.setConsensSequence(fullcons)
                        loaded_fullcons = True
                    except Exception:
                        self.showMessage('The saved consensus sequence cannot be used because its size is incorrect.  A new consensus sequence will be generated.')

                # create a new trace window and add event handlers
                newwin = self.tw_manager.newTraceWindow(csb, idnum)
                newwin.registerObserver('consensus_saved', self.traceWindowConsensusSaved)
                if loaded_fullcons:
                    # the saved consensus sequence was successfully loaded, so start with "Save" button disabled
                    newwin.setSaveEnabled(False)
            else:
                # show the existing trace window
                searchres.present()

    def getSeqTraces(self, projectitem):
        seqtraces = list()

        # load the trace files
        if projectitem.isFile():
            seqt = self.openTraceFileFromItem(projectitem)
            if seqt == None:
                return None
            seqtraces.append(seqt)
        else:
            children = projectitem.getChildren()
            for child in children:
                seqt = self.openTraceFileFromItem(child)
                if seqt == None:
                    return None
                if child.getIsReverse():
                    seqt.reverseComplement()
                seqtraces.append(seqt)

        return seqtraces

    def openTraceFileFromItem(self, projectitem):
        fname = projectitem.getName()
        fullpath = os.path.join(self.project.getAbsTraceFileDir(), fname)

        return self.openTraceFileInternal(fullpath)

    def openTraceFileInternal(self, filepath):
        # get the appropriate SequenceTrace object
        try:
            seqt = sequencetrace.SequenceTraceFactory.loadTraceFile(filepath)
        except IOError:
            self.showMessage('The sequence trace file "' + filepath + '" could not be opened.  Verify that the file exists and that you have permission to read it.')
            return None
        except sequencetrace.TraceFileError as err:
            self.showMessage('Error opening "' + filepath + '".\n\n' + str(err))
            return None

        return seqt

    def traceWindowConsensusSaved(self, tracewindow, compact_consens, full_consens):
        itemid = self.tw_manager.getItemId(tracewindow)
        item = self.project.getItemById(itemid)

        item.setUseSequence(True)
        item.setConsensusSequence(compact_consens, full_consens)

        tracewindow.setSaveEnabled(False)

    def projectAddFiles(self, widget):
        # create a file chooser dialog to get a file name (or names) from the user
        fc = gtk.FileChooserDialog('Add Files to Project', None, gtk.FILE_CHOOSER_ACTION_OPEN,
                (gtk.STOCK_ADD, gtk.RESPONSE_OK, gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))
        fc.set_local_only(True)
        fc.set_select_multiple(True)
        fc.set_current_folder(self.project.getAbsTraceFileDir())
        f1 = gtk.FileFilter()
        f1.set_name('trace files (*.ab1;*.scf;*.ztr)')
        f1.add_pattern('*.ztr')
        f1.add_pattern('*.ab1')
        f1.add_pattern('*.scf')
        f2 = gtk.FileFilter()
        f2.set_name('all files (*)')
        f2.add_pattern('*')
        fc.add_filter(f1)
        fc.add_filter(f2)
        response = fc.run()
        filenames = fc.get_filenames()
        fc.destroy()
        if response != gtk.RESPONSE_OK:
            return

        for filepath in filenames:
            # check if the file already exists in the project
            if self.project.isFileInProject(filepath):
                response = self.showYesNoDialog('The file "' + filepath
                        + '" has already been added to this project.  Do you want to add it anyway?')
                if response != gtk.RESPONSE_YES:
                    continue

            self.project.addFiles((filepath,))

    def projectRemoveFiles(self, widget):
        # confirm this is what the user actually wants to do
        response = self.showYesNoDialog('Are you sure you want to remove the selected file(s) from the project?  This operation cannot be undone.')
        if response != gtk.RESPONSE_YES:
            return False

        items = self.projview.getSelection()
        for item in items:
            # if there is an open trace window for the file or an associative node that contains
            # it, close the window(s) first
            self.tw_manager.closeByItemId(item.getId())
            if item.hasParent():
                parent = item.getParent()
                self.tw_manager.closeByItemId(parent.getId())

        # now remove the files from the project
        self.project.removeFileItems(items)

    def deleteAllSeqs(self, widget):
        # confirm this is what the user actually wants to do
        response = self.showYesNoDialog('Are you sure you want to delete all saved consensus sequences?  This operation cannot be undone.')
        if response != gtk.RESPONSE_YES:
            return

        for item in self.project:
            item.deleteConsensusSequence()
            for child in item.getChildren():
                child.deleteConsensusSequence()

    def deleteSelSeqs(self, widget):
        # confirm this is what the user actually wants to do
        response = self.showYesNoDialog('Are you sure you want to delete the selected consensus sequences?  This operation cannot be undone.')
        if response != gtk.RESPONSE_YES:
            return

        items = self.projview.getSelection()

        for item in items:
            item.deleteConsensusSequence()

    def generateAllSequences(self, widget):
        # confirm this is what the user actually wants to do
        response = self.showYesNoDialog('Are you sure you want to generate finished sequences for all trace files?  This will overwrite any sequences that have already been saved.')
        if response != gtk.RESPONSE_YES:
            return

        self.generateSequencesInternal(iter(self.project), 'Generating sequences for all trace files...')

    def generateSelectedSequences(self, widget):
        # confirm this is what the user actually wants to do
        response = self.showYesNoDialog('Are you sure you want to generate finished sequences for the selected trace files?  This will overwrite any sequences that have already been saved.')
        if response != gtk.RESPONSE_YES:
            return

        items = self.projview.getSelection()
        self.generateSequencesInternal(items, 'Generating sequences for selected trace files...')

    def generateSequencesInternal(self, itemlist, progressmsg):
        # create a progress bar dialog
        diag = ProgressBarDialog(self, progressmsg)
        diag.show()

        cnt = 0.0
        for item in itemlist:
            # update the progress bar and check if the user canceled the operation
            diag.updateProgress(cnt / len(itemlist))
            cnt += 1
            if diag.getIsCanceled():
                break

            if item.isFile() and item.hasParent():
                continue

            # load the trace files
            seqtraces = self.getSeqTraces(item)
            if seqtraces == None:
                continue

            # get and save the consensus sequence
            csb = ConsensSeqBuilder(seqtraces, self.project.getConsensSeqSettings())
            full_cons = csb.getConsensus()
            compact_cons = csb.getCompactConsensus()
            item.setUseSequence(True)
            item.setConsensusSequence(compact_cons, full_cons)

        diag.destroy()

    def projectAssociateFiles(self, widget):
        diag = EntryDialog(self, 'Group Name', 'Name for new forward/reverse group:', 'new_group', 40)
        response = diag.run()
        name = diag.get_text()
        while (name == '') and (response == gtk.RESPONSE_OK):
            response = diag.run()
            name = diag.get_text()

        diag.destroy()

        if response != gtk.RESPONSE_OK:
            return

        items = self.projview.getSelection()
        self.project.associateItems(items, name)

    def projectDissociateFiles(self, widget):
        # confirm this is what the user actually wants to do
        response = self.showYesNoDialog('Are you sure you want to remove the selected forward/reverse groupings?')
        if response != gtk.RESPONSE_YES:
            return

        items = self.projview.getSelection()
        for item in items:
            if not(item.isFile()):
                # if there is an open trace window for the file or an associative node that contains
                # it, close the window(s) first
                self.tw_manager.closeByItemId(item.getId())
                self.project.removeAssociativeItem(item)

    def findFwdRev(self, widget):
        # confirm this is what the user wants to do
        response = self.showYesNoDialog('Attempt to identify selected files as forward or reverse reads?')
        if response != gtk.RESPONSE_YES:
            return

        items = self.projview.getSelection()
        for item in items:
            if item.isFile():
                if os.path.basename(item.getName()).find(self.project.getFwdTraceSearchStr()) != -1:
                    item.setIsReverse(False)
                elif os.path.basename(item.getName()).find(self.project.getRevTraceSearchStr()) != -1:
                    item.setIsReverse(True)

    def projectAssociateAllFiles(self, widget):
        match_iter = self.project.getFwdRevMatchIter()
        self.processFwdRevMatches(match_iter)

    def projectAssociateSelectedFiles(self, widget):
        items = self.projview.getSelection()

        match_iter = self.project.getFwdRevMatchIter(items)
        self.processFwdRevMatches(match_iter)

    def processFwdRevMatches(self, match_iter):
        pair_cnt = 0
        show_confirm = True
        do_associate = False

        for pair in match_iter:
            pair_cnt += 1
            fname1 = pair[0].getFileNames()[0]
            fname2 = pair[1].getFileNames()[0]

            # confirm the user wants to group these two files
            if show_confirm:
                msgtxt = 'The following files appear to match:\n\n' + fname1 + '\n' + fname2
                msgtxt += '\n\nDo you want to group these files as matching forward and reverse sequencing traces?'
                response = self.showYesToAllDialog(msgtxt)

                if (response == gtk.RESPONSE_YES) or (response == dialgs.YES_TO_ALL):
                    if response == dialgs.YES_TO_ALL:
                        show_confirm = False
                    do_associate = True
                elif response == gtk.RESPONSE_NO:
                    do_associate = False
                else:
                    break

            if do_associate:
                # make sure the forward/reverse properties are set correctly
                pair[0].setIsReverse(False)
                pair[1].setIsReverse(True)
                self.project.associateItems(pair[0:2], pair[2])

        if pair_cnt == 0:
            self.showMessage('No matching forward and reverse sequencing trace files were found.', gtk.MESSAGE_INFO)

    def showAbout(self, widget):
        # set location of the supporting image files
        images_folder = os.path.dirname(__file__) + '/images'

        diag = gtk.AboutDialog()
        diag.set_name('SeqTrace')
        #diag.set_program_name('Simple Trace Viewer')
        diag.set_version('0.8')
        diag.set_copyright('Copyright \xC2\xA9 2012 Brian J. Stucky')
        #diag.set_authors(['Brian Stucky'])
        diag.set_comments('by Brian Stucky\n\na program for viewing and processing sequencing trace files')
        diag.set_license(
        '''Copyright (C) 2012 Brian J. Stucky

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.''')
        diag.set_logo(gtk.gdk.pixbuf_new_from_file(images_folder + '/about.png'))
        diag.run()
        diag.destroy()

    def deleteEvent(self, widget, data=None):
        if self.project_open:
            if not(self.closeProject(None)):
                return True

        # close any remaining trace windows that are still open
        self.tw_manager.closeAllTraceWindows()

        gtk.main_quit()

