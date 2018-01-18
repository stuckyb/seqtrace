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


from seqtrace.core.consens import ConsensSeqBuilder
from seqtrace.gui.dialgs import CommonDialogs

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

import os.path
import re


class ProjectSettingsDialog(Gtk.Dialog, CommonDialogs):
    def __init__(self, parent, project):
        Gtk.Dialog.__init__(
            self, title='Project Settings', parent=parent,
            flags=(Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT),
            buttons=(Gtk.STOCK_OK, Gtk.ResponseType.OK, Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)
        )
        self.set_default_response(Gtk.ResponseType.OK)

        self.project = project

        # Set up some spacing values for the UI layout.
        insideframe_padding = 14
        tabpadding_tops = 24
        tabpadding_sides = 18

        # Set up the tabs ("notebook") for the project settings.
        nb = Gtk.Notebook()
        nb.set_border_width(8)
        nb.set_tab_pos(Gtk.PositionType.TOP)

        # Create the UI elements for the trace file settings tab.
        mainvb = Gtk.VBox(False, 16)
        tracevb = Gtk.VBox(False, 20)
        tracevb.set_border_width(insideframe_padding)

        # Get the consensus sequence settings from the project.
        cssettings = self.project.getConsensSeqSettings()

        # Set up UI components for the trace file location.
        vb = Gtk.VBox()
        tf_hb1 = Gtk.HBox()
        tf_hb1.pack_start(Gtk.Label('Location of trace files:'), False, True, 0)
        tf_hb2 = Gtk.HBox()
        self.fc_entry = Gtk.Entry()
        self.fc_entry.set_width_chars(40)
        self.fc_entry.set_text(self.project.getTraceFileDir())
        tf_hb2.pack_start(self.fc_entry, True, True, 0)

        # Use the default "folder" icon for the button (formerly
        # STOCK_DIRECTORY with the deprecated stock item system).
        iconimg = Gtk.Image.new_from_icon_name('folder', Gtk.IconSize.BUTTON)
        fc_button = Gtk.Button.new_with_mnemonic(' C_hoose...')
        fc_button.set_image(iconimg)
        fc_button.connect('clicked', self.chooseDirectory, self.fc_entry)

        #fc_button.set_label('Choose...')
        tf_hb2.pack_start(fc_button, True, True, 0)
        vb.pack_start(tf_hb1, True, True, 0)
        vb.pack_start(tf_hb2, True, True, 0)

        self.fc_checkbox = Gtk.CheckButton('Use relative folder path')
        if os.path.isabs(self.project.getTraceFileDir()):
            self.fc_checkbox.set_active(False)
        else:
            self.fc_checkbox.set_active(True)
        self.fc_cb_hid = self.fc_checkbox.connect('toggled', self.useRelPathToggled)
        vb.pack_start(self.fc_checkbox, True, True, 0)

        tracevb.pack_start(vb, True, True, 0)

        # Set up UI components for the forward/reverse trace file search strings.
        vb = Gtk.VBox()
        tfs_hb1 = Gtk.HBox()
        tfs_hb1.pack_start(Gtk.Label('Search strings for identifying forward and reverse trace files:'), False, True, 0)

        # Create a layout table for the labels and text entries.
        table = Gtk.Table(2, 2)

        self.tfs_fwd_entry = Gtk.Entry()
        self.tfs_fwd_entry.set_width_chars(12)
        self.tfs_fwd_entry.set_text(self.project.getFwdTraceSearchStr())
        table.attach(Gtk.Label(label='Forward: '), 0, 1, 0, 1, xoptions=0)
        table.attach(self.tfs_fwd_entry, 1, 2, 0, 1, xoptions=0)
        
        self.tfs_rev_entry = Gtk.Entry()
        self.tfs_rev_entry.set_width_chars(12)
        self.tfs_rev_entry.set_text(self.project.getRevTraceSearchStr())
        table.attach(Gtk.Label(label='Reverse: '), 0, 1, 1, 2, xoptions=0)
        table.attach(self.tfs_rev_entry, 1, 2, 1, 2, xoptions=0)

        vb.pack_start(tfs_hb1, True, True, 0)
        vb.pack_start(table, True, True, 0)

        tracevb.pack_start(vb, True, True, 0)

        frame = Gtk.Frame(label='Trace files')
        frame.add(tracevb)
        mainvb.pack_start(frame, True, True, 0)

        # Set up UI components for the forward/reverse primer strings.
        vb = Gtk.VBox()
        vb = Gtk.VBox(False, 20)
        vb.set_border_width(insideframe_padding)

        # Create a layout table for the labels and text entries.
        table = Gtk.Table(2, 2)

        self.fwdprimer_entry = Gtk.Entry()
        self.fwdprimer_entry.set_width_chars(38)
        self.fwdprimer_entry.set_text(cssettings.getForwardPrimer())
        table.attach(Gtk.Label(label='Forward primer: '), 0, 1, 0, 1, xoptions=0)
        table.attach(self.fwdprimer_entry, 1, 2, 0, 1, xoptions=0)
        
        self.revprimer_entry = Gtk.Entry()
        self.revprimer_entry.set_width_chars(38)
        self.revprimer_entry.set_text(cssettings.getReversePrimer())
        table.attach(Gtk.Label(label='Reverse primer: '), 0, 1, 1, 2, xoptions=0)
        table.attach(self.revprimer_entry, 1, 2, 1, 2, xoptions=0)

        vb.pack_start(table, True, True, 0)

        frame = Gtk.Frame(label="Primer sequences (5' to 3')")
        frame.add(vb)
        mainvb.pack_start(frame, True, True, 0)

        # Use another VBox to get extra padding on the sides.
        vbpad = Gtk.VBox(False, 0)
        vbpad.set_border_width(tabpadding_sides)
        vbpad.pack_start(mainvb, False, True, tabpadding_tops - tabpadding_sides)

        nb.append_page(vbpad, Gtk.Label(label='Trace settings'))

        # Create the UI components for the sequence processing tab.
        mainvb = Gtk.VBox(False, 16)

        # Set up UI components for choosing the confidence score cutoff value.
        vb = Gtk.VBox(False, 12)
        vb.set_border_width(insideframe_padding)
        hb1 = Gtk.HBox()
        hb1.pack_start(Gtk.Label('Min. confidence score:  '), False, True, 0)

        self.ph_adj = Gtk.Adjustment(cssettings.getMinConfScore(), 1, 61, 1)
        spin = Gtk.SpinButton(adjustment=self.ph_adj, climb_rate=0, digits=0)
        hb1.pack_start(spin, False, False, 0)

        vb.pack_start(hb1, True, True, 0)

        # Create the UI components for choosing a consensus algorithm.
        hb1 = Gtk.HBox()
        hb1.pack_start(Gtk.Label('Consensus algorithm:  '), False, True, 0)
        self.cons_bayes_rb = Gtk.RadioButton(label='Bayesian   ')
        hb1.pack_start(self.cons_bayes_rb, False, True, 0)
        self.cons_legacy_rb = Gtk.RadioButton(group=self.cons_bayes_rb, label='SeqTrace 0.8')

        if cssettings.getConsensusAlgorithm() == 'Bayesian':
            self.cons_bayes_rb.set_active(True)
        else:
            self.cons_legacy_rb.set_active(True)

        hb1.pack_start(self.cons_legacy_rb, True, True, 0)

        vb.pack_start(hb1, True, True, 0)

        frame = Gtk.Frame(label='Consensus settings')
        frame.add(vb)
        mainvb.pack_start(frame, True, True, 0)

        # Set up UI components for sequence trimming settings.
        vb = Gtk.VBox(False, 24)
        vb.set_border_width(insideframe_padding)
        self.autotrim_checkbox = Gtk.CheckButton('Automatically trim sequence ends')
        self.autotrim_checkbox.connect('toggled', self.autoTrimToggled)
        vb.pack_start(self.autotrim_checkbox, True, True, 0)

        # Create UI components for primer trimming.
        vb2 = Gtk.VBox(False, 6)
        hb2 = Gtk.HBox()
        self.trimprimers_checkbox = Gtk.CheckButton('Trim primers if ')
        self.trimprimers_checkbox.set_active(cssettings.getTrimPrimers())
        hb2.pack_start(self.trimprimers_checkbox, False, True, 0)
        self.primermatch_th_adj = Gtk.Adjustment(int(cssettings.getPrimerMatchThreshold() * 100), 1, 100, 1)
        self.primermatch_th_spin = Gtk.SpinButton(
            adjustment=self.primermatch_th_adj, climb_rate=0, digits=0
        )
        hb2.pack_start(self.primermatch_th_spin, False, False, 0)
        self.trimprimers_label = Gtk.Label(label=' % of the primer alignment matches.')
        hb2.pack_start(self.trimprimers_label, False, True, 0)

        vb2.pack_start(hb2, True, True, 0)

        # Check box for end gap trimming.
        self.trimgaps_checkbox = Gtk.CheckButton('Trim alignment end gap regions')
        self.trimgaps_checkbox.set_active(cssettings.getTrimEndGaps())
        vb2.pack_start(self.trimgaps_checkbox, True, True, 0)

        qualtrim_winsize, qualtrim_basecnt = cssettings.getQualityTrimParams()

        # Check box and spin buttons for end quality trimming.
        hb2 = Gtk.HBox()
        self.qualtrim_checkbox = Gtk.CheckButton('Trim until at least ')
        self.qualtrim_checkbox.set_active(cssettings.getDoQualityTrim())
        hb2.pack_start(self.qualtrim_checkbox, False, True, 0)
        self.qualtrim_basecnt_adj = Gtk.Adjustment(qualtrim_basecnt, 1, qualtrim_winsize, 1)
        self.qualtrim_basecnt_spin = Gtk.SpinButton(
            adjustment=self.qualtrim_basecnt_adj, climb_rate=0, digits=0
        )
        hb2.pack_start(self.qualtrim_basecnt_spin, False, False, 0)

        self.qualtrim_label1 = Gtk.Label(label=' out of ')
        hb2.pack_start(self.qualtrim_label1, False, True, 0)
        self.qualtrim_winsize_adj = Gtk.Adjustment(qualtrim_winsize, 1, 20, 1)
        self.qualtrim_winsize_spin = Gtk.SpinButton(
            adjustment=self.qualtrim_winsize_adj, climb_rate=0, digits=0
        )
        hb2.pack_start(self.qualtrim_winsize_spin, False, False, 0)
        self.qualtrim_winsize_adj.connect('value_changed', self.autoTrimWinSizeChanged)

        self.qualtrim_label2 = Gtk.Label(label=' bases are correctly called.')
        hb2.pack_start(self.qualtrim_label2, False, True, 0)
        vb2.pack_start(hb2, True, True, 0)

        self.autotrim_checkbox.set_active(cssettings.getTrimConsensus())
        self.autotrim_checkbox.toggled()

        vb.pack_start(vb2, True, True, 0)
        frame = Gtk.Frame(label='Sequence trimming')
        frame.add(vb)

        mainvb.pack_start(frame, True, True, 0)

        # Use another VBox to get extra padding on the sides.
        vbpad = Gtk.VBox(False, 0)
        vbpad.set_border_width(tabpadding_sides)
        vbpad.pack_start(mainvb, False, True, tabpadding_tops - tabpadding_sides)

        nb.append_page(vbpad, Gtk.Label(label='Sequence processing'))

        self.vbox.pack_start(nb, True, True, 0)

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

    def getForwardPrimerStr(self):
        return self.fwdprimer_entry.get_text().strip().upper()

    def getReversePrimerStr(self):
        return self.revprimer_entry.get_text().strip().upper()

    def checkSettingsValues(self):
        """
        Checks some of the project settings inputs for validity.  If any problems are
        found, an appropriate message is displayed, and the method returns False.
        Otherwise, the method returns True.
        """
        tffpath = os.path.abspath(
                os.path.join(self.project.getProjectDir(), self.getTraceFileFolder())
                )
        if not(os.path.isdir(tffpath)):
            self.showMessage('The trace file location "' + self.getTraceFileFolder() +
                    '" is not valid.  Verify that the specified directory exists and that you have permission to read it.')
            return False

        if self.getFwdTraceSearchStr() == '':
            self.showMessage('You must specify a search string for identifying forward sequencing trace files.')
            return False

        elif self.getRevTraceSearchStr() == '':
            self.showMessage('You must specify a search string for identifying reverse sequencing trace files.')
            return False

        # Build a regular expression object for checking if the characters in the primer
        # sequence strings are all valid bases.
        reo = re.compile('[' + ''.join(ConsensSeqBuilder.allbases) + ']*')

        # Check the forward primer string.
        match = reo.match(self.getForwardPrimerStr())
        if (match.end() - match.start()) != len(self.getForwardPrimerStr()):
            self.showMessage('The forward primer sequence contains invalid characters.  You may only use IUPAC nucleotide codes.')
            return False

        # Check the reverse primer string.
        match = reo.match(self.getReversePrimerStr())
        if (match.end() - match.start()) != len(self.getReversePrimerStr()):
            self.showMessage('The reverse primer sequence contains invalid characters.  You may only use IUPAC nucleotide codes.')
            return False

        # If primer trimming is enabled, make sure that we have sequences for both primers.
        if self.trimprimers_checkbox.get_active():
            if self.getForwardPrimerStr() == '' or self.getReversePrimerStr() == '':
                # Create a customized error message.
                if self.getForwardPrimerStr() == '' and self.getReversePrimerStr() == '':
                    msgdetail = 'forward and reverse primer sequences are'
                elif self.getForwardPrimerStr() == '':
                    msgdetail = 'forward primer sequence is'
                elif self.getReversePrimerStr() == '':
                    msgdetail = 'reverse primer sequence is'

                self.showMessage('You have enabled primer trimming, but the ' + msgdetail + ' missing.  Please specify both primer sequences or disable primer trimming.')
                return False
    
        return True

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
                self.trimgaps_checkbox.get_active(),
                self.trimprimers_checkbox.get_active(),
                float(self.primermatch_th_adj.get_value()) / 100.0,
                self.getForwardPrimerStr(), self.getReversePrimerStr(),
                self.qualtrim_checkbox.get_active(),
                (int(self.qualtrim_winsize_adj.get_value()), int(self.qualtrim_basecnt_adj.get_value())),
                )

    def chooseDirectory(self, widget, entry):
        # create a file chooser dialog to get a directory name from the user
        fc = Gtk.FileChooserDialog(
            'Choose Trace Files Location', self, Gtk.FileChooserAction.SELECT_FOLDER,
            (Gtk.STOCK_OK, Gtk.ResponseType.OK, Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)
        )
        fc.set_current_folder(self.project.getAbsTraceFileDir())
        response = fc.run()
        fname = fc.get_filename()
        fc.destroy()
        if response != Gtk.ResponseType.OK:
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
            self.trimprimers_checkbox.set_sensitive(True)
            self.primermatch_th_spin.set_sensitive(True)
            self.trimprimers_label.set_sensitive(True)
            self.qualtrim_basecnt_spin.set_sensitive(True)
            self.qualtrim_winsize_spin.set_sensitive(True)
            self.trimgaps_checkbox.set_sensitive(True)
            self.qualtrim_checkbox.set_sensitive(True)
            self.qualtrim_label1.set_sensitive(True)
            self.qualtrim_label2.set_sensitive(True)
        else:
            self.trimprimers_checkbox.set_sensitive(False)
            self.primermatch_th_spin.set_sensitive(False)
            self.trimprimers_label.set_sensitive(False)
            self.qualtrim_basecnt_spin.set_sensitive(False)
            self.qualtrim_winsize_spin.set_sensitive(False)
            self.trimgaps_checkbox.set_sensitive(False)
            self.qualtrim_checkbox.set_sensitive(False)
            self.qualtrim_label1.set_sensitive(False)
            self.qualtrim_label2.set_sensitive(False)

    def autoTrimWinSizeChanged(self, adj):
        winsize = self.qualtrim_winsize_adj.get_value()

        if self.qualtrim_basecnt_adj.get_value() > winsize:
            self.qualtrim_basecnt_adj.set_value(winsize)

        self.qualtrim_basecnt_adj.set_upper(winsize)
