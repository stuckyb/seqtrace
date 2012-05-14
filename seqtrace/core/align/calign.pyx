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
"""
This module is functionally identical to pyalign.py, except that the core pairwise alignment
algorithm, doAlignment(), is implemented mostly in C (via Cython).  Performance tests indicate
that this improves the average time (n=1000) to calculate a pairwise alignment by more than
88% compared to the pure Python implementation.  In other words, alignments run in 11% of the
time taken by the pure Python implementation, or just over 9 times faster.

The code has also been thoroughly tested to ensure that it does not leak memory.
"""



# declarations for the C stdlib dynamic memory functions
cdef extern from 'stdlib.h':
    void* malloc(size_t size)
    void* calloc(size_t size1, size_t size2)
    void* free(void* ptr)



class PairwiseAlignment:
    def __init__(self):
        # substitution score matrix
        self.svals = {
        'A': {'A': 1, 'T': -1, 'G': -1, 'C': -1, 'N': 0},
        'T': {'A': -1, 'T': 1, 'G': -1, 'C': -1, 'N': 0},
        'G': {'A': -1, 'T': -1, 'G': 1, 'C': -1, 'N': 0},
        'C': {'A': -1, 'T': -1, 'G': -1, 'C': 1, 'N': 0},
        'N': {'A': 0, 'T': 0, 'G': 0, 'C': 0, 'N': 0}
        }

        # gap penalty
        self.gapp = -1

        self.seq1 = ''
        self.seq2 = ''

        self.seq1aligned = ''
        self.seq2aligned = ''
        self.seq1indexed = []
        self.seq2indexed = []

        self.score = 0

    def setGapPenalty(self, gap_penalty):
        self.gapp = gap_penalty

    def getGapPenalty(self):
        return self.gapp

    def setSequences(self, sequence1, sequence2):
        self.seq1 = sequence1
        self.seq2 = sequence2

    def getSequences(self):
        return (self.seq1, self.seq2)

    def getAlignedSequences(self):
        return (self.seq1aligned, self.seq2aligned)

    def getAlignedSeqIndexes(self):
        return (self.seq1indexed, self.seq2indexed)

    def getAlignmentScore(self):
        return self.score

    def doAlignment(self):
        """ Implements the Needleman-Wunsch pairwise sequence alignment algorithm.
        
        Most of the implementation is in C (using Cython).  2D C arrays (arrays
        of arrays) are dynamically allocated for the score and traceback matrices.
        All of the core algorithm should run as "pure" C, except for lookups to the
        substitution cost matrix.
        """

        cdef int seq1len = len(self.seq1)
        cdef int seq2len = len(self.seq2)

        # 1st subscript = sequence 1,
        # 2nd subscript = sequence 2
        cdef int cnt
    
        cdef int** scores
        cdef char** tracebk
    
        # allocate the 2D scores array, initialized to all zeros
        scores = <int**>malloc((seq1len + 1) * sizeof(int*));
        if not scores:
            raise MemoryError('Unable to malloc() alignment data structures.')
        for cnt in range(seq1len + 1):
            scores[cnt] = <int*>calloc(seq2len + 1, sizeof(int));
            if not scores[cnt]:
                raise MemoryError('Unable to calloc() alignment data structures.')
        
        # allocate the 2D traceback array
        tracebk = <char**>malloc((seq1len + 1) * sizeof(char*));
        if not tracebk:
            raise MemoryError('Unable to malloc() alignment data structures.')
        for cnt in range(seq1len + 1):
            tracebk[cnt] = <char*>calloc(seq2len + 1, sizeof(char));
            if not tracebk[cnt]:
                raise MemoryError('Unable to malloc() alignment data structures.')
    
        # initialize the traceback matrix
        for cnt in range(1, seq1len+1):
            tracebk[cnt][0] = 'l'
        for cnt in range(1, seq2len+1):
            tracebk[0][cnt] = 'u'
        #print tracebk
        
        cdef int i, j, sdiag, sup, sleft
        cdef int gapp = self.gapp

        # calculate the scores for the alignment matrix and directional
        # pointers for the traceback matrix
        for i in range(1, seq1len+1):
            for j in range(1, seq2len+1):
                # calculate the maximum subscores for this position
                sdiag = scores[i-1][j-1] + self.svals[self.seq1[i-1]][self.seq2[j-1]]
                sup = scores[i][j-1] + gapp
                sleft = scores[i-1][j] + gapp
                # do not assess a penalty for end gaps
                if j == seq2len:
                    sleft -= gapp
                if i == seq1len:
                    sup -= gapp
                # record maximum subscore and direction
                if (sdiag >= sup) and (sdiag >= sleft):
                    tracebk[i][j] = 'd'
                    scores[i][j] = sdiag
                elif (sup >= sdiag) and (sup >= sleft):
                    tracebk[i][j] = 'u'
                    scores[i][j] = sup
                else:
                    tracebk[i][j] = 'l'
                    scores[i][j] = sleft

        self.score = scores[seq1len][seq2len]
        
        # follow the directional pointers in the traceback matrix
        # to generate an optimal alignment
        seq1a = list()
        seq2a = list()
        seq1aindex = list()
        seq2aindex = list()
        i = seq1len
        j = seq2len
        while (i > 0) or (j > 0):
            if tracebk[i][j] == 'd':
                seq1a.append(self.seq1[i-1])
                seq2a.append(self.seq2[j-1])
                seq1aindex.append(i-1)
                seq2aindex.append(j-1)
                i -= 1
                j -= 1
            elif tracebk[i][j] == 'u':
                seq1a.append('-')
                seq2a.append(self.seq2[j-1])
                seq1aindex.append(-1)
                seq2aindex.append(j-1)
                j -= 1
            else:
                seq1a.append(self.seq1[i-1])
                seq2a.append('-')
                seq1aindex.append(i-1)
                seq2aindex.append(-1)
                i -= 1
        
        seq1a.reverse()
        seq2a.reverse()
        seq1aindex.reverse()
        seq2aindex.reverse()
        self.seq1aligned = ''.join(seq1a)
        self.seq2aligned = ''.join(seq2a)
        self.seq1indexed = seq1aindex
        self.seq2indexed = seq2aindex

        # free the memory for the 2D scores array
        for cnt in range(seq1len + 1):
            free(scores[cnt]);
        free(scores);
        
        # free the memory for the 2D traceback array
        for cnt in range(seq1len + 1):
            free(tracebk[cnt]);
        free(tracebk);

        # go through the sequence indexes and mark the gaps with (-nextbaseindex - 1)
        # so that the index lookups return a more informative value
        seq1gv = seq2gv = -1
        for cnt in range(len(self.seq1indexed)):
            if self.seq1indexed[cnt] == -1:
                self.seq1indexed[cnt] = seq1gv
            else:
                seq1gv -= 1
            if self.seq2indexed[cnt] == -1:
                self.seq2indexed[cnt] = seq2gv
            else:
                seq2gv -= 1

        #print self.seq1indexed

