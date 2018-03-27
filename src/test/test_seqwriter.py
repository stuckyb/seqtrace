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


from seqtrace.core import seqwriter

import unittest
import tempfile
import os


# This test fixture tests all concrete SequenceWriter subclasses.  Both
# addAlignedSequence() and addUnalignedSequence() are tested.  The general
# approach is to send a bunch of test sequence data to the SequenceWriter,
# write the file, then read the file back and check the data.  Note that in the
# case of structured sequence file formats, such as NEXUS, these tests make no
# attempt to thoroughly verify that the structure of the generated file
# conforms to specifications.  They instead focus on ensuring that the data
# read back from the file exactly matches the original data that was sent to
# the SequenceWriter.
class TestSequenceWriter(unittest.TestCase):
    # Define a bunch of test sequence data.
    numaligned = 2
    testseqs = [
            # The first two sequences are for testing addAlignedSequence().
            {
                'desc': 'test sequence 3', 'filename': 'fakefile3.ztr',
                'seq': 'NAAANTAANNNNTNTTTTTAANNATATTTATTTTTCAAATTATTTCAATTTTCTTTCACAATACTACTCAACTATAATTTAAATTATTTTTTCTTTATAAAATACTAAAACAAAAATTATTATAATTATTTTTAATAATTTATTAAAACTAAAAAAAAATTAATAAATAAAACATAATCAA'
            },
            {
                'desc': 'test sequence 4', 'filename': 'fakefile4.ztr',
                'seq': 'NCNACTACACCTAAAATTATATCTTAATCCAACATCGAGGTCGCAATCTTTTTTATTGATATGAACTCTCCAAAAAAATTACGCTGTTATCCCTAAAGTAACTTATTTTTTTAATCGTTATTAACGGATCAATTTTCCATAAATTAATGTAAAAAAAAATTAAAAGTTATTCAAATTTTAA'
            },

            # The last six sequences are all for testing addUnalignedSequence().
            {
                'desc': 'test sequence 1', 'filename': 'fakefile1.ztr',
                'seq': 'AANTAANNTTTNTTTTTAAATATTTATTTTTCAANTTATTTCAATTTTCTTTCACAATACTATTCAACTATAATTAAAATTATTTTTTCTTTATAAAATACTAAAACAAAAATTTATTATAATTATTTTTAATAATTTATTTAACCAAAAAAAAATTTAATAAATAAAACACAATCAATTTATATTGATTTGCACAAAAATCTTTTCAATGTAAATGAAATACTTTACTTAATAAGCTTTAAATTGCATTCTAGATACACTTTCCAGTACATCTACTATGTTACGACTTATCTTACCTTAATAGCAAGAGTGACGGGCGATGTGTGCATATTTTAGAGCTAAAATCAAATTATTTATCTTTATAATTTTACTATCAAATCCACCTTCAATAAAAATTTCAAATTTATATCCATTTTAAATAATTTTATTGTAACCCATTAATACTTAAATATAAGCTACACCTTGATCTGATATACTTTCATTTTTAAAATTATGAAAATTAACATTCTTATAAAATATTCTAATAACGACGGTATATAAACTGAATACAAATTTAAGTAAGGTCCATCGTGGATTATCGATTATAAAACAGGTTCCTCTGAATAGACTAAAATACCGCCAAATTTTTTAAGTTTTAAGAACATAACTNATACTACCTTAGTTTTTATATTTACNTTTTAAATAANNNNNNNNNNNNNCCNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNAA'
            },
            {
                'desc': 'test sequence 2', 'filename': 'fakefile2.ztr',
                'seq': 'TNNAAACTTAAAAAATTTGGCGGTATTTTAGTCTATTCAGAGGAACCTGTTTTATAATCGATAATCCACGATGGACCTTACTTAAATTTGTATTCAGTTTATATACCGTCGTTATTAGAATATTTCATAAGAATGTTAATTTTCATAATTTTAAAAATGAAAGTATATCAGATCAAGGTGTAGCTTATATTTAAGTATTAATGGGTTACAATAAAATTATTTAAGATGGATATAAATTTGAAATTTTTATTGAAGGTGGATTTGATAGTAAAATTATAAAGATAAATAATTTGATTTTAGCTCTAAAATATGCACACATCGCCCGTCACTCTTTCTATTAAGGTAAGATAAGTCGTAACATAGTAGATGTACTGGAAAGTGTATCTAGAATGCAATTTAAAGCTTATTAAGTAAAGTATTTCATTTACATTGAAAAGATTTTTGTGCAAATCAATATAAATTGATTATGTTTTATTTATTAATTTTTTTTTAGTTTTGATAAATTATTAAAAATAATTATAATAATTTTTGTTTTAGTATTTTATAAAGAAAAAATAATTTAAATTATAGTTGAGTAGTATTGTGAAAGAAAATTGAAATAATTTGAAAAATAAATATTTAAAAANAAANNTTANTTT'
            },
            {
                'desc': 'test sequence 3', 'filename': 'fakefile3.ztr',
                'seq': 'NAAANTAANNNNTNTTTTTAANNATATTTATTTTTCAAATTATTTCAATTTTCTTTCACAATACTACTCAACTATAATTTAAATTATTTTTTCTTTATAAAATACTAAAACAAAAATTATTATAATTATTTTTAATAATTTATTAAAACTAAAAAAAAATTAATAAATAAAACATAATCAATTTATATTGATTTGCACAAAAATCTTTTCAATGTAAATGAAATACTTTACTTAATAAGCTTTAAATTGCATTCTAGGTACACTTTCCAGTACATCTACTATGTTACGACTTATCTTACCTTAATAGAAAGAGTGACGGGCGATGTGTGCATATTTTAGAGCTAAAATCAAATTATTTATCTTTATAATTTTACTATCAAATCCACCTTCAATAAAAATTTCAAATTTATATCCATCTTAAATAATTTTATTGTAACCCATTAATACTTAAATATAAGCTACACCTTGATCTGATATACTTTCATTTTTAAAATTATGAAAATTAACATTCTTATGAAATATTCTAATAACGACGGTATATAAACTGAATACAAATTTAAGTAAGGTCCATCGTGGATTATCGATTATAAAACAGGTTCCTCTGAATAGACTAAAATACCGCCAAATTTTTTAAGTTTTAANAANATAACNNATACNNANNNTANTTTTTATACTTACNNTT'
            },
            # Has exactly one base beyond an integral multiple of 80 (for
            # testing FASTA).
            {
                'desc': 'test sequence 4', 'filename': 'fakefile4.ztr',
                'seq': 'NCNACTACACCTAAAATTATATCTTAATCCAACATCGAGGTCGCAATCTTTTTTATTGATATGAACTCTCCAAAAAAATTACGCTGTTATCCCTAAAGTAACTTATTTTTTTAATCGTTATTAACGGATCAATTTTCCATAAATTAATGTAAAAAAAAATTAAAAGTTATTCAAATTTTAATATCACCCCAATAAAATATAATAAATTATTACAATAAAAAAAATCTACAAAATTATAATAATATAGATATAAAGATTTATAGGGTCTTCTCGTCTTTTAATTTTATTTTAGCGTTTTAACTAAAAAATAAAATTCTAATATAAATTTTAATGAAACAGTTAATATCTCGTCCAACCATTCATTCCAGCCTCCAATTAAAAGACTAATGATTATGCTACCTTTGCACAGTTAATATACTGCGGCCATTTAAAAATTATTCAGTGGGCAGGTTAGACTTAAAATAAAATTCAAAAAGACATG'
            },
            # Has exactly 80 bases (for testing FASTA).
            {
                'desc': 'test sequence 5', 'filename': 'fakefile5.ztr',
                'seq': 'NCNACTACACCTAAAATTATATCTTAATCCAACATCGAGGTCGCAATCTTTTTTATTGATATGAACTCTCCAAAAAAATT'
            },
            # Less than 80 bases (for testing FASTA).
            {
                'desc': 'test sequence 6', 'filename': 'fakefile6.ztr',
                'seq': 'TTAATCCAACATCGAGGTCGCAATCTTTTTTA'
            }
        ]

    def test_plainText(self):
        sw = seqwriter.SequenceWriterFactory.getSequenceWriter(seqwriter.FORMAT_PLAINTEXT)

        # Get a temporary file.
        tmpfd, tmpfpath = tempfile.mkstemp()
        os.close(tmpfd)

        sw.open(tmpfpath)

        # Write the data to the file, testing both addUnalignedSequences() and
        # addAlignedSequences().
        cnt = 0
        for seq in self.testseqs:
            if cnt > 1:
                sw.addUnalignedSequence(seq['seq'], seq['filename'], seq['desc'])
            else:
                sw.addAlignedSequence(seq['seq'], seq['filename'], seq['desc'])
            cnt += 1

        sw.write()

        sfile = open(tmpfpath)

        cnt = 0
        line = '\n'

        # Read each sequence from the file and make sure the data are correct.
        while line != '':
            line = sfile.readline()

            # Test the next sequence.
            if line.startswith('Description: '):
                seq = self.testseqs[cnt]

                self.assertEqual(seq['desc'], line.rstrip().replace('Description: ', ''))
                line = sfile.readline()
                self.assertEqual(seq['filename'], line.rstrip().replace('Filename: ', ''))
                line = sfile.readline()
                self.assertEqual(seq['seq'], line.rstrip())

                cnt += 1

        # Make sure we got back the correct number of sequences.
        self.assertEqual(len(self.testseqs), cnt)

        sfile.close()
        os.unlink(tmpfpath)

    def test_FASTA(self):
        sw = seqwriter.SequenceWriterFactory.getSequenceWriter(seqwriter.FORMAT_FASTA)

        # Get a temporary file.
        tmpfd, tmpfpath = tempfile.mkstemp()
        os.close(tmpfd)

        sw.open(tmpfpath)

        # Write the data to the file, testing both addUnalignedSequences() and
        # addAlignedSequences().
        cnt = 0
        for seq in self.testseqs:
            if cnt > 1:
                sw.addUnalignedSequence(seq['seq'], seq['filename'], seq['desc'])
            else:
                sw.addAlignedSequence(seq['seq'], seq['filename'], seq['desc'])
            cnt += 1

        sw.write()

        sfile = open(tmpfpath)

        cnt = 0
        line = '\n'

        # Read each sequence from the file and make sure the data are correct.
        while line != '':
            line = sfile.readline()

            # Test the next sequence.
            if line.startswith('>'):
                seq = self.testseqs[cnt]

                desc, sep, filename = line.rstrip().partition(': ')
                self.assertEqual('>' + seq['desc'], desc)
                self.assertEqual(seq['filename'], filename)

                # Read the sequence.
                fseq = ''
                while line != '\n':
                    line = sfile.readline()
                    fseq += line.rstrip()

                self.assertEqual(seq['seq'], fseq)

                cnt += 1

        # Make sure we got back the correct number of sequences.
        self.assertEqual(len(self.testseqs), cnt)

        sfile.close()
        os.unlink(tmpfpath)

    def test_NEXUS(self):
        sw = seqwriter.SequenceWriterFactory.getSequenceWriter(seqwriter.FORMAT_NEXUS)

        # Get a temporary file.
        tmpfd, tmpfpath = tempfile.mkstemp()
        os.close(tmpfd)

        sw.open(tmpfpath)

        # Write the data to the file, testing both addUnalignedSequences() and
        # addAlignedSequences().
        cnt = 0
        for seq in self.testseqs:
            if cnt > 1:
                sw.addUnalignedSequence(seq['seq'], seq['filename'], seq['desc'])
            else:
                sw.addAlignedSequence(seq['seq'], seq['filename'], seq['desc'])
            cnt += 1

        sw.write()

        sfile = open(tmpfpath)

        # Read the NEXUS file and make sure all of the data are correct.
        cnt = 0
        line = '\n'
        while line != '':
            line = sfile.readline()

            # Test the taxa labels.
            if line.endswith('TAXLABELS\n'):
                line = sfile.readline()
                line = line.strip(" \n'")
                labels = line.strip().split("' '")
                cnt = 0
                for label in labels:
                    desc, sep, filename = label.partition(': ')
                    self.assertEqual(self.testseqs[cnt]['desc'], desc)
                    self.assertEqual(self.testseqs[cnt]['filename'], filename)
                    cnt += 1
                    if cnt == 4:
                        # We need to jump ahead in the testseqs list because of
                        # the order in which the labels were added.
                        cnt = 6

                # Make sure we got back the correct number of labels.
                self.assertEqual(len(self.testseqs), cnt)

            # Test the aligned sequence data.
            if line.endswith('CHARACTERS;\n'):
                data = self.readNEXUSMatrix(sfile, line)
                cnt = 0
                for item in data:
                    # Test the label and sequence.
                    self.assertEqual(self.testseqs[cnt]['desc'], item['label']['desc'])
                    self.assertEqual(self.testseqs[cnt]['filename'], item['label']['filename'])
                    self.assertEqual(self.testseqs[cnt]['seq'], item['seq'])

                    cnt += 1

                # Make sure we got back the correct number of sequences.
                self.assertEqual(self.numaligned, len(data))

            # Test the unaligned sequence data.
            if line.endswith('UNALIGNED;\n'):
                data = self.readNEXUSMatrix(sfile, line)
                cnt = self.numaligned
                for item in data:
                    # Test the label and sequence.
                    self.assertEqual(self.testseqs[cnt]['desc'], item['label']['desc'])
                    self.assertEqual(self.testseqs[cnt]['filename'], item['label']['filename'])
                    self.assertEqual(self.testseqs[cnt]['seq'], item['seq'])

                    cnt += 1

                # Make sure we got back the correct number of sequences.
                self.assertEqual(len(self.testseqs) - self.numaligned, len(data))

        # A final test to make sure we actually read sequence data (the similar
        # tests inside of the loop will never run if none of the if statements
        # match).
        self.assertEqual(len(self.testseqs), cnt)

        sfile.close()
        os.unlink(tmpfpath)

    def readNEXUSMatrix(self, sfile, line):
        res = list()

        while not(line.endswith('MATRIX\n')):
            line = sfile.readline()

        line = sfile.readline()
        while not(line.endswith(';\n')):
            # Get the label and sequence.
            line = line.strip(" \n'")
            label, sep, seq = line.partition("' ")

            # Get the label parts.
            desc, sep, filename = label.partition(': ')

            res.append({'label': {'desc': desc, 'filename': filename}, 'seq': seq})

            line = sfile.readline()

        return res





if __name__ == '__main__':
    #unittest.main()
    suite = unittest.defaultTestLoader.loadTestsFromName(__name__)
    unittest.TextTestRunner(verbosity=2).run(suite)

