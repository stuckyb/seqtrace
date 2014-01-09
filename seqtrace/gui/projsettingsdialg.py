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


from seqtrace.gui.dialgs import CommonDialogs

import pygtk
pygtk.require('2.0')
import gtk

import os.path


class ProjectSettingsDialog(gtk.Dialog, CommonDialogs):
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
        self.fc_cb_hid = self.fc_checkbox.connect('toggled', self.useRelPathToggled)
        vb.pack_start(self.fc_checkbox)

        tracevb.pack_start(vb)

        # Set up UI components for the forward/reverse trace file search strings.
        vb = gtk.VBox()
        tfs_hb1 = gtk.HBox()
        tfs_hb1.pack_start(gtk.Label('Search strings for identifying forward and reverse trace files:'), False)

        # Create a layout table for the labels and text entries.
        table = gtk.Table(2, 2)

        self.tfs_fwd_entry = gtk.Entry()
        self.tfs_fwd_entry.set_width_chars(12)
        self.tfs_fwd_entry.set_text(self.project.getFwdTraceSearchStr())
        table.attach(gtk.Label('Forward: '), 0, 1, 0, 1, xoptions=0)
        table.attach(self.tfs_fwd_entry, 1, 2, 0, 1, xoptions=0)
        
        self.tfs_rev_entry = gtk.Entry()
        self.tfs_rev_entry.set_width_chars(12)
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

        # set up UI components for choosing the confidence score cutoff value
        vb = gtk.VBox(False, 20)
        vb.set_border_width(10)
        hb1 = gtk.HBox()
        hb1.pack_start(gtk.Label('Min. confidence score:  '), False)

        self.ph_adj = gtk.Adjustment(cssettings.getMinConfScore(), 1, 61, 1)
        spin = gtk.SpinButton(self.ph_adj)
        hb1.pack_start(spin, False, False)

        vb.pack_start(hb1)

        # Create the UI components for choosing a consensus algorithm.
        hb1 = gtk.HBox()
        hb1.pack_start(gtk.Label('Consensus algorithm:  '), False)
        self.cons_bayes_rb = gtk.RadioButton(None, 'Bayesian   ')
        hb1.pack_start(self.cons_bayes_rb, False)
        self.cons_legacy_rb = gtk.RadioButton(self.cons_bayes_rb, 'SeqTrace 0.8')

        if cssettings.getConsensusAlgorithm() == 'Bayesian':
            self.cons_bayes_rb.set_active(True)
        else:
            self.cons_legacy_rb.set_active(True)

        hb1.pack_start(self.cons_legacy_rb)

        vb.pack_start(hb1)

        # set up UI components for sequence trimming settings
        vb2 = gtk.VBox()
        self.autotrim_checkbox = gtk.CheckButton('automatically trim sequence ends')
        self.autotrim_checkbox.connect('toggled', self.autoTrimToggled)
        vb2.pack_start(self.autotrim_checkbox)

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
        vb2.pack_start(hb2)

        self.trimgaps_checkbox = gtk.CheckButton('trim alignment end gap regions')
        self.trimgaps_checkbox.set_active(cssettings.getTrimEndGaps())
        vb2.pack_start(self.trimgaps_checkbox)

        self.autotrim_checkbox.set_active(cssettings.getDoAutoTrim())
        self.autotrim_checkbox.toggled()

        vb.pack_start(vb2)
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

    def getConsensusAlgorithm(self):
        if self.cons_bayes_rb.get_active():
            return 'Bayesian'
        else:
            return 'legacy'

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
                self.getConsensusAlgorithm(),
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
            # On Windows, there is no root location for all drives, so getting a relative path between
            # drives is impossible.  So, we need to check if the CWD and the chosen directory are on
            # different drives, and if so, switch to using an absolute path.  We can check this by seeing
            # if relpath throws a ValueError exception, then toggle the "relative path" checkbox if needed.
            try:
                tmpname = os.path.relpath(fname, self.project.getProjectDir())
                fname = tmpname
            except ValueError:
                self.fc_checkbox.handler_block(self.fc_cb_hid)
                self.fc_checkbox.set_active(False)
                self.fc_checkbox.handler_unblock(self.fc_cb_hid)

        entry.set_text(fname)

    def useRelPathToggled(self, button):
        # toggle the display of the currently-selected trace file folder, making sure that paths
        # are always relative to the location of the project file
        if self.fc_checkbox.get_active():
            # On Windows, there is no root location for all drives, so getting a relative path between
            # drives is impossible.  We can check for this by seeing if relpath throws a ValueError
            # exception, then uncheck the "relative path" checkbox if needed.
            try:
                tmpname = os.path.relpath(self.fc_entry.get_text(), self.project.getProjectDir())
                self.fc_entry.set_text(tmpname)
            except ValueError:
                self.fc_checkbox.handler_block(self.fc_cb_hid)
                self.fc_checkbox.set_active(False)
                self.showMessage('Relative paths cannot be used when the trace files and project file are located on different drives.')
                self.fc_checkbox.handler_unblock(self.fc_cb_hid)
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
