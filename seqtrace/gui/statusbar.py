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


import pygtk
pygtk.require('2.0')
import gtk



class GenericStatusBar(gtk.Frame):
    """ Implements the appearance and layout of a generic status bar.  Not intended for direct instantiation;
    this class should be subclassed to actually display messages. Unlike the status bar provided by GTK, this
    status bar has the ability to include multiple message areas. """
    def __init__(self):
        gtk.Frame.__init__(self)

        self.set_shadow_type(gtk.SHADOW_OUT)

        self.hbox = gtk.HBox(False, 0)

        self.add(self.hbox)

    def addStatusArea(self, expand=False):
        """ Adds an independent message area to the status bar.  Returns a reference to a label for managing the
        text displayed by the message area. """
        frame = gtk.Frame()
        frame.set_shadow_type(gtk.SHADOW_IN)
        frame.set_border_width(1)
        label = gtk.Label()
        label.set_padding(4, 1)
        label.set_alignment(0, 0)
        frame.add(label)
        self.hbox.pack_start(frame, expand)

        return label


class ConsensSeqStatusBar(GenericStatusBar):
    """ A status bar that tracks the sequence lengths and settings state of a consensus
    sequence builder. """
    def __init__(self, consens_seq_builder):
        GenericStatusBar.__init__(self)

        self.cons = consens_seq_builder
        self.cons_len = len(self.cons.getCompactConsensus())

        self.cons.registerObserver('consensus_changed', self.consChanged)
        self.cons.getSettings().registerObserver('settings_change', self.consSettingsChanged)
        self.connect('destroy', self.onDestroy)

        # the alignment/raw length
        self.align_label = self.addStatusArea()

        # the consensus length
        self.cons_label = self.addStatusArea()

        # additional messages
        self.status_label = self.addStatusArea(True)

        self.setSeqLabelTexts()

    def onDestroy(self, widget):
        # unregister this object as an observer of the consensus sequence settings and consensus sequence
        self.cons.getSettings().unregisterObserver('settings_change', self.consSettingsChanged)
        self.cons.unregisterObserver('consensus_changed', self.consChanged)

    def setSeqLabelTexts(self):
        if self.cons.getNumSeqs() == 1:
            msgstr = 'trace seq. length: '
        else:
            msgstr = 'alignment length: '

        self.align_label.set_text(msgstr + str(len(self.cons.getAlignedSequence(0))) + ' b')
        
        self.cons_label.set_text('working seq. length: ' + str(self.cons_len) + ' b')

    def consChanged(self, startindex, endindex):
        # clear the status label
        self.status_label.set_markup('')

        if len(self.cons.getCompactConsensus()) != self.cons_len:
            self.cons_len = len(self.cons.getCompactConsensus())
            self.setSeqLabelTexts()

    def consSettingsChanged(self):
        warnstr = '<span foreground="#AA0000">working sequence settings have changed</span>'
        self.status_label.set_markup(warnstr)


class ProjectStatusBar(GenericStatusBar):
    """ A status bar that tracks the number of files in a project. """
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

