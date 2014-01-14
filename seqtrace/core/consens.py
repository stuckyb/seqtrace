# Copyright (C) 2014 Brian J. Stucky
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


from seqtrace.core.align import PairwiseAlignment
import seqtrace.core.sequencetrace as sequencetrace
from observable import Observable

import math
import re



class ConsensSeqSettingsError(Exception):
    pass

class ConsensSeqSettings(Observable):
    """
    Manages the settings that specify how SeqTrace calculates consensus sequences
    from matching forward and reverse traces.
    """
    def __init__(self):
        # Initialize all settings to default values.
        # Min. confidence score for consensus sequences.
        self.min_confscore = 30
        # Which consensus algorithm to use.
        self.consensus_algorithm = 'Bayesian'
        # Whether to trim the ends of the sequences.
        self.do_autotrim = True
        # Whether to trim the end gap regions from forward/reverse alignments.
        self.trim_endgaps = False
        # Whether to search for and trim primer sequences from the consensus sequence.
        self.trim_primers = False
        # The proportion of bases that must match to consider a primer alignment valid.
        self.primermatch = 0.8
        # The primer sequences.
        self.fwdprimer = ''
        self.revprimer = ''
        # Settings for automatic quality trimming.
        self.do_qualitytrim = True
        self.autotrim_winsize = 10 
        self.autotrim_basecnt = 8

        # A flag to indicate if a setAll() operation is in progress.
        self.notify_all = True

        # Initialize observable events.  The event "settings_change" is triggered whenever 
        # the value of any setting is changed.  The remaining events give notification of
        # more specific settings changes.
        self.defineObservableEvents(['settings_change', 'min_confscore_change',
            'autotrim_change', 'consensus_algorithm_change'])

    def copyFrom(self, settings):
        """
        Copies settings from another ConsensSeqSettings object to this object.
        """
        self.min_confscore = settings.getMinConfScore()
        self.consensus_algorithm = settings.getConsensusAlgorithm()
        self.do_autotrim = settings.getTrimConsensus()
        self.trim_endgaps = settings.getTrimEndGaps()
        self.trim_primers = settings.getTrimPrimers()
        self.primermatch = settings.getPrimerMatchThreshold()
        self.fwdprimer = settings.getForwardPrimer()
        self.revprimer = settings.getReversePrimer()
        self.do_qualitytrim = settings.getDoQualityTrim()
        self.autotrim_winsize = settings.getQualityTrimParams()[0]
        self.autotrim_basecnt = settings.getQualityTrimParams()[1]

    def setAll(self, min_confscore, consensus_algorithm, do_autotrim, trim_endgaps, trim_primers,
            primermatch_threshold, fwd_primer, rev_primer, do_qualitytrim, qualitytrim_params):
        self.notify_all = False
        self.change_made = False

        try:
            self.setMinConfScore(min_confscore)
            self.setConsensusAlgorithm(consensus_algorithm)
            self.setTrimConsensus(do_autotrim)
            self.setTrimEndGaps(trim_endgaps)
            self.setTrimPrimers(trim_primers)
            self.setPrimerMatchThreshold(primermatch_threshold)
            self.setForwardPrimer(fwd_primer)
            self.setReversePrimer(rev_primer)
            self.setDoQualityTrim(do_qualitytrim)
            self.setQualityTrimParams(*qualitytrim_params)
        finally:
            self.notify_all = True
            if self.change_made:
                self.notifyObservers('settings_change', ())

    def notifySettingsChanged(self):
        """
        Notifies listeners that one or more settings have changed.  If this method
        is called in the middle of setAll() operation, the notification is deferred
        until all settings have been changed.
        """
        if self.notify_all:
            self.notifyObservers('settings_change', ())
        else:
            self.change_made = True

    def getMinConfScore(self):
        return self.min_confscore

    def setMinConfScore(self, newval):
        if (newval > 61) or (newval < 1):
            raise ConsensSeqSettingsError('Confidence score values must be between 1 and 61, inclusive.')

        if self.min_confscore != newval:
            oldval = self.min_confscore
            self.min_confscore = newval
            self.notifyObservers('min_confscore_change', (self.min_confscore, oldval))
            self.notifySettingsChanged()

    def getConsensusAlgorithm(self):
        return self.consensus_algorithm

    def setConsensusAlgorithm(self, newval):
        if newval not in ('Bayesian', 'legacy'):
            raise ConsensSeqSettingsError('Invalid consensus algorithm specification.')

        if self.consensus_algorithm != newval:
            self.consensus_algorithm = newval
            self.notifyObservers('consensus_algorithm_change', ())
            self.notifySettingsChanged()

    def getTrimConsensus(self):
        return self.do_autotrim

    def setTrimConsensus(self, newval):
        if self.do_autotrim != newval:
            self.do_autotrim = newval
            self.notifyObservers('autotrim_change', ())
            self.notifySettingsChanged()

    def getDoQualityTrim(self):
        return self.do_qualitytrim

    def setDoQualityTrim(self, newval):
        if self.do_qualitytrim != newval:
            self.do_qualitytrim = newval
            self.notifyObservers('autotrim_change', ())
            self.notifySettingsChanged()

    def getQualityTrimParams(self):
        return (self.autotrim_winsize, self.autotrim_basecnt)

    def setQualityTrimParams(self, windowsize, basecount):
        if basecount > windowsize:
            raise ConsensSeqSettingsError('The number of correct base calls cannot exceed the window size.')

        if (self.autotrim_winsize != windowsize) or (self.autotrim_basecnt != basecount):
            self.autotrim_winsize = windowsize
            self.autotrim_basecnt = basecount
            self.notifyObservers('autotrim_change', ())
            self.notifySettingsChanged()

    def getTrimEndGaps(self):
        return self.trim_endgaps

    def setTrimEndGaps(self, newval):
        if self.trim_endgaps != newval:
            self.trim_endgaps = newval
            self.notifyObservers('autotrim_change', ())
            self.notifySettingsChanged()

    def getTrimPrimers(self):
        return self.trim_primers

    def setTrimPrimers(self, newval):
        if self.trim_primers != newval:
            self.trim_primers = newval
            self.notifyObservers('autotrim_change', ())
            self.notifySettingsChanged()

    def getPrimerMatchThreshold(self):
        return self.primermatch

    def setPrimerMatchThreshold(self, newval):
        if newval < 0 or newval > 1:
            raise ConsensSeqSettingsError('The primer match threshold must be between 0 and 1.')

        if self.primermatch != newval:
            self.primermatch = newval
            self.notifyObservers('autotrim_change', ())
            self.notifySettingsChanged()

    def getForwardPrimer(self):
        return self.fwdprimer

    def setForwardPrimer(self, primerseq):
        if self.fwdprimer != primerseq:
            self.fwdprimer = primerseq
            self.notifyObservers('autotrim_change', ())
            self.notifySettingsChanged()

    def getReversePrimer(self):
        return self.revprimer

    def setReversePrimer(self, primerseq):
        if self.revprimer != primerseq:
            self.revprimer = primerseq
            self.notifyObservers('autotrim_change', ())
            self.notifySettingsChanged()



