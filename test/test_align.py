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


import seqtrace.core.align as align
import seqtrace.core.align.pyalign as pyalign
try:
    # try to load the compiled C alignment module
    import seqtrace.core.align.calign as calign
except ImportError:
    # if that fails, make calign a dummy variable, causing the tests to fail
    # but preventing the script from crashing due to a failed import
    calign = None

import unittest



class TestPairwiseAlignment(unittest.TestCase):
    """
    Tests the pairwise alignment code with the generic package reference.
    """
    def setUp(self):
        self.align = align.PairwiseAlignment()

    def test_init(self):
        self.assertEquals(self.align.getSequences(), ('', ''))
        self.assertEquals(self.align.getAlignedSequences(), ('', ''))
        self.assertEquals(self.align.getAlignedSeqIndexes(), ([], []))

        self.align.doAlignment()
        self.assertEquals(self.align.getAlignedSequences(), ('', ''))
        self.assertEquals(self.align.getAlignedSeqIndexes(), ([], []))

    def test_scoringMatrix(self):
        """
        Runs some consistency tests on the alignment scoring matrix.
        """
        allbases = ('A', 'T', 'G', 'C', 'W', 'S', 'M', 'K', 'R', 'Y', 'B', 'D', 'H', 'V', 'N')

        # Get the scoring matrix.
        sm = self.align.svals

        # The average probability of an exact match across all columns and rows of the
        # matrix is the same (0.25), so all rows and columns should have the same sum,
        # (0.25 * 12 - 6) * 15 = -45.  Checking the row/column sums will detect
        # virtually all accidental mistakes, such as swapping two numbers or using
        # the wrong value somewhere.  It is of course possible to construct wrong
        # matrices that this test will not catch, but it is extremely unlikely that
        # these cases would arise by accident!
        for base in ('A', 'T', 'G', 'C', 'W', 'S', 'M', 'K', 'R', 'Y', 'N'):
            # Check the row sum.
            self.assertEqual(sum(sm[base].values()), -45)

            # Check the column sum.
            total = 0
            for row in allbases:
                total += sm[row][base]

            self.assertEqual(total, -45)

        # Because of rounding errors when calculating the scores, these will be off
        # by 1 (i.e., -44 instead of -45).
        for base in ('B', 'D', 'H', 'V'):
            # Check the row sum.
            self.assertEqual(sum(sm[base].values()), -44)

            # Check the column sum.
            total = 0
            for row in allbases:
                total += sm[row][base]

            self.assertEqual(total, -44)

    def test_doAlignment(self):
        """
        Tests the Needleman-Wunsch pairwise alignment algorithm with a variety
        of test cases.
        """
        self.align.setGapPenalty(-6)

        # Define the test cases.  Each case is defined by a list with the elements
        # [sequence1, sequence2, alignedseq1, alignedseq2, alignscore].
        testcases = [
            # Sequences of different lengths that align perfectly.
            # CATGCATTTATTATAAGGTT
            # CATGCATTTATTATAAGG--
            ['CATGCATTTATTATAAGGTT', 'CATGCATTTATTATAAGG', 'CATGCATTTATTATAAGGTT', 'CATGCATTTATTATAAGG--', 108],

            # --TGCATTTATTATAAGGTT
            # CATGCATTTATTATAAGGTT
            ['TGCATTTATTATAAGGTT', 'CATGCATTTATTATAAGGTT', '--TGCATTTATTATAAGGTT', 'CATGCATTTATTATAAGGTT', 108],

            # Sequences of different lengths with 2 mismatched bases and 6 fully ambiguous bases.
            # CNTGCANCCATTATNAGGTT
            # CNTGCANTTATTATANGG--
            ['CNTGCANCCATTATNAGGTT', 'CNTGCANTTATTATANGG', 'CNTGCANCCATTATNAGGTT', 'CNTGCANTTATTATANGG--', 48],

            # CNTGCANCCATTATNAGGTT
            # CNTGCANTTATTAT-AGNT-
            ['CNTGCANCCATTATNAGGTT', 'CNTGCANTTATTATAGNT', 'CNTGCANCCATTATNAGGTT', 'CNTGCANTTATTAT-AGNT-', 51],

            # Sequences of different lengths with 2 mismatched bases.
            # CATGCATCCATTATAAGGTT
            # CATGCATTTATTATAAGG--
            ['CATGCATCCATTATAAGGTT', 'CATGCATTTATTATAAGG', 'CATGCATCCATTATAAGGTT', 'CATGCATTTATTATAAGG--', 84],

            # Sequences of the same length with 2 mismatched bases and 2 missing bases in the middle.
            # CAT--ATCCATTATAAGGTT
            # CATGCATTTATTATAAGG--
            ['CATATCCATTATAAGGTT', 'CATGCATTTATTATAAGG', 'CAT--ATCCATTATAAGGTT', 'CATGCATTTATTATAAGG--', 60],

            # Sequences that align with two end gaps, one internal gap, and one mismatch.
            # CATATCCAT-ATAAG---
            # --TGTCCATCATAAGGCA
            ['CATATCCATATAAG', 'TGTCCATCATAAGGCA', 'CATATCCAT-ATAAG---', '--TGTCCATCATAAGGCA', 54],

            # Sequences with partially ambiguous bases.  Tests several combinations of 1-
            # 2- and 3-base codes to verify that the bases are placed correctly.
            # CAWGCA-WTT-BTATAAGGTT
            # CATGSAMWTTATTATAM-GT-
            ['CAWGCAWTTBTATAAGGTT', 'CATGSAMWTTATTATAMGT', 'CAWGCA-WTT-BTATAAGGTT', 'CATGSAMWTTATTATAM-GT-', 52]
            ]

        # Define the indices for the test sequences and results.
        seq1 = 0
        seq2 = 1
        alignedseq1 = 2
        alignedseq2 = 3
        score = 4

        # Run all of the test cases twice, switching the sequence order the
        # second time around.
        for i in (0,1):
            # The second time through, reverse the order of the sequences.
            if i == 1:
                seq1 = 1
                seq2 = 0
                alignedseq1 = 3
                alignedseq2 = 2

            # Run each test case.
            for case in testcases:
                self.align.setSequences(case[seq1], case[seq2])
                self.align.doAlignment()
                #print self.align.getAlignedSequences()[0]
                #print self.align.getAlignedSequences()[1]
                self.assertEquals(self.align.getAlignedSequences(), (case[alignedseq1], case[alignedseq2]))
                self.assertEquals(self.align.getAlignmentScore(), case[score])

        # Now run a few tests with different gap penalties.
        # CATGCATCC--ATTATAAGGTT
        # CATGCAT--TTATTATAAGG--
        self.align.setGapPenalty(0)
        self.align.setSequences('CATGCATCCATTATAAGGTT', 'CATGCATTTATTATAAGG')
        self.align.doAlignment()
        self.assertEquals(self.align.getAlignedSequences(), ('CATGCATCC--ATTATAAGGTT', 'CATGCAT--TTATTATAAGG--'))
        self.assertEquals(self.align.getAlignmentScore(), 96)

        # Different sequences with the same gap penalty.
        # CAT--ATCC--ATTATAAGGTT
        # CATGCAT--TTATTATAAGG--
        self.align.setGapPenalty(0)
        self.align.setSequences('CATATCCATTATAAGGTT', 'CATGCATTTATTATAAGG')
        self.align.doAlignment()
        self.assertEquals(self.align.getAlignedSequences(), ('CAT--ATCC--ATTATAAGGTT', 'CATGCAT--TTATTATAAGG--'))
        self.assertEquals(self.align.getAlignmentScore(), 84)

        # Using the sequences in the previous tests, test an extreme gap penalty.
        # --CATATCCATTATAAGGTT
        # CATGCATTTATTATAAGG--
        self.align.setGapPenalty(-36)
        self.align.setSequences('CATATCCATTATAAGGTT', 'CATGCATTTATTATAAGG')
        self.align.doAlignment()
        self.assertEquals(self.align.getAlignedSequences(), ('--CATATCCATTATAAGGTT', 'CATGCATTTATTATAAGG--'))
        self.assertEquals(self.align.getAlignmentScore(), 36)

    def test_getAlignedSeqIndexes(self):
        # sequences of the same length with 2 mismatched bases and 2 missing bases in the middle,
        # same as in doAlignment() tests
        self.align.setGapPenalty(0)
        self.align.setSequences('CATATCCATTATAAGGTT', 'CATGCATTTATTATAAGG')
        self.align.doAlignment()
        #print self.align.getAlignedSeqIndexes()[1]
        self.assertEquals(self.align.getAlignedSeqIndexes()[0],
                [0, 1, 2, -4, -4, 3, 4, 5, 6, -8, -8, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17])
        self.assertEquals(self.align.getAlignedSeqIndexes()[1],
                [0, 1, 2, 3, 4, 5, 6, -8, -8, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, -19, -19])


class TestPyPairwiseAlignment(TestPairwiseAlignment):
    """
    Tests the pairwise alignment code with the native Python implementation.
    """
    def setUp(self):
        self.align = pyalign.PairwiseAlignment()


class TestCPairwiseAlignment(TestPairwiseAlignment):
    """
    Tests the pairwise alignment code with the C (Cython) implementation.
    """
    def setUp(self):
        self.align = calign.PairwiseAlignment()




if __name__ == '__main__':
    #unittest.main()
    suite = unittest.defaultTestLoader.loadTestsFromName(__name__)
    unittest.TextTestRunner(verbosity=2).run(suite)

