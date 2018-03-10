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


import unittest
import os
import gi
gi.require_version('Pango', '1.0')
from gi.repository import Pango
import tempfile, shutil

from seqtrace.core.stproject import *
from seqtrace.gui import getDefaultFont


# This test fixture provides fairly complete coverage of project functionality,
# project iterators, and project items, and good coverage of reading/writing
# project files.
class TestProject(unittest.TestCase):
    def setUp(self):
        self.filename = 'test.str'
        self.tracefiles = ('fwd1.ztr', 'rev1.ztr', 'fwd2.ztr', 'rev2.ztr', 'fwd3.ztr')

        self.proj = SequenceTraceProject()
        self.proj.setProjectFileName(self.filename)

    def test_init(self):
        """
        Checks if the initial state of a new project is as expected.
        """
        self.assertEqual(self.proj.getFwdTraceSearchStr(), '_F')
        self.assertEqual(self.proj.getRevTraceSearchStr(), '_R')
        self.assertEqual(self.proj.getTraceFileDir(), '.')
        self.assertEqual(self.proj.getAbsTraceFileDir(), os.getcwd())

        self.assertIsInstance(self.proj.getFont(), Pango.FontDescription)

        csettings = self.proj.getConsensSeqSettings()
        self.assertEqual(csettings.getMinConfScore(), 30)
        self.assertEqual(csettings.getConsensusAlgorithm(), 'Bayesian')
        self.assertTrue(csettings.getTrimConsensus())
        self.assertFalse(csettings.getTrimEndGaps())
        self.assertFalse(csettings.getTrimPrimers())
        self.assertEqual(csettings.getForwardPrimer(), '')
        self.assertEqual(csettings.getReversePrimer(), '')
        self.assertEqual(csettings.getPrimerMatchThreshold(), 0.8)
        self.assertTrue(csettings.getDoQualityTrim())
        self.assertEqual(csettings.getQualityTrimParams(), (10, 8))

        self.assertEqual(
            self.proj.getProjectFileName(), os.path.abspath(self.filename)
        )
        self.assertEqual(self.proj.getProjectDir(), os.getcwd())
        self.assertTrue(self.proj.getSaveState())
        self.assertTrue(self.proj.isProjectEmpty())

    def test_addRemoveFiles(self):
        self.assertTrue(self.proj.isProjectEmpty())

        self.proj.addFiles(self.tracefiles)

        self.assertFalse(self.proj.isProjectEmpty())
        for file in self.tracefiles:
            self.assertTrue(self.proj.isFileInProject(file))

        self.assertFalse(self.proj.isFileInProject('not_exist.ztr'))

        for item in self.proj:
            self.proj.removeFileItems((item,))

        self.assertTrue(self.proj.isProjectEmpty())
        for file in self.tracefiles:
            self.assertFalse(self.proj.isFileInProject(file))

    def test_projIter(self):
        self.proj.addFiles(self.tracefiles)

        cnt = 0
        for item in self.proj:
            cnt += 1
        self.assertEqual(cnt, len(self.tracefiles))

        # create an associative item
        self.proj.associateItems((self.proj.getItemById(2), self.proj.getItemById(3)), 'new item')

        cnt = 0
        for item in self.proj:
            cnt += 1
        self.assertEqual(cnt, len(self.tracefiles) - 1)

    def test_fwdRevMatchIter(self):
        self.proj.addFiles(self.tracefiles)
        self.proj.setFwdTraceSearchStr('fwd')
        self.proj.setRevTraceSearchStr('rev')

        miter = self.proj.getFwdRevMatchIter()
        match = miter.next()
        self.assertEqual(match[2], '1.ztr')
        match = miter.next()
        self.assertEqual(match[2], '2.ztr')
        self.assertRaises(StopIteration, miter.next)

        # now test some trickier matches
        self.proj.clearProject()
        self.proj.setFwdTraceSearchStr('F_')
        self.proj.setRevTraceSearchStr('R_')
        pairs = [['F_', 'R_', ''],
                ['F_CO1_F_10F_.ab1F_', 'R_CO1_F_10F_.ab1F_', 'CO1_F_10F_.ab1F_'],
                ['F_CO1_F_10F_.ab1F_', 'F_CO1_R_10F_.ab1F_', 'F_CO1_10F_.ab1F_'],
                ['F_CO1_F_10F_.ab1F_', 'F_CO1_F_10R_.ab1F_', 'F_CO1_F_10.ab1F_'],
                ['F_CO1_F_10F_.ab1F_', 'F_CO1_F_10F_.ab1R_', 'F_CO1_F_10F_.ab1']]
        # some additional names that have either forward or reverse strings in them
        # but don't pair up with any other names
        extnames = ['F_12S_.ab1', '16S_R_10.ab1']

        # Add the names to the project (note that the names without 'R' in them
        # will sort to the top of the project and so be chosen first for
        # matching).
        for names in pairs:
            self.proj.addFiles(names[0:2])
        for name in extnames:
            self.proj.addFiles((name,))

        miter = self.proj.getFwdRevMatchIter()
        for names in pairs:
            match = miter.next()
            self.assertEqual(match[0].getName(), names[0])
            self.assertEqual(match[1].getName(), names[1])
            self.assertEqual(match[2], names[2])

        self.assertRaises(StopIteration, miter.next)

        # Swap forward and reverse search strings and test if all matches are
        # still found.
        self.proj.setFwdTraceSearchStr('R_')
        self.proj.setRevTraceSearchStr('F_')
        miter = self.proj.getFwdRevMatchIter()
        for names in pairs:
            match = miter.next()
            # the forward and reverse names will be swapped
            self.assertEqual(match[0].getName(), names[1])
            self.assertEqual(match[1].getName(), names[0])
            self.assertEqual(match[2], names[2])

        self.assertRaises(StopIteration, miter.next)

    def test_associateItems(self):
        self.proj.addFiles(self.tracefiles)
        self.proj.setFwdTraceSearchStr('fwd')
        self.proj.setRevTraceSearchStr('rev')

        for match in self.proj.getFwdRevMatchIter():
            self.proj.associateItems((match[0], match[1]), match[2])

        cnt = 0
        for item in self.proj:
            cnt += 1
            if item.getName() == 'fwd3.ztr':
                self.assertTrue(item.isFile())
            else:
                self.assertFalse(item.isFile())
                self.assertEqual(len(item.getChildren()), 2)
                for child in item.getChildren():
                    # test that the parent's name is contained in the child's name
                    self.assertNotEqual(child.getName().find(item.getName()), -1)

        self.assertEqual(cnt, 3)

        # now delete all of the associative items
        for item in self.proj:
            if not(item.isFile()):
                self.proj.removeAssociativeItem(item)

        cnt = 0
        for item in self.proj:
            cnt += 1
            self.assertTrue(item.isFile())

        self.assertEqual(cnt, len(self.tracefiles))

    def test_removeFileItems(self):
        self.proj.addFiles(self.tracefiles)

        item = self.proj.getItemById(0)
        name = item.getName()
        i_id = item.getId()

        # remove the item
        self.proj.removeFileItems((item,))

        # test that it is no longer in the project
        cnt = 0
        for item in self.proj:
            cnt += 1
            self.assertNotEqual(item.getName(), name)
            self.assertNotEqual(item.getId(), i_id)

        self.assertEqual(cnt, len(self.tracefiles) - 1)

        self.proj.clearProject()
        self.proj.addFiles(self.tracefiles)

        # next, test removing a file item inside of an associative item
        item = self.proj.getItemById(0)
        name = item.getName()
        i_id = item.getId()
        self.proj.associateItems((item, self.proj.getItemById(1)), 'new_item')

        # remove the item
        self.proj.removeFileItems((self.proj.getItemById(0),))

        # test that it is no longer in the project and that the associative item has also been removed
        cnt = 0
        for item in self.proj:
            cnt += 1
            self.assertTrue(item.isFile())
            self.assertNotEqual(item.getName(), name)
            self.assertNotEqual(item.getId(), i_id)

        self.assertEqual(cnt, len(self.tracefiles) - 1)

    def test_clearProject(self):
        # First, set all of the various project settings.
        self.proj.addFiles(self.tracefiles)
        self.proj.setFwdTraceSearchStr('_F_')
        self.proj.setFwdTraceSearchStr('_R_')
        self.proj.setTraceFileDir('tracedir')

        newfont = getDefaultFont()
        default_font_str = newfont.to_string()
        newfont.set_size(newfont.get_size() + 1)
        self.proj.setFont(newfont)
        self.assertNotEqual(default_font_str, self.proj.getFont().to_string())

        csettings = self.proj.getConsensSeqSettings()
        csettings.setMinConfScore(20)
        csettings.setConsensusAlgorithm('legacy')
        csettings.setTrimConsensus(False)
        csettings.setTrimPrimers(True)
        csettings.setPrimerMatchThreshold(0.2)
        csettings.setForwardPrimer('AAAT')
        csettings.setReversePrimer('AAAT')
        csettings.setTrimEndGaps(False)
        csettings.setDoQualityTrim(False)
        csettings.setQualityTrimParams(20, 18)

        self.proj.clearProject()

        # Now make sure the project is empty and all settings have default
        # values.
        self.assertTrue(self.proj.isProjectEmpty())
        for file in self.tracefiles:
            self.assertFalse(self.proj.isFileInProject(file))

        self.assertEqual(self.proj.getFwdTraceSearchStr(), '_F')
        self.assertEqual(self.proj.getRevTraceSearchStr(), '_R')
        self.assertEqual(self.proj.getTraceFileDir(), '.')
        self.assertEqual(self.proj.getAbsTraceFileDir(), os.getcwd())

        self.assertEqual(default_font_str, self.proj.getFont().to_string())

        csettings = self.proj.getConsensSeqSettings()
        self.assertEqual(csettings.getMinConfScore(), 30)
        self.assertEqual(csettings.getConsensusAlgorithm(), 'Bayesian')
        self.assertTrue(csettings.getTrimConsensus())
        self.assertFalse(csettings.getTrimEndGaps())
        self.assertFalse(csettings.getTrimPrimers())
        self.assertEqual(csettings.getForwardPrimer(), '')
        self.assertEqual(csettings.getReversePrimer(), '')
        self.assertEqual(csettings.getPrimerMatchThreshold(), 0.8)
        self.assertTrue(csettings.getDoQualityTrim())
        self.assertEqual(csettings.getQualityTrimParams(), (10, 8))

    def test_projectItem(self):
        self.proj.addFiles(self.tracefiles)
        item = self.proj.getItemById(0)

        # test the basic item properties
        self.assertEqual(item.getId(), 0)
        self.assertTrue(item.isFile())
        self.assertFalse(item.hasParent())
        self.assertEqual(item.getChildren(), ())

        # test the name and notes methods
        item.setName('test_name')
        self.assertEqual(item.getName(), 'test_name')
        self.assertEqual(item.getFileNames()[0], 'test_name')

        self.assertEqual(item.getNotes(), '')
        item.setNotes('sample notes')
        self.assertEqual(item.getNotes(), 'sample notes')

        # test the sequence methods
        self.assertFalse(item.hasSequence())
        self.assertFalse(item.getUseSequence())
        self.assertEqual(item.getCompactConsSequence(), '')
        self.assertEqual(item.getFullConsSequence(), '')
        self.assertFalse(item.getIsReverse())

        item.setIsReverse(True)
        self.assertTrue(item.getIsReverse())
        item.toggleIsReverse()
        self.assertFalse(item.getIsReverse())

        item.setConsensusSequence('AATTAATTGGCC', 'AA TT AA TT GGCC')
        item.setUseSequence(True)
        self.assertEqual(item.getCompactConsSequence(), 'AATTAATTGGCC')
        self.assertEqual(item.getFullConsSequence(), 'AA TT AA TT GGCC')
        self.assertTrue(item.hasSequence())
        self.assertTrue(item.getUseSequence())

        item.toggleUseSequence()
        self.assertFalse(item.getUseSequence())
        item.toggleUseSequence()
        self.assertTrue(item.getUseSequence())

        item.deleteConsensusSequence()
        self.assertFalse(item.hasSequence())
        self.assertFalse(item.getUseSequence())
        self.assertEqual(item.getCompactConsSequence(), '')
        self.assertEqual(item.getFullConsSequence(), '')

        # next, run tests specific to an associative item and its child items
        a_item = self.proj.associateItems((item, self.proj.getItemById(1)), 'new_item')
        self.assertFalse(a_item.isFile())
        self.assertFalse(a_item.hasParent())
        self.assertEqual(len(a_item.getChildren()), 2)
        self.assertEqual(len(a_item.getFileNames()), 2)

        for child in a_item.getChildren():
            self.assertFalse(child.getIsReverse())
            self.assertTrue(child.isFile())
            self.assertTrue(child.hasParent())
            parent = child.getParent()
            self.assertEqual(parent.getName(), 'new_item')

    def _checkProjectItems(self, project, child1name, child2name):
        """
        Common code used for testing a standard set of items read from a saved
        project file.
        """
        for (cnt, item) in enumerate(project):
            if not(item.isFile()):
                # test the properties of the associative item and its child items
                self.assertEqual(item.getName(), 'new item')
                self.assertEqual(item.getNotes(), 'sample notes')
                self.assertEqual(item.getCompactConsSequence(), 'AATTAATTGGCC')
                self.assertEqual(item.getFullConsSequence(), 'AA TT AA TT GGCC')
                self.assertTrue(item.hasSequence())
                self.assertTrue(item.getUseSequence())

                children = item.getChildren()
                child1 = children[0]
                child2 = children[1]
                self.assertEqual(len(children), 2)
                self.assertEqual(child1.getName(), child1name)
                self.assertEqual(child2.getName(), child2name)
                self.assertFalse(child1.getIsReverse())
                self.assertTrue(child2.getIsReverse())
                self.assertEqual(child1.getCompactConsSequence(), 'CATCATGATCATTAGTAC')
                self.assertEqual(child1.getFullConsSequence(), 'CATCATGATCAT TAGTAC')
                self.assertTrue(child1.hasSequence())
                self.assertEqual(child2.getCompactConsSequence(), '')
                self.assertEqual(child2.getFullConsSequence(), '')
                self.assertFalse(child2.hasSequence())

                for child in children:
                    self.assertTrue(child.hasParent())
                    self.assertEqual(child.getParent().getName(), 'new item')
                    self.assertFalse(child.getUseSequence())
            else:
                # test the properties of the top-level file items
                self.assertEqual(item.getNotes(), str(cnt))
                self.assertEqual(item.getCompactConsSequence(), 'AT' * cnt)
                self.assertEqual(item.getFullConsSequence(), 'AT' * cnt)
                self.assertEqual(item.hasSequence(), cnt != 0)
                self.assertFalse(item.getUseSequence())
                self.assertFalse(item.getIsReverse())

    def test_readWriteProject(self):
        # Write the test project file in a temporary directory.
        tmpdir = tempfile.mkdtemp()
        tmpfpath = os.path.join(tmpdir, self.filename)
        self.proj.setProjectFileName(tmpfpath)

        self.proj.addFiles(self.tracefiles)
        self.proj.setFwdTraceSearchStr('_F_')
        self.proj.setRevTraceSearchStr('_R_')
        self.proj.setTraceFileDir('tracedir')

        # Set a non-default font.
        newfont = getDefaultFont()
        newfont.set_size(newfont.get_size() + 1)
        newfontstr = newfont.to_string()
        self.assertNotEqual(newfontstr, self.proj.getFont().to_string())
        self.proj.setFont(newfont)

        # Set all consensus settings.
        csettings = self.proj.getConsensSeqSettings()
        csettings.setMinConfScore(20)
        csettings.setConsensusAlgorithm('legacy')
        csettings.setTrimConsensus(False)
        csettings.setTrimPrimers(True)
        csettings.setPrimerMatchThreshold(0.2)
        csettings.setForwardPrimer('AAAT')
        csettings.setReversePrimer('GGGC')
        csettings.setTrimEndGaps(True)
        csettings.setDoQualityTrim(False)
        csettings.setQualityTrimParams(20, 18)

        # Create an associative item.
        a_item = self.proj.associateItems(
            (self.proj.getItemById(2), self.proj.getItemById(3)), 'new item'
        )

        # Set some properties of the associative item and its children.
        a_item.setNotes('sample notes')
        a_item.setConsensusSequence('AATTAATTGGCC', 'AA TT AA TT GGCC')
        a_item.setUseSequence(True)
        child1 = a_item.getChildren()[0]
        child2 = a_item.getChildren()[1]
        child1name = child1.getName()
        child2name = child2.getName()
        child1.setConsensusSequence('CATCATGATCATTAGTAC', 'CATCATGATCAT TAGTAC')
        child2.setIsReverse(True)

        # Set sequences and notes for the remaining items.
        # item 0: ''
        # item 1: 'AT'
        # item 3: 'ATATAT'
        for (cnt, item) in enumerate(self.proj):
            if item.isFile():
                item.setConsensusSequence('AT' * cnt, 'AT' * cnt)
                item.setNotes(str(cnt))

        self.proj.saveProjectFile()
        self.proj.clearProject()
        self.proj.loadProjectFile(tmpfpath)
        
        # Test if the project properties saved properly.
        self.assertFalse(self.proj.isProjectEmpty())
        self.assertEqual(self.proj.getFwdTraceSearchStr(), '_F_')
        self.assertEqual(self.proj.getRevTraceSearchStr(), '_R_')
        self.assertEqual(self.proj.getTraceFileDir(), 'tracedir')
        self.assertEqual(
            self.proj.getAbsTraceFileDir(), os.path.join(tmpdir, 'tracedir')
        )
        self.assertEqual(newfontstr, self.proj.getFont().to_string())

        # Test if the consensus settings saved properly.
        csettings = self.proj.getConsensSeqSettings()
        self.assertEqual(csettings.getMinConfScore(), 20)
        self.assertEqual(csettings.getConsensusAlgorithm(), 'legacy')
        self.assertFalse(csettings.getTrimConsensus())
        self.assertTrue(csettings.getTrimPrimers())
        self.assertEqual(csettings.getPrimerMatchThreshold(), 0.2)
        self.assertEqual(csettings.getForwardPrimer(), 'AAAT')
        self.assertEqual(csettings.getReversePrimer(), 'GGGC')
        self.assertTrue(csettings.getTrimEndGaps())
        self.assertFalse(csettings.getDoQualityTrim())
        self.assertEqual(csettings.getQualityTrimParams(), (20, 18))

        self.proj.setTraceFileDir('.')
        for fname in self.tracefiles:
            self.assertTrue(
                self.proj.isFileInProject(os.path.join(tmpdir, fname))
            )

        self._checkProjectItems(self.proj, child1name, child2name)

        # Remove the temporary directory.
        shutil.rmtree(tmpdir)

    def test_readVer9Project(self):
        """
        Tests reading a version 0.9 project file and conversion to 1.0.0
        format.
        """
        self.proj.loadProjectFile('test_data/test_project-0.9.str')
        
        # Test if the project properties are correct.
        self.assertFalse(self.proj.isProjectEmpty())
        self.assertEqual(self.proj.getFwdTraceSearchStr(), '_F_')
        self.assertEqual(self.proj.getRevTraceSearchStr(), '_R_')
        self.assertEqual(self.proj.getTraceFileDir(), 'tracedir')
        self.assertEqual(
            self.proj.getAbsTraceFileDir(),
            os.path.join(os.getcwd(), 'test_data/tracedir')
        )
        self.assertEqual(
            getDefaultFont().to_string(), self.proj.getFont().to_string()
        )

        # Test if the consensus settings are correct.
        csettings = self.proj.getConsensSeqSettings()
        self.assertEqual(csettings.getMinConfScore(), 20)
        self.assertEqual(csettings.getConsensusAlgorithm(), 'legacy')
        self.assertFalse(csettings.getTrimConsensus())
        self.assertTrue(csettings.getTrimPrimers())
        self.assertEqual(csettings.getPrimerMatchThreshold(), 0.2)
        self.assertEqual(csettings.getForwardPrimer(), 'AAAT')
        self.assertEqual(csettings.getReversePrimer(), 'GGGC')
        self.assertTrue(csettings.getTrimEndGaps())
        self.assertFalse(csettings.getDoQualityTrim())
        self.assertEqual(csettings.getQualityTrimParams(), (20, 18))

        self.proj.setTraceFileDir('.')
        for fname in self.tracefiles:
            self.assertTrue(self.proj.isFileInProject('test_data/' + fname))

        self._checkProjectItems(self.proj, 'fwd2.ztr', 'rev2.ztr')

    def test_readVer8Project(self):
        """
        Tests reading a version 0.8 project file and conversion to 1.0.0
        format.
        """
        self.proj.loadProjectFile('test_data/test_project-0.8.str')
        
        # Test if the project properties are correct.
        self.assertFalse(self.proj.isProjectEmpty())
        self.assertEqual(self.proj.getFwdTraceSearchStr(), '_F_')
        self.assertEqual(self.proj.getRevTraceSearchStr(), '_R_')
        self.assertEqual(self.proj.getTraceFileDir(), 'tracedir')
        self.assertEqual(
            self.proj.getAbsTraceFileDir(),
            os.path.join(os.getcwd(), 'test_data/tracedir')
        )
        self.assertEqual(
            getDefaultFont().to_string(), self.proj.getFont().to_string()
        )

        # Test if the consensus settings are correct.
        csettings = self.proj.getConsensSeqSettings()
        self.assertEqual(csettings.getMinConfScore(), 20)
        self.assertEqual(csettings.getConsensusAlgorithm(), 'legacy')
        self.assertFalse(csettings.getTrimConsensus())
        self.assertFalse(csettings.getTrimPrimers())
        self.assertEqual(csettings.getPrimerMatchThreshold(), 0.8)
        self.assertEqual(csettings.getForwardPrimer(), '')
        self.assertEqual(csettings.getReversePrimer(), '')
        self.assertFalse(csettings.getTrimEndGaps())
        self.assertFalse(csettings.getDoQualityTrim())
        self.assertEqual(csettings.getQualityTrimParams(), (10, 6))

        self.proj.setTraceFileDir('.')
        for fname in self.tracefiles:
            self.assertTrue(self.proj.isFileInProject('test_data/' + fname))

        self._checkProjectItems(self.proj, 'fwd2.ztr', 'rev2.ztr')