class ConsensSeqBuilderError(Exception):
    pass

class ConsensSeqBuilder:
    """
    Constructs a consensus sequence from matching forward and reverse
    sequencing trace data.  After building the consensus sequence, or
    if only one sequence is provided, ConsensSeqBuilder can also perform
    finishing operations on the final sequence, such as automatic end
    quality trimming.
    """
    # Define a few class attributes that will act as constants.

    # All unambiguous nucleotide codes.
    bases = ('A', 'T', 'G', 'C')
    # All 2-nucleotide codes, along with the single bases they represent.
    bases2 = {
            'W': ('A', 'T'),
            'S': ('C', 'G'),
            'M': ('A', 'C'),
            'K': ('G', 'T'),
            'R': ('A', 'G'),
            'Y': ('C', 'T')}
    # All 3-nucleotide codes, along with the single bases they represent.
    bases3 = {
            'B': ('C', 'G', 'T'),
            'D': ('A', 'G', 'T'),
            'H': ('A', 'C', 'T'),
            'V': ('A', 'C', 'G')}
    # All valid nucleotide codes.
    allbases = ('A', 'T', 'G', 'C', 'W', 'S', 'M', 'K', 'R', 'Y', 'B', 'D', 'H', 'V', 'N')

    def __init__(self, sequencetraces, settings=None):
        self.numseqs = len(sequencetraces)

        # Define a list for the aligned trace sequences.
        self.alignedseqs = list()

        # Define a list for the indexes from the aligned sequence into
        # the original trace sequence.
        self.seqindexes = list()

        # The aligned primer sequence(s).
        self.alignedprimers = ''

        self.settings = settings
        if self.settings == None:
            self.settings = ConsensSeqSettings()

        #self.seqtraces[0] = sequencetraces[0]
        self.seqtraces = []
        self.seqtraces.append(sequencetraces[0])
        if self.numseqs == 2:
            self.seqtraces.append(sequencetraces[1])

        # Set up lists for the aligned sequences and alignment indices.
        self.alignedseqs = [None] * self.numseqs
        self.seqindexes = [None] * self.numseqs

        self.makeConsensusSequence()

    def getSettings(self):
        return self.settings

    def setConsensSequence(self, use_consens_seq):
        #print len(use_consens_seq), len(self.consensus)
        if len(use_consens_seq) == len(self.consensus):
            self.consensus = use_consens_seq
        else:
            raise ConsensSeqBuilderError('The length of the supplied consensus sequence is invalid.')

    def makeConsensusSequence(self):
        min_confscore = self.settings.getMinConfScore()

        # Get the raw sequences and align the forward/reverse traces if we have both.
        if self.numseqs == 2:
            align = PairwiseAlignment()
            align.setSequences(self.seqtraces[0].getBaseCalls(), self.seqtraces[1].getBaseCalls())
            align.doAlignment()
            self.alignedseqs[0], self.alignedseqs[1] = align.getAlignedSequences()
            self.seqindexes[0], self.seqindexes[1] = align.getAlignedSeqIndexes()
        else:
            self.alignedseqs[0] = self.seqtraces[0].getBaseCalls()
            self.seqindexes[0] = range(0, len(self.alignedseqs[0]))

        # If we have primers, align them to the alignment or single sequence.
        haveprimers = (self.settings.getForwardPrimer() != '' and self.settings.getReversePrimer() != '')
        if haveprimers:
            if self.numseqs == 1:
                self.alignPrimerToSequence()
            else:
                self.alignPrimersToAlignment()

        # Build the consensus sequence.
        if self.numseqs == 1:
            self.makeSingleConsensus(min_confscore)
        else:
            if self.settings.getConsensusAlgorithm() == 'Bayesian':
                self.makeBayesianConsensus(min_confscore)
            else:
                self.makeLegacyConsensus(min_confscore)

        # Do sequence trimming, if requested.
        if self.settings.getTrimConsensus():
            if self.settings.getTrimPrimers() and haveprimers:
                if self.numseqs == 1:
                    self.trimPrimerFromSequence()
                else:
                    self.trimPrimersFromAlignment()

            if self.settings.getTrimEndGaps():
                self.trimEndGaps()

            if self.settings.getDoQualityTrim():
                winsize, basecnt = self.settings.getQualityTrimParams()
                self.trimConsensus(winsize, basecnt)

    def makeBayesianConsensus(self, min_confscore):
        """
        Constructs a consensus sequence using Bayesian inference to assign base
        probabilities to each position in the alignment.
        """
        cons = list()
        consconf = list()

        # Create a dictionary to use for nucleotide posterior probability distributions.
        nppd = {'A': 0.0, 'T': 0.0, 'G': 0.0, 'C': 0.0}

        # Get the start indices for the end gap regions of the alignment.
        lgapstart = self.getLeftEndGapStart()
        rgapstart = self.getRightEndGapStart()

        for cnt in range(len(self.alignedseqs[0])):
            # Initialize variables to indicate no usable data at this position.
            base1 = base2 = 'N'

                # If the mean quality score exceeds the minimum AND the quality of the
                # gap-introducing base is less than the minimum, then keep the gap in the
                # consensus sequence.
                #if mqual >= min_confscore and self.seqtraces[0].getBaseCallConf(self.seq1indexed[cnt]) < min_confscore:
                #    base2 = '-'
                #    score2 = mqual


            # Get the base calls at this position.
            base1 = self.alignedseqs[0][cnt]
            base2 = self.alignedseqs[1][cnt]

            # Determine the consensus base at this position.
            gapflankscore = -1.0
            if base1 not in ('-', 'N') and base2 not in ('-', 'N'):
                # Both traces have usable data, so calculate the posterior probability
                # distribution of nucleotides using Bayes' Theorem, then determine the
                # consensus base.
                self.calcPosteriorBasePrDist(
                        base1, self.seqtraces[0].getBaseCallConf(self.seqindexes[0][cnt]),
                        base2, self.seqtraces[1].getBaseCallConf(self.seqindexes[1][cnt]), nppd)
                cbase, cscore = self.getMostProbableBase(nppd)
            elif base1 not in ('-', 'N'):
                # Only the first trace has usable data.
                cbase = base1
                cscore = self.seqtraces[0].getBaseCallConf(self.seqindexes[0][cnt])

                # Check if this is an internal gap.
                if cnt >= lgapstart and cnt <= rgapstart and base2 == '-':
                    # It is, so get the mean score of the flanking bases.
                    gapflankscore = self.getGapFlankingScore(1, cnt)
            elif base2 not in ('-', 'N'):
                # Only the second trace has usable data.
                cbase = base2
                cscore = self.seqtraces[1].getBaseCallConf(self.seqindexes[1][cnt])

                # Check if this is an internal gap.
                if cnt >= lgapstart and cnt <= rgapstart and base1 == '-':
                    # It is, so get the mean score of the flanking bases.
                    gapflankscore = self.getGapFlankingScore(0, cnt)
            elif base1 == '-' and base2 == '-':
                # We encountered a gap in both sequences due to the primer alignment.
                cbase = ' '
                cscore = 0
            else:
                # Neither trace has usable data.
                cbase = 'N'
                cscore = 1

            # Update the consensus sequence and associated quality score.
            if cscore < min_confscore and cbase != ' ':
                if gapflankscore > min_confscore:
                    # Consider this a spurious gap and delete the position from
                    # the consensus sequence.
                    cbase = ' '
                else:
                    cbase = 'N'
            cons.append(cbase)
            consconf.append(cscore)

        self.consensus = ''.join(cons)
        self.consconf = consconf

    def getGapFlankingScore(self, seqnum, pos):
        """
        Returns the log-adjusted mean score of the two bases flanking an
        internal gap at the position specified by ps in sequence seqnum.
        """
        # Get the locations of the flanking bases.
        index1 = (self.seqindexes[seqnum][pos] + 1) * -1 - 1
        index2 = index1 + 1

        # Calculate the mean quality score of the two flanking bases.
        p1 = 10.0 ** (self.seqtraces[seqnum].getBaseCallConf(index1) / -10.0)
        p2 = 10.0 ** (self.seqtraces[seqnum].getBaseCallConf(index2) / -10.0)

        return -10 * math.log10((p1 + p2) / 2)

    def getMostProbableBase(self, nppd):
        """
        This function determines the most probable base and calculates its associated
        Phred-type quality score from a nucleotide posterior probability distribution.
        """
        # Find the base with the highest probability.
        cbase = 'A'
        for base in ('T', 'G', 'C'):
            if nppd[base] > nppd[cbase]:
                cbase = base

        # Calculate the Phred-type quality score of the most probable base.
        if nppd[cbase] > 0:
            cscore = -10.0 * math.log10(1.0 - nppd[cbase])
        else:
            cscore = 0

        # Add a very small quantity is added to the calculated confidence score to
        # ensure that values very near the minimum confidence score are accepted.
        # Without this, values that should be exactly equal to the minimum are sometimes
        # incorrectly rejected due to rounding error.  An example of the problem is
        # shown in the following line of code, which illustrates the calculations for
        # an initial quality score of 30.  The expression should evaluate to 30, but
        # instead equals 29.999999999.
        #print -10.0 * math.log10(1.0 - (1 - 10.0 ** (30 / -10.0)))
        cscore += 0.000001

        return (cbase, cscore)

    def defineBasePrDist(self, basecall, score, distdict):
        """
        Defines a nucleotide probability distribution based on a given base call
        and Phred-type quality score.  Fully supports all IUPAC ambiguity codes.
        The argument "distdict" is expected to be a dictionary with elements
        indexed by 'A', 'T', 'G', and 'C'.
        """
        # Calculate the error probability.
        eprob = 10.0 ** (score / -10.0)

        # Determine if we have a single base or an ambiguity code and handle
        # each situation appropriately.
        if basecall in self.bases:
            # Fill in the probabilities for each base.
            distdict[basecall] = 1 - eprob
            for base in self.bases:
                if base != basecall:
                    distdict[base] = eprob / 3.0
        elif basecall in self.bases2:
            # We have a 2-base ambiguity code, so split the probability of
            # a correct call between the two bases represented.
            # First assign the error probability to all bases.
            for base in self.bases:
                distdict[base] = eprob / 2.0
            # Then assign the correct call probabilities.
            for base in self.bases2[basecall]:
                distdict[base] = (1 - eprob) / 2.0
        elif basecall in self.bases3:
            # We have a 3-base ambiguity code, so split the probability of
            # a correct call between the three bases represented.
            # First assign the error probability to all bases.
            for base in self.bases:
                distdict[base] = eprob
            # Then assign the correct call probabilities.
            for base in self.bases3[basecall]:
                distdict[base] = (1 - eprob) / 3.0

    def calcPosteriorBasePrDist(self, base1, score1, base2, score2, distdict):
        """
        Uses Bayes' theorem to calculate a posterior distribution of nucleotide
        probabilities with the provided base calls and confidence scores.  The
        result is returned in the argument "distdict", which is expected to be a
        dictionary with elements indexed by 'A', 'T', 'G', and 'C'.
        """
        # Get the prior distribution using the 1st base call and quality score.
        prior = {'A': 0.0, 'T': 0.0, 'G': 0.0, 'C': 0.0}
        self.defineBasePrDist(base1, score1, prior)

        # Use distdict to hold the conditional probabilities for the 2nd base call.
        self.defineBasePrDist(base2, score2, distdict)

        # Calculate the shared denominator for Bayes' theorem, which is the total
        # probability of observing the 2nd base call.
        denom = 0.0
        for base in self.bases:
            denom += distdict[base] * prior[base]

        # Calculate the posterior probability distribution.
        for base in self.bases:
            distdict[base] = (distdict[base] * prior[base]) / denom

    def makeLegacyConsensus(self, min_confscore):
        """
        Uses the algorithm from versions of SeqTrace prior to 0.9.0 to construct a
        consensus sequence.  If ambiguous bases meet the quality criterion, they
        are retained in the final sequence.  This algorithm does not use the quality
        score information as effectively as the Bayesian approach, so the latter
        should generally be used instead.
        """
        cons = list()
        consconf = list()
        #print self.alignedseqs[1]
        #print self.seqindexes[1]
        #print len(self.seqtraces[1].getBaseCalls())

        for cnt in range(len(self.alignedseqs[0])):
            cscore = cscore2 = -1
            if (self.alignedseqs[0][cnt] != '-') and (self.alignedseqs[0][cnt] != 'N'):
                cbase = self.alignedseqs[0][cnt]
                cscore = self.seqtraces[0].getBaseCallConf(self.seqindexes[0][cnt])
            if (self.alignedseqs[1][cnt] != '-') and (self.alignedseqs[1][cnt] != 'N'):
                cbase2 = self.alignedseqs[1][cnt]
                cscore2 = self.seqtraces[1].getBaseCallConf(self.seqindexes[1][cnt])

            if cscore >= min_confscore:
                if cscore2 >= min_confscore:
                    if cbase != cbase2:
                        cbase = 'N'
            elif cscore2 >= min_confscore:
                cscore = cscore2
                cbase = cbase2
            elif self.alignedseqs[0][cnt] == '-' and self.alignedseqs[1][cnt] == '-':
                # We encountered a gap in both sequences due to the primer alignment.
                cscore = cscore2 = 0
                cbase = ' '
            else:
                cbase = 'N'

            cons.append(cbase)
            if cscore > cscore2:
                consconf.append(cscore)
            else:
                consconf.append(cscore2)

        self.consensus = ''.join(cons)
        self.consconf = consconf

    def makeSingleConsensus(self, min_confscore):
        """
        Constructs a "consensus sequence" from a single trace file.  With only one
        trace file, this requires simply checking the quality score for each base
        call to see if it exceeds the minimum quality threshold.  If ambiguous bases
        meet the quality criterion, they are retained in the final sequence.
        """
        cons = list()
        consconf = list()

        for cnt in range(len(self.alignedseqs[0])):
            cscore = 0
            cbase = self.alignedseqs[0][cnt]
            if cbase != '-':
                cscore = self.seqtraces[0].getBaseCallConf(self.seqindexes[0][cnt])

                if cscore < min_confscore:
                    cbase = 'N'
            else:
                # We encountered a gap due to the primer alignment.
                cscore = 0
                cbase = ' '

            cons.append(cbase)
            consconf.append(cscore)

        self.consensus = ''.join(cons)
        self.consconf = consconf

    def getLeftEndGapStart(self):
        """
        Returns the index of the start of the left end gap.  If there are overlapping
        bases in the alignment, this will also be the index of the first pair of
        overlapping bases.  If only one sequence is present or the sequence is empty,
        -1 is returned.
        """
        if self.numseqs == 1:
            return -1

        lgindex = 0

        # Move past any end positions where both trace sequences are gaps.
        # This can happen when primers are aligned to the ends.
        while lgindex < len(self.alignedseqs[0]) and self.alignedseqs[0][lgindex] == '-' and self.alignedseqs[1][lgindex] == '-':
            lgindex += 1

        # Check if both sequences were empty.
        if lgindex == len(self.alignedseqs[0]):
            return -1

        if self.alignedseqs[0][lgindex] == '-':
            while (lgindex < len(self.alignedseqs[0])) and (self.alignedseqs[0][lgindex] == '-'):
                lgindex += 1
        elif self.alignedseqs[1][lgindex] == '-':
            while (lgindex < len(self.alignedseqs[0])) and (self.alignedseqs[1][lgindex] == '-'):
                lgindex += 1

        if lgindex == len(self.alignedseqs[0]):
            return -1
        else:
            return lgindex

    def getRightEndGapStart(self):
        """
        Returns the index of the start of the right end gap.  If there are overlapping
        bases in the alignment, this will also be the index of the last pair of
        overlapping bases.  If only one sequence is present or the sequence is empty,
        -1 is returned.
        """
        if self.numseqs == 1:
            return -1

        rgindex = len(self.alignedseqs[0]) - 1

        # Move past any end positions where both trace sequences are gaps.
        # This can happen when primers are aligned to the ends.
        while rgindex >= 0 and self.alignedseqs[0][rgindex] == '-' and self.alignedseqs[1][rgindex] == '-':
            rgindex -= 1

        # Check if both sequences were empty.
        if rgindex < 0:
            return rgindex

        if self.alignedseqs[0][rgindex] == '-':
            while (rgindex >= 0) and (self.alignedseqs[0][rgindex] == '-'):
                rgindex -= 1
        elif self.alignedseqs[1][rgindex] == '-':
            while (rgindex >= 0) and (self.alignedseqs[1][rgindex] == '-'):
                rgindex -= 1

        return rgindex

    def alignPrimersToAlignment(self):
        """
        Aligns the forward and reverse primer sequences to the forward/reverse
        sequencing trace alignment.  Searching is limited to the non-overlapping
        end regions of the alignment because the primers can only be in these
        regions.  Also adjusts the alignment and alignment indices to accomodate
        the alignment with the primers, if extra gaps are needed.  An alignment-
        length string containing the aligned primers in the appropriate locations
        is saved as self.alignedprimers.  The aligned primers and end gap regions
        of the trace alignment are also saved in a list as self.pr_alignments =
        [[fwd_align, left_end], [rev_align, right_end]].
        """
        if self.numseqs != 2:
            return

        # Figure out which trace is the reverse trace.
        if self.seqtraces[0].isReverseComplemented():
            rev = 0
            fwd = 1
        else:
            rev = 1
            fwd = 0

        # Get the portions of the trace sequences that are in the end gaps, as
        # these regions are where the primers will be located.  We don't use
        # the getEndGapStart() methods because we want to be sure that we're
        # operating on the correct sequence.
        lgapstart = 0
        while self.alignedseqs[fwd][lgapstart] == '-' and lgapstart < len(self.alignedseqs[fwd]):
            lgapstart += 1

        rgapstart = len(self.alignedseqs[rev]) - 1
        while self.alignedseqs[rev][rgapstart] == '-' and rgapstart >= 0:
            rgapstart -= 1

        # Check if either sequence is empty.  If so, we can't proceed.
        if lgapstart == len(self.alignedseqs[fwd]) or rgapstart < 0:
            return

        # Get the left and right ends that should contain the primers.
        leftend = self.alignedseqs[rev][0:lgapstart]
        rightend = self.alignedseqs[fwd][rgapstart + 1:]
        #print leftend
        #print rightend

        # Align the forward primer sequence to the left end gap sequence.  Using
        # a harsher gap penalty (-9 instead of -6) seems to generally produce
        # more useful alignments.
        forward = self.settings.getForwardPrimer()
        align = PairwiseAlignment()
        align.setGapPenalty(-9)
        align.setSequences(forward, leftend)
        align.doAlignment()
        fwdaligned, lendaligned = align.getAlignedSequences()

        # Align the reverse complemented reverse primer sequence to the
        # right end gap sequence.
        reverse = sequencetrace.reverseCompSequence(self.settings.getReversePrimer())
        align.setSequences(reverse, rightend)
        align.doAlignment()
        #print align.getAlignedSequences()[0]
        #print align.getAlignedSequences()[1]
        revaligned, rendaligned = align.getAlignedSequences()

        # Replace starting and ending gap characters in the aligned primer
        # sequences with spaces.
        fwdaligned = self.trimAlignedPrimerEnds(fwdaligned)
        revaligned = self.trimAlignedPrimerEnds(revaligned)

        # If the primer alignment introduced gaps into the end gap region of the
        # trace alignment, update the alignment, alignment indices, consensus
        # sequence, and consensus quality score list to include the extra gaps.
        for index in range(len(lendaligned)):
            if lendaligned[index] == '-':
                # Update the starts of the end gaps to reflect the new gaps
                # that are added to the left side of the alignment.
                lgapstart += 1
                rgapstart += 1

                # Update both aligned sequences and sequence indexes.
                for seqnum in range(2):
                    self.alignedseqs[seqnum] = self.alignedseqs[seqnum][0:index] + '-' + self.alignedseqs[seqnum][index:]
                    sindex = self.seqindexes[seqnum][index]
                    if sindex > 0:
                        sindex = (sindex * -1) - 1
                    self.seqindexes[seqnum].insert(index, sindex)

        # Do the same for the right end region.
        for index in range(len(rendaligned)):
            if rendaligned[index] == '-':
                # Update both aligned sequences and sequence indexes.
                for seqnum in range(2):
                    gappos = rgapstart + index + 1
                    self.alignedseqs[seqnum] = self.alignedseqs[seqnum][0:gappos] + '-' + self.alignedseqs[seqnum][gappos:]
                    # Check if we're at the end of the alignment.
                    if gappos != len(self.seqindexes[seqnum]):
                        sindex = self.seqindexes[seqnum][gappos]
                        if sindex > 0:
                            sindex = (sindex * -1) - 1
                    else:
                        sindex = self.seqindexes[seqnum][gappos - 1]
                        if sindex > 0:
                            sindex = ((sindex + 1) * -1) - 1
                    self.seqindexes[seqnum].insert(gappos, sindex)

        # Save the primer and end gap alignments.
        self.pr_alignments = [[fwdaligned, lendaligned], [revaligned, rendaligned]]

        # Construct a full-length sequence to contain the primer alignments.
        self.alignedprimers = (
                fwdaligned + ' ' * (rgapstart - lgapstart + 1)
                + revaligned)
        #print self.alignedprimers
        #print len(self.alignedprimers)
        #print len(self.alignedseqs[0])

    def alignPrimerToSequence(self):
        """
        Aligns a primer sequence to the base calls of a single trace file.
        Also adjusts the alignment and alignment indices to accomodate
        the alignment with the primer, if extra gaps are needed.  An
        alignment-length string containing the aligned primer in the
        appropriate location is saved as self.alignedprimers.
        """
        if self.numseqs == 2:
            return

        # Figure out if we're working on a reverse trace and get the
        # appropriate primer sequence to search for.
        isreverse = self.seqtraces[0].isReverseComplemented()
        if isreverse:
            primer = self.settings.getForwardPrimer()
        else:
            primer = sequencetrace.reverseCompSequence(self.settings.getReversePrimer())

        if primer == '':
            return

        # Align the primer sequence to the trace sequence.  Using a harsher gap
        # penalty (-12 instead of -6) seems to improve the chances of getting the
        # primer to align in the correct location.
        align = PairwiseAlignment()
        align.setGapPenalty(-12)
        align.setSequences(primer, self.alignedseqs[0])
        align.doAlignment()
        praligned, seqaligned = align.getAlignedSequences()

        # Use the new alignment for the trace sequence and index list.
        self.alignedseqs[0] = seqaligned
        self.seqindexes[0] = align.getAlignedSeqIndexes()[1]

        # Replace starting and ending gap characters in the aligned primer
        # sequences with spaces.
        praligned = self.trimAlignedPrimerEnds(praligned)
        self.alignedprimers = praligned

        #print self.alignedprimers
        #print len(self.alignedprimers)
        #print len(self.alignedseqs[0])

    def trimPrimersFromAlignment(self):
        """
        Uses a primer alignment produced by the method
        alignPrimersToAlignment() to see if the primers could be located
        in the trace alignment.  If so, the ends of the consensus sequence
        are trimmed to remove the primers and any additional preceding
        or trailing sequence.
        """
        if self.numseqs != 2:
            return

        # Retrieve the primer and end gap alignments.
        fwdaligned = self.pr_alignments[0][0]
        lendaligned = self.pr_alignments[0][1]
        revaligned = self.pr_alignments[1][0]
        rendaligned = self.pr_alignments[1][1]

        # Determine the percent of forward primer bases that matched the trace
        # data.  Count all gaps as mismatches.
        fwdtotallen = fwdmatches = 0
        for index in range(len(fwdaligned)):
            if fwdaligned[index] != ' ':
                fwdtotallen += 1
                if fwdaligned[index] == lendaligned[index]:
                    fwdmatches += 1
        #print fwdmatches, fwdtotallen, (float(fwdmatches) / fwdtotallen)

        # If there are enough matches to consider the alignment valid, trim
        # the forward primer from the finished sequence.
        if float(fwdmatches) / fwdtotallen >= self.settings.getPrimerMatchThreshold():
            # Find the ending location of the forward primer in the alignment.
            index = len(fwdaligned) - 1
            while fwdaligned[index] == ' ':
                index -= 1

            self.consensus = ' ' * (index + 1) + self.consensus[index + 1:]

        # Determine the percent of reverse primer bases that matched the trace
        # data.  Count all gaps as mismatches.
        revtotallen = revmatches = 0
        for index in range(len(revaligned)):
            if revaligned[index] != ' ':
                revtotallen += 1
                if revaligned[index] == rendaligned[index]:
                    revmatches += 1
        #print revmatches, revtotallen, (float(revmatches) / revtotallen)

        # If there are enough matches to consider the alignment valid, trim
        # the reverse primer from the finished sequence.
        if float(revmatches) / revtotallen >= self.settings.getPrimerMatchThreshold():
            # Find the starting location of the reverse primer in the alignment.
            index = 0
            while revaligned[index] == ' ':
                index += 1
            alindex = len(self.consensus) - (len(revaligned) - index)

            self.consensus = self.consensus[0:alindex] + ' ' * (len(revaligned) - index)

    def trimPrimerFromSequence(self):
        """
        Uses a primer alignment produced by the method
        alignPrimersToAlignment() to see if a primer could be located in
        the trace alignment.  If so, the right end of the consensus sequence
        is trimmed to remove the primer and any additional trailing sequence.
        """
        if self.numseqs == 2:
            return

        # Determine the percent of primer bases that matched the trace data.
        # Count all gaps as mismatches.
        praligned = self.alignedprimers
        prtotallen = prmatches = 0
        for index in range(len(praligned)):
            if praligned[index] != ' ':
                prtotallen += 1
                if praligned[index] == self.alignedseqs[0][index]:
                    prmatches += 1
        #print float(prmatches) / prtotallen

        if prtotallen == 0:
            # There was no primer in the alignment, so do nothing.
            return

        # See if enough primer bases match to consider the alignment valid.
        # If so, trim the sequence.  Forward traces are trimmed from the left
        # end of the primer, reverse traces are trimmed from the right end of
        # the primer.
        if float(prmatches) / prtotallen >= self.settings.getPrimerMatchThreshold():
            if self.seqtraces[0].isReverseComplemented():
                # Find the starting location of the primer in the alignment.
                index = len(praligned) - 1
                while praligned[index] == ' ':
                    index -= 1

                self.consensus = ' ' * (index + 1) + self.consensus[index + 1:]
            else:
                # Find the starting location of the primer in the alignment.
                index = 0
                while praligned[index] == ' ':
                    index += 1

                self.consensus = self.consensus[0:index] + ' ' * (len(self.alignedseqs[0]) - index)

    def trimAlignedPrimerEnds(self, alignedp):
        """
        Replaces starting and ending gap characters in an aligned primer sequence
        with spaces.
        """
        index1 = 0
        while alignedp[index1] == '-':
            index1 += 1
        index2 = len(alignedp) - 1
        while alignedp[index2] == '-':
            index2 -= 1
        trimmed = ' ' * index1 + alignedp[index1:index2+1] + ' ' * (len(alignedp) - index2 - 1)

        return trimmed

    def getAlignedPrimers(self):
        return self.alignedprimers

    def trimEndGaps(self):
        if self.numseqs == 1:
            return

        # Get the index of the start of the left end gap.
        lgindex = self.getLeftEndGapStart()

        # Get the index of the start of the right end gap.
        rgindex = self.getRightEndGapStart()

        # See if we encountered an empty sequence (this should never happen with real data)
        # and adjust the index values to result in a blank string of appropriate length.
        if rgindex == -1:
            lgindex = 0

        # Construct the consensus sequence without the end gap portions.
        self.consensus = ((' ' * lgindex) + self.consensus[lgindex:rgindex + 1]
                + (' ' * (len(self.consensus) - rgindex - 1)))

    def trimConsensus(self, winsize, basecnt):
        """
        Trims the ends of the consensus sequence until basecnt bases within a
        run of winsize bases meet the minimum quality threshold.  Any spaces in
        the sequence are ignored and not counted in the window size.
        """
        # Build a dictionary for all valid nucleotide codes that will be
        # used for counting the number of good bases in a window.
        base_to_int = {}
        for base in self.allbases:
            base_to_int[base] = 1
        base_to_int['N'] = 0

        # First, eliminate spaces from the consensus sequence.
        compcons = self.consensus.replace(' ', '')

        # Make sure there are enough bases to actually do the analysis.
        if len(compcons) < winsize:
            return

        # Build a list mapping the consensus sequence to simple integer values.  Correctly-called
        # bases get assigned a 1, incorrectly-called bases get assigned a 0.
        consvals = [base_to_int[base] for base in compcons]

        # Analyze the left end (5') of the sequence first.
        index = 0

        # Initialize the count of good bases.
        num_good = sum(consvals[0:winsize])

        # Slide the window along the sequence until it contains enough correct base calls.
        while (num_good < basecnt) and ((index + winsize) < len(compcons)):
            num_good += consvals[index + winsize]
            num_good -= consvals[index]

            index += 1
            #print index, num_good

        # Find the correct index in the consensus after accounting for any ignored spaces.
        index_left = skipcnt = -1
        while skipcnt != index:
            index_left += 1
            if self.consensus[index_left] != ' ':
                skipcnt += 1
        #print 'index_left:', index_left, 'num_good:', num_good

        # Now analyze the right end (3') of the sequence.
        indexold = index
        index = len(compcons) - 1

        # Initialize the count of good bases.
        num_good = sum(consvals[len(consvals) - winsize:len(consvals)])

        # Slide the window along the sequence until it contains enough correct base calls.
        while (num_good < basecnt) and ((index - winsize) >= indexold):
            num_good += consvals[index - winsize]
            num_good -= consvals[index]

            index -= 1
        #print index, num_good

        # Find the correct index in the consensus after accounting for any ignored spaces.
        index_right = skipcnt = -1
        while skipcnt != index:
            index_right += 1
            if self.consensus[index_right] != ' ':
                skipcnt += 1
        #print 'index:', index
        #print 'index_right:', index_right, 'num_good:', num_good

        if num_good < basecnt:
            # If we failed to find a sufficient number of quality bases anywhere in the sequence,
            # simply trim the entire string.
            new_consensus = ' ' * len(self.consensus)
        else:
            # Build the trimmed consensus sequence.
            new_consensus = ((' ' * index_left) + self.consensus[index_left:index_right + 1]
                    + (' ' * (len(self.consensus) - index_right - 1)))

        self.consensus = new_consensus

    def getNumSeqs(self):
        return self.numseqs

    def getConsensus(self, startindex=0, endindex=-1):
        if endindex == -1:
            endindex = len(self.consensus) - 1

        return self.consensus[startindex:endindex+1]

    def getCompactConsensus(self):
        return self.consensus.replace(' ', '')

    def getAlignedSequence(self, sequence_num):
        if (sequence_num < 0) or (sequence_num >= self.numseqs):
            raise ConsensSeqBuilderError('Invalid sequence number.')

        return self.alignedseqs[sequence_num]

    def getSequenceTrace(self, sequence_num):
        if (sequence_num < 0) or (sequence_num >= self.numseqs):
            raise ConsensSeqBuilderError('Invalid sequence number.')

        return self.seqtraces[sequence_num]

    def getActualSeqIndex(self, sequence_num, alignment_index):
        if (sequence_num < 0) or (sequence_num >= self.numseqs):
            raise ConsensSeqBuilderError('Invalid sequence number.')

        return self.seqindexes[sequence_num][alignment_index]


