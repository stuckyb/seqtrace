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


class GenericStatusBar(Gtk.Frame):
    """
    Implements the appearance and layout of a generic status bar.  Not intended
    for direct instantiation; this class should be subclassed to actually
    display messages. Unlike the status bar provided by GTK, this status bar
    has the ability to include multiple message areas.
    """
    def __init__(self):
        Gtk.Frame.__init__(self)

        self.set_shadow_type(Gtk.ShadowType.OUT )

        self.hbox = Gtk.HBox(False, 0)

        # Use a VBox to get some padding at the top and bottom of the status
        # areas.
        vbox = Gtk.VBox(False, 0)
        vbox.pack_start(self.hbox, False, False, 4)
        self.add(vbox)

        self.status_area_cnt = 0

        # Set up a custom CSS provider for drawing the status bar borders.
        self.css_provider = Gtk.CssProvider()
        self.css_provider.load_from_data("""
            GtkFrame.main {
                border-style: solid;
                border-width: 1px 0 0 0;
            }
            
            GtkFrame.status_area {
                padding: 1px 8px 1px 8px;
            }
            
            GtkFrame.first_area {
                border-width: 0;
            }
            
            GtkFrame.next_area {
                border-style: groove;
                border-width: 0 0 0 2px;
            }"""
        )

        scontext = self.get_style_context()
        scontext.add_class('main')
        scontext.add_provider(
            self.css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def addStatusArea(self, expand=False):
        """
        Adds an independent message area to the status bar.  Returns a
        reference to a label for managing the text displayed by the message
        area.
        """
        frame = Gtk.Frame()
        frame.set_shadow_type(Gtk.ShadowType.IN)
        label = Gtk.Label()
        label.set_padding(0, 0)
        label.set_alignment(0, 0)
        frame.add(label)

        self.hbox.pack_start(frame, expand, True, 0)

        scontext = frame.get_style_context()
        scontext.add_class('status_area')
        if self.status_area_cnt > 0:
            scontext.add_class('next_area')
        else:
            scontext.add_class('first_area')

        scontext.add_provider(
            self.css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        self.status_area_cnt += 1

        return label


class ConsensSeqStatusBar(GenericStatusBar):
    """
    A status bar that tracks the sequence lengths and settings state of a
    consensus sequence builder.
    """
    def __init__(self, consens_seq_builder):
        GenericStatusBar.__init__(self)

        self.cons = consens_seq_builder
        self.cons_len = len(self.cons.getCompactConsensus())

        self.cons.registerObserver('consensus_changed', self.consChanged)
        self.cons.getSettings().registerObserver(
            'settings_change', self.consSettingsChanged
        )
        self.connect('destroy', self.onDestroy)

        # the alignment/raw length
        self.align_label = self.addStatusArea()

        # the consensus length
        self.cons_label = self.addStatusArea()

        # additional messages
        self.status_label = self.addStatusArea(True)

        self.setSeqLabelTexts()

    def onDestroy(self, widget):
        # Unregister this object as an observer of the consensus sequence
        # settings and consensus sequence.
        self.cons.getSettings().unregisterObserver('settings_change', self.consSettingsChanged)
        self.cons.unregisterObserver('consensus_changed', self.consChanged)

    def setSeqLabelTexts(self):
        if self.cons.getNumSeqs() == 1:
            msgstr = 'trace seq. length: '
        else:
            msgstr = 'alignment length: '

        self.align_label.set_text(msgstr + str(len(self.cons.getAlignedSequence(0))) + ' b')
        
        self.cons_label.set_text('edited seq. length: ' + str(self.cons_len) + ' b')

    def consChanged(self, startindex, endindex):
        # clear the status label
        self.status_label.set_markup('')

        if len(self.cons.getCompactConsensus()) != self.cons_len:
            self.cons_len = len(self.cons.getCompactConsensus())
            self.setSeqLabelTexts()

    def consSettingsChanged(self):
        warnstr = '<span foreground="#AA0000"> Sequence consensus/trimming settings have changed!</span>'
        self.status_label.set_markup(warnstr)


class ProjectStatusBar(GenericStatusBar):
    """
    A status bar that tracks the number of files in a project.
    """
    def __init__(self, project):
        GenericStatusBar.__init__(self)

        self.project = project

        self.project.registerObserver('files_added', self.numFilesChanged)
        self.project.registerObserver('files_removed', self.numFilesChanged)
        self.project.registerObserver('file_loaded', self.numFilesChanged)
        self.project.registerObserver('project_cleared', self.numFilesChanged)

        # number of files in the project
        self.numfile_label = self.addStatusArea(True)

    def setNumFiles(self):
        numfiles = self.project.getNumFiles()
        self.numfile_label.set_text('files in project: ' + str(numfiles))

    def numFilesChanged(self):
        self.setNumFiles()

    def showNoProject(self):
        self.numfile_label.set_text('')

