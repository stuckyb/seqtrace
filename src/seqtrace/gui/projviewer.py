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
from gi.repository import GdkPixbuf

from seqtrace.core import stproject
from seqtrace.core.observable import Observable

# Get the location of the GUI image files.
from seqtrace.gui import images_folder


# Another way to detect if the forward/reverse arrow in the treeview is clicked.  I'm not sure which
# approach is better, or "more correct".  For now, the method of testing the x/y coords of clicks on
# the treeview itself is used, because it was simpler to integrate with already-existing code.
#class CellRendererPixbufClickable(Gtk.CellRendererPixbuf):
#    def __init__(self):
#        GObject.GObject.__init__(self)
#        self.set_property('mode', Gtk.CellRendererMode.ACTIVATABLE)
#
#    def do_activate(self, event, widget, path, background_area, cell_area, flags):
#        if (event.x > cell_area.x) and (event.x < (cell_area.x + cell_area.width)):
#            print 'clicked'
#from gi.repository import GObject
#GObject.type_register(CellRendererPixbufClickable)


class ProjectViewer(Gtk.ScrolledWindow, Observable):
    def __init__(self, project):
        Gtk.ScrolledWindow.__init__(self)

        self.project = project

        # initialize the TreeView
        self.treeview = Gtk.TreeView(self.project.getTreeStore())
        self.treeview.set_enable_tree_lines(True)
        self.treeview.set_grid_lines(Gtk.TreeViewGridLines.NONE)
        self.treeview.set_rules_hint(True)

        # first column: for item name and forward/reverse icons
        self.col1 = Gtk.TreeViewColumn('Trace Files')
        self.col1.set_expand(True)
        self.col1.set_resizable(True)
        #self.col1.set_clickable(True)
        #self.col1.connect('clicked', self.colHeadClicked, stproject.FILE_NAME)
        self.col1.set_sort_column_id(stproject.FILE_NAME)

        # set up cell renderer for forward/reverse icons
        self.isfwdrev_both = GdkPixbuf.Pixbuf.new_from_file(images_folder + '/isfwdrev_both.png')
        self.isfwdrev_fwd = GdkPixbuf.Pixbuf.new_from_file(images_folder + '/isfwdrev_fwd.png')
        self.isfwdrev_rev = GdkPixbuf.Pixbuf.new_from_file(images_folder + '/isfwdrev_rev.png')
        self.isrev_ren = Gtk.CellRendererPixbuf()
        self.col1.pack_start(self.isrev_ren, False)
        self.col1.set_cell_data_func(self.isrev_ren, self.showFrwdRev)

        # set up cell renderer for item name
        nameren = Gtk.CellRendererText()
        nameren.connect('edited', self.nameEdited)
        self.col1.pack_start(nameren, True)
        self.col1.add_attribute(nameren, 'text', stproject.FILE_NAME)
        self.col1.set_cell_data_func(nameren, self.isRowFile)
        self.treeview.append_column(self.col1)

        # second column: for description/notes
        notesren = Gtk.CellRendererText()
        notesren.connect('edited', self.notesEdited)
        notesren.set_property('editable', True)
        self.col2 = Gtk.TreeViewColumn('Notes/Description', notesren, text=stproject.NOTES)
        self.col2.set_expand(True)
        self.col2.set_resizable(True)
        self.col2.set_sort_column_id(stproject.NOTES)
        self.treeview.append_column(self.col2)

        # third column: for has sequence icons
        hasseqren = Gtk.CellRendererPixbuf()
        self.hasseq_no = GdkPixbuf.Pixbuf.new_from_file(images_folder + '/hasseq_no.png')
        self.hasseq_yes = GdkPixbuf.Pixbuf.new_from_file(images_folder + '/hasseq_yes.png')
        col3 = Gtk.TreeViewColumn('Seq. Saved', hasseqren)
        col3.set_cell_data_func(hasseqren, self.renderHasSeq)
        col3.set_sort_column_id(stproject.HAS_CONS)
        self.treeview.append_column(col3)

        # fourth column: for use sequence checkbox
        useseqren = Gtk.CellRendererToggle()
        useseqren.set_property('activatable', True)
        useseqren.connect('toggled', self.useseqToggled)
        col4 = Gtk.TreeViewColumn('Use Seq.', useseqren, active=stproject.USE_CONS)
        col4.set_cell_data_func(useseqren, self.renderUseSeq)
        col4.set_sort_column_id(stproject.USE_CONS)
        self.treeview.append_column(col4)

        self.treeview.get_selection().set_mode(Gtk.SelectionMode.MULTIPLE)

        # add the treeview to the scrolled window
        self.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
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

    def showFrwdRev(self, col, renderer, model, node, data):
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

    def isRowFile(self, col, renderer, model, node, data):
        item = self.project.getItemByTsiter(node)

        if item.isFile():
            renderer.set_property('editable', False)
        else:
            renderer.set_property('editable', True)

    def renderHasSeq(self, col, renderer, model, node, data):
        item = self.project.getItemByTsiter(node)
        self.setSeqRendererVisible(renderer, item)

        if item.hasSequence():
            renderer.set_property('pixbuf', self.hasseq_yes)
        else:
            renderer.set_property('pixbuf', self.hasseq_no)

    def renderUseSeq(self, col, renderer, model, node, data):
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
                # cell_area contains the coordinates (relative to the treeview
                # widget) of the actual content of the cell (including both
                # cell renderers), ignoring any space in the cell outside of
                # the renderers (such as area for the tree expanders).
                # renderer_width is the width the specified renderer occupies
                # inside of the cell_area.
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