class ModifiableConsensSeqBuilder(ConsensSeqBuilder, Observable):
    """
    Extends ConsensSeqBuilder to allow for user editing of the consensus
    sequence with support for unlimited undo/redo functinality.
    """
    def __init__(self, sequencetraces, settings=None):
        ConsensSeqBuilder.__init__(self, sequencetraces, settings)

        self.undo_stack = list()
        self.redo_stack = list()

        # initialize observable events
        self.defineObservableEvents(['consensus_changed', 'undo_state_changed', 'redo_state_changed'])

    def deleteBases(self, start_index, end_index):
        # swap the start and end points, if necessary
        if start_index > end_index:
            tmp = start_index
            start_index = end_index
            end_index = tmp

        # add the undo information
        self.undo_stack.append({'start': start_index, 'end': end_index, 'data': self.consensus[start_index:end_index+1]})

        # delete the bases
        self.consensus = self.consensus[0:start_index] + ' '*(end_index-start_index+1) + self.consensus[end_index+1:]

        self.notifyObservers('consensus_changed', (start_index, end_index))
        if len(self.undo_stack) == 1:
            self.notifyObservers('undo_state_changed', (True,))

    def modifyBases(self, start_index, end_index, newseq):
        """
        Modifies bases in the consensus sequence.  The changes can be reversed with
        the undo() method.  The replacement string must be a combination of valid
        IUPAC nucleotide codes and spaces.
        """
        # swap the start and end points, if necessary
        if start_index > end_index:
            tmp = start_index
            start_index = end_index
            end_index = tmp

        if len(newseq) != (end_index - start_index + 1):
            raise ConsensSeqBuilderError('Start and end indexes do not match the length of the replacement string.')

        # Use a regular expression to check if the characters in the new string are all valid.
        reo = re.compile('[' + ''.join(self.allbases) + ' ]+')
        match = reo.match(newseq)
        if match.end() - match.start() != len(newseq):
            raise ConsensSeqBuilderError('The replacement sequence contains invalid characters.')

        # add the undo information
        self.undo_stack.append({'start': start_index, 'end': end_index, 'data': self.consensus[start_index:end_index+1]})

        # insert the new bases
        self.consensus = self.consensus[0:start_index] + newseq + self.consensus[end_index+1:]

        self.notifyObservers('consensus_changed', (start_index, end_index))
        if len(self.undo_stack) == 1:
            self.notifyObservers('undo_state_changed', (True,))

    def recalcConsensusSequence(self):
        oldcons = self.consensus
        self.makeConsensusSequence()

        # Any time the consensus sequence is recalculated, trigger a change event.
        self.notifyObservers('consensus_changed', (0, len(self.consensus) - 1))

        if oldcons != self.consensus:
            self.undo_stack.append({'start': 0, 'end': len(self.consensus) - 1, 'data': oldcons})

            if len(self.undo_stack) == 1:
                self.notifyObservers('undo_state_changed', (True,))

    def undo(self):
        if len(self.undo_stack) > 0:
            u = self.undo_stack.pop()
            start = u['start']
            end = u['end']

            # save the redo information
            self.redo_stack.append({'start': start, 'end': end, 'data': self.consensus[start:end+1]})

            self.consensus = self.consensus[0:start] + u['data'] + self.consensus[end+1:]

            self.notifyObservers('consensus_changed', (start, end))
            if len(self.redo_stack) == 1:
                self.notifyObservers('redo_state_changed', (True,))
            if len(self.undo_stack) == 0:
                self.notifyObservers('undo_state_changed', (False,))

    def redo(self):
        if len(self.redo_stack) > 0:
            r = self.redo_stack.pop()
            start = r['start']
            end = r['end']

            # save the undo information
            self.undo_stack.append({'start': start, 'end': end, 'data': self.consensus[start:end+1]})

            self.consensus = self.consensus[0:start] + r['data'] + self.consensus[end+1:]

            self.notifyObservers('consensus_changed', (start, end))
            if len(self.undo_stack) == 1:
                self.notifyObservers('undo_state_changed', (True,))
            if len(self.redo_stack) == 0:
                self.notifyObservers('redo_state_changed', (False,))


