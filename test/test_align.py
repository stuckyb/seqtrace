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
    """ Tests the pairwise alignment code with the generic package reference. """

    def setUp(self):
        self.align = align.PairwiseAlignment()

    def test_init(self):
        self.assertEquals(self.align.getSequences(), ('', ''))
        self.assertEquals(self.align.getAlignedSequences(), ('', ''))
        self.assertEquals(self.align.getAlignedSeqIndexes(), ([], []))

        self.align.doAlignment()
        self.assertEquals(self.align.getAlignedSequences(), ('', ''))
        self.assertEquals(self.align.getAlignedSeqIndexes(), ([], []))

    def test_doAlignment(self):
        self.align.setGapPenalty(-1)

        # sequences of different lengths that align perfectly
        self.align.setSequences('CATGCATTTATTATAAGGTT', 'CATGCATTTATTATAAGG')
        self.align.doAlignment()
        self.assertEquals(self.align.getAlignedSequences(), ('CATGCATTTATTATAAGGTT', 'CATGCATTTATTATAAGG--'))
        self.assertEquals(self.align.getAlignmentScore(), 18)

        self.align.setSequences('TGCATTTATTATAAGGTT', 'CATGCATTTATTATAAGGTT')
        self.align.doAlignment()
        self.assertEquals(self.align.getAlignedSequences(), ('--TGCATTTATTATAAGGTT', 'CATGCATTTATTATAAGGTT'))
        self.assertEquals(self.align.getAlignmentScore(), 18)

        # sequences of different lengths with 2 mismatched bases and 6 ambiguous bases
        self.align.setSequences('CNTGCANCCATTATNAGGTT', 'CNTGCANTTATTATANGG')
        self.align.doAlignment()
        self.assertEquals(self.align.getAlignedSequences(), ('CNTGCANCCATTATNAGGTT', 'CNTGCANTTATTATANGG--'))
        self.assertEquals(self.align.getAlignmentScore(), 10)

        # sequences of different lengths with 2 mismatched bases
        self.align.setSequences('CATGCATCCATTATAAGGTT', 'CATGCATTTATTATAAGG')
        self.align.doAlignment()
        self.assertEquals(self.align.getAlignedSequences(), ('CATGCATCCATTATAAGGTT', 'CATGCATTTATTATAAGG--'))
        self.assertEquals(self.align.getAlignmentScore(), 14)

        self.align.setGapPenalty(0)
        self.align.setSequences('CATGCATCCATTATAAGGTT', 'CATGCATTTATTATAAGG')
        self.align.doAlignment()
        self.assertEquals(self.align.getAlignedSequences(), ('CATGCATCC--ATTATAAGGTT', 'CATGCAT--TTATTATAAGG--'))
        self.assertEquals(self.align.getAlignmentScore(), 16)

        # sequences of the same length with 2 mismatched bases and 2 missing bases in the middle
        self.align.setGapPenalty(-1)
        self.align.setSequences('CATATCCATTATAAGGTT', 'CATGCATTTATTATAAGG')
        self.align.doAlignment()
        self.assertEquals(self.align.getAlignedSequences(), ('CAT--ATCCATTATAAGGTT', 'CATGCATTTATTATAAGG--'))
        self.assertEquals(self.align.getAlignmentScore(), 10)

        self.align.setGapPenalty(0)
        self.align.setSequences('CATATCCATTATAAGGTT', 'CATGCATTTATTATAAGG')
        self.align.doAlignment()
        self.assertEquals(self.align.getAlignedSequences(), ('CAT--ATCC--ATTATAAGGTT', 'CATGCAT--TTATTATAAGG--'))
        self.assertEquals(self.align.getAlignmentScore(), 14)

        # using the sequences in the previous tests, test an extreme gap penalty
        self.align.setGapPenalty(-6)
        self.align.setSequences('CATATCCATTATAAGGTT', 'CATGCATTTATTATAAGG')
        self.align.doAlignment()
        #print self.align.getAlignmentScore()
        #print self.align.getAlignedSequences()[0]
        #print self.align.getAlignedSequences()[1]
        self.assertEquals(self.align.getAlignedSequences(), ('--CATATCCATTATAAGGTT', 'CATGCATTTATTATAAGG--'))
        self.assertEquals(self.align.getAlignmentScore(), 6)

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
    """ Tests the pairwise alignment code with the native Python implementation. """

    def setUp(self):
        self.align = pyalign.PairwiseAlignment()


class TestCPairwiseAlignment(TestPairwiseAlignment):
    """ Tests the pairwise alignment code with the C (Cython) implementation. """

    def setUp(self):
        self.align = calign.PairwiseAlignment()






if __name__ == '__main__':
    #unittest.main()
    suite = unittest.defaultTestLoader.loadTestsFromName(__name__)
    unittest.TextTestRunner(verbosity=2).run(suite)

