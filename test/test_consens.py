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


from seqtrace.core.consens import *
from seqtrace.core.sequencetrace import SequenceTrace

import unittest



class TestConsensus(unittest.TestCase):
    def setUp(self):
        self.settings = ConsensSeqSettings()

        # set up some simple sequence trace data
        self.seqt1 = SequenceTrace()
        self.seqt2 = SequenceTrace()
        self.seqt1.basecalls = 'AAGCTACCTGACATGATTTACG'
        self.seqt2.basecalls = 'GCTCCTGACACGAATTAC'
        # alignment of the above:   'AAGCTACCTGACATGATTTACG'
        #                           '--GCT-CCTGACACGAATTAC-'

        #                    A  A   G   C   T   A  C   C   T   G   A   C   A   T   G   A   T   T   T   A   C   G
        self.seqt1.bcconf = [5, 4, 20, 24, 34, 12, 8, 30, 32, 16, 34, 40, 52, 61, 61, 61, 28, 61, 46, 32, 12, 24]
        #                           G   C   T       C  C   T   G   A   C   A   C   G   A   A   T   T   A   C
        self.seqt2.bcconf = [      20, 24, 34,     12, 8, 30, 16, 34, 40, 52, 42, 61, 61, 30, 61, 46, 32, 12    ]
        #print len(self.seqt1.getBaseCalls())
        #print len(self.seqt1.bcconf)

    # Test the basic ConsensSeqBuilder operations.
    def test_consensus(self):
        cons = ConsensSeqBuilder((self.seqt1,))

        self.assertRaises(ConsensSeqBuilderError, cons.setConsensSequence, 'AATT')

        cons.setConsensSequence('   AAAAAAAATTTTTTGGCC ')
        self.assertEqual(cons.getConsensus(), '   AAAAAAAATTTTTTGGCC ')

        self.assertEqual(cons.getCompactConsensus(), 'AAAAAAAATTTTTTGGCC')

        self.assertEqual(cons.getNumSeqs(), 1)

    # Test consensus sequence construction on a single sequence trace.
    def test_singleConsensus(self):
        self.settings.setDoAutoTrim(False)

        self.settings.setMinConfScore(30)
        cons = ConsensSeqBuilder((self.seqt1,), self.settings)
        self.assertEqual(cons.getConsensus(), '    TNNCTNACATGANTTA  ')

        self.settings.setMinConfScore(20)
        cons.makeConsensusSequence()
        self.assertEqual(cons.getConsensus(), '  GCTNNCTNACATGATTTANG')

        self.settings.setMinConfScore(5)
        cons.makeConsensusSequence()
        self.assertEqual(cons.getConsensus(), 'ANGCTACCTGACATGATTTACG')

        self.settings.setMinConfScore(61)
        cons.makeConsensusSequence()
        self.assertEqual(cons.getConsensus(), '             TGANT    ')

    # Test consensus sequence construction with two (forward/reverse) sequence traces.
    def test_doubleConsensus(self):
        self.settings.setDoAutoTrim(False)

        cons = ConsensSeqBuilder((self.seqt1, self.seqt2), self.settings)

        # verify the alignment is correct
        self.assertEqual(cons.getAlignedSequence(0), 'AAGCTACCTGACATGATTTACG')
        self.assertEqual(cons.getAlignedSequence(1), '--GCT-CCTGACACGAATTAC-')

        #                    A  A   G   C   T   A  C   C   T   G   A   C   A   T   G   A   T   T   T   A   C   G
        #                   [5, 4, 20, 24, 34, 12, 8, 30, 32, 16, 34, 40, 52, 61, 61, 61, 28, 61, 46, 32, 12, 24]
        #                           G   C   T       C  C   T   G   A   C   A   C   G   A   A   T   T   A   C
        #                   [      20, 24, 34,     12, 8, 30, 16, 34, 40, 52, 42, 61, 61, 30, 61, 46, 32, 12    ]

        # run each set of tests with seqt1 first, then with seqt2 first
        for cnt in range(2):
            if cnt == 1:
                # swap the sequence trace order on the second pass through the loop
                cons = ConsensSeqBuilder((self.seqt2, self.seqt1), self.settings)

            # conflicting bases: one pair unresolvable, the other resolvable; no gaps filled
            self.settings.setMinConfScore(30)
            cons.makeConsensusSequence()
            self.assertEqual(cons.getConsensus(), '    TNNCTNACANGAATTA  ')
    
            # conflicting bases: neither pair resolvable; one gap filled
            self.settings.setMinConfScore(20)
            cons.makeConsensusSequence()
            self.assertEqual(cons.getConsensus(), '  GCTNNCTNACANGANTTANG')
    
            # two gaps filled
            self.settings.setMinConfScore(12)
            cons.makeConsensusSequence()
            self.assertEqual(cons.getConsensus(), '  GCTACCTGACANGANTTACG')
    
            # three gaps filled
            self.settings.setMinConfScore(5)
            cons.makeConsensusSequence()
            self.assertEqual(cons.getConsensus(), 'ANGCTACCTGACANGANTTACG')

    # Test the automatic trimming of sequence ends.
    def test_autoTrim(self):
        # Test consensus construction with end trimming by testing a bunch of different
        # confscore/windowsize/num good bases combinations, including special cases.
        self.settings.setMinConfScore(30)
        self.settings.setDoAutoTrim(True)
        self.settings.setAutoTrimParams(6, 6)
        cons = ConsensSeqBuilder((self.seqt1,), self.settings)
        self.assertEqual(cons.getConsensus(), '          ACATGA      ')

        self.settings.setAutoTrimParams(6, 5)
        cons.makeConsensusSequence()
        self.assertEqual(cons.getConsensus(), '       CTNACATGANTTA  ')

        self.settings.setAutoTrimParams(6, 4)
        cons.makeConsensusSequence()
        self.assertEqual(cons.getConsensus(), '      NCTNACATGANTTA  ')

        self.settings.setAutoTrimParams(6, 3)
        cons.makeConsensusSequence()
        self.assertEqual(cons.getConsensus(), '    TNNCTNACATGANTTA  ')

        self.settings.setAutoTrimParams(7, 6)
        cons.makeConsensusSequence()
        self.assertEqual(cons.getConsensus(), '       CTNACATGANTTA  ')

        self.settings.setAutoTrimParams(7, 7)
        cons.makeConsensusSequence()
        self.assertEqual(cons.getConsensus(), '                      ')

        self.settings.setMinConfScore(5)
        self.settings.setAutoTrimParams(3, 2)
        cons.makeConsensusSequence()
        self.assertEqual(cons.getConsensus(), 'ANGCTACCTGACATGATTTACG')

        self.settings.setAutoTrimParams(3, 3)
        cons.makeConsensusSequence()
        self.assertEqual(cons.getConsensus(), '  GCTACCTGACATGATTTACG')

        self.settings.setMinConfScore(20)
        self.settings.setAutoTrimParams(3, 2)
        cons.makeConsensusSequence()
        self.assertEqual(cons.getConsensus(), '  GCTNNCTNACATGATTTANG')

        self.settings.setAutoTrimParams(3, 3)
        cons.makeConsensusSequence()
        self.assertEqual(cons.getConsensus(), '  GCTNNCTNACATGATTTA  ')

        # now some special cases: window size of 1
        self.settings.setMinConfScore(30)
        self.settings.setAutoTrimParams(1, 1)
        cons.makeConsensusSequence()
        self.assertEqual(cons.getConsensus(), '    TNNCTNACATGANTTA  ')

        # window size equal to the sequence length, base count 1 more than the number of good bases
        self.settings.setAutoTrimParams(22, 13)
        cons.makeConsensusSequence()
        self.assertEqual(cons.getConsensus(), '                      ')

        # window size equal to the sequence length, base count exactly equal to the number of good bases
        self.settings.setAutoTrimParams(22, 12)
        cons.makeConsensusSequence()
        self.assertEqual(cons.getConsensus(), '    TNNCTNACATGANTTA  ')


class TestModifiableConsensus(unittest.TestCase):
    def setUp(self):
        # set up some simple sequence trace data
        self.seqt1 = SequenceTrace()
        self.seqt1.basecalls = 'AAGCTACCTGACATGATTTACG'

        #                    A  A   G   C   T   A  C   C   T   G   A   C   A   T   G   A   T   T   T   A   C   G
        self.seqt1.bcconf = [5, 4, 20, 24, 34, 12, 8, 30, 32, 16, 34, 40, 52, 61, 61, 61, 28, 61, 46, 32, 12, 24]

        self.settings = ConsensSeqSettings()
        self.settings.setDoAutoTrim(False)
        self.settings.setMinConfScore(4)
        self.cons = ModifiableConsensSeqBuilder((self.seqt1,), self.settings)

        # delete test cases: [start index, end index, result]
        self.del_tests = [
                [0, 0, ' AGCTACCTGACATGATTTACG'],   # one base from the beginning
                [21, 21, ' AGCTACCTGACATGATTTAC '], # one base from the end
                [4, 10, ' AGC       CATGATTTAC '],  # several from the middle 
                [0, 21, '                      ']   # the entire sequence
                ]

        # modify test cases: [start index, end index, replacement, result]
        self.modify_tests = [
                [0, 0, 'C', 'CAGCTACCTGACATGATTTACG'],      # one base from the beginning
                [21, 21, 'A', 'CAGCTACCTGACATGATTTACA'],    # one base from the end
                [7, 10, 'TCAT', 'CAGCTACTCATCATGATTTACA'],  # several from the middle 
                [0, 21, 'AATTGGCCTGACTGACGACTAA', 'AATTGGCCTGACTGACGACTAA']   # the entire sequence
                ]

    def test_deleteBases(self):
        for testcase in self.del_tests:
            self.cons.deleteBases(testcase[0], testcase[1])
            self.assertEqual(self.cons.getConsensus(), testcase[2])

        # test again, with the start and end indexes swapped
        self.cons.makeConsensusSequence()
        for testcase in self.del_tests:
            self.cons.deleteBases(testcase[1], testcase[0])
            self.assertEqual(self.cons.getConsensus(), testcase[2])

    def test_modifyBases(self):
        for testcase in self.modify_tests:
            self.cons.modifyBases(testcase[0], testcase[1], testcase[2])
            self.assertEqual(self.cons.getConsensus(), testcase[3])

        # test again, with the start and end indexes swapped
        self.cons.makeConsensusSequence()
        for testcase in self.modify_tests:
            self.cons.modifyBases(testcase[0], testcase[1], testcase[2])
            self.assertEqual(self.cons.getConsensus(), testcase[3])

    def test_undoRedo(self):
        # apply all of the delete test cases
        for testcase in self.del_tests:
            self.cons.deleteBases(testcase[0], testcase[1])

        # now undo them all and test the results
        for cnt in range(len(self.del_tests) - 1, -1, -1):
            self.assertEqual(self.cons.getConsensus(), self.del_tests[cnt][2])
            self.cons.undo()
        # make sure we ended on the starting sequence
        self.assertEqual(self.cons.getConsensus(), self.seqt1.getBaseCalls())

        # now redo them all and test the results
        for testcase in self.del_tests:
            self.cons.redo()
            self.assertEqual(self.cons.getConsensus(), testcase[2])

        # apply all of the modify test cases
        self.cons.makeConsensusSequence()
        for testcase in self.modify_tests:
            self.cons.modifyBases(testcase[0], testcase[1], testcase[2])

        # now undo them all and test the results
        for cnt in range(len(self.modify_tests) - 1, -1, -1):
            self.assertEqual(self.cons.getConsensus(), self.modify_tests[cnt][3])
            self.cons.undo()
        # make sure we ended on the starting sequence
        self.assertEqual(self.cons.getConsensus(), self.seqt1.getBaseCalls())

        # now redo them all and test the results
        for testcase in self.modify_tests:
            self.cons.redo()
            self.assertEqual(self.cons.getConsensus(), testcase[3])

        # finally, test recalcConsensusSequence()
        oldseq = self.cons.getConsensus()
        self.cons.recalcConsensusSequence()
        self.assertEqual(self.cons.getConsensus(), self.seqt1.getBaseCalls())
        self.cons.undo()
        self.assertEqual(self.cons.getConsensus(), oldseq)
        self.cons.redo()
        self.assertEqual(self.cons.getConsensus(), self.seqt1.getBaseCalls())





if __name__ == '__main__':
    #unittest.main()
    suite = unittest.defaultTestLoader.loadTestsFromName(__name__)
    unittest.TextTestRunner(verbosity=2).run(suite)

