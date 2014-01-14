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


from datetime import datetime
import pygtk
pygtk.require('2.0')
import gtk



class SequenceWriterError(Exception):
    pass

class UnknownFileFormatError(SequenceWriterError):
    def __str__(self):
        return 'The specified file format was not recognized.';


# define sequence file formats
FORMAT_PLAINTEXT = 0
FORMAT_FASTA = 1
FORMAT_NEXUS = 2

class SequenceWriterFactory:
    @staticmethod
    def getSequenceWriter(file_format):
        if file_format == FORMAT_PLAINTEXT:
            writer = PlainTextSeqWriter()
        elif file_format == FORMAT_FASTA:
            writer = FASTASeqWriter()
        elif file_format == FORMAT_NEXUS:
            writer = NEXUSSeqWriter()
        else:
            raise UnknownFileFormatError

        return writer


# An abstract class that should not be instantiated directly.
class SequenceWriter:
    def __init__(self):
        self.a_sequences = list()
        self.u_sequences = list()
        
        self.a_length = -1

    def addAlignedSequence(self, seqstr, filename, description):
        if self.a_length == -1:
            self.a_length = len(seqstr)

        # make sure all aligned sequence lengths match
        if len(seqstr) != self.a_length:
            raise SequenceWriterError('All aligned sequences must be the same length.')

        self.a_sequences.append({
            'seq': seqstr, 'filename': filename, 'desc': description
            })

    def addUnalignedSequence(self, seqstr, filename, description):
        self.u_sequences.append({
            'seq': seqstr, 'filename': filename, 'desc': description
            })

    def open(self, filename):
        try:
            self.fh = open(filename, 'w')
        except IOError:
            raise

    # Returns a single string that contains both the provided description and filename(s),
    # formatted in a nice way.
    def getDescStr(self, sequence):
        name = sequence['desc']
        if len(sequence['filename']) != 0:
            if len(name) != 0:
                name += ': '
            name += sequence['filename']

        return name


# This class does not write data in any specific format supported by other software;
# instead, it simply writes out all data in a plain text format that is easy to read
# and edit manually.
class PlainTextSeqWriter(SequenceWriter):
    def write(self):
        dt = datetime.now()
        self.fh.write('Date and time: ' + dt.strftime('%B %d, %Y %I:%M:%S %p') + '\n\n')

        # write the sequence data
        if len(self.a_sequences) != 0:
            self.writeAlignedSeqs()

        if len(self.u_sequences) != 0:
            self.writeUnalignedSeqs()

        self.fh.close()

    def writeAlignedSeqs(self):
        self.fh.write('-- Aligned Sequences --\n\n')

        for sequence in self.a_sequences:
            self.fh.write('Description: ' + sequence['desc'] + '\n')
            self.fh.write('Filename: ' + sequence['filename'] + '\n')
            self.fh.write(sequence['seq'] + '\n\n')

    def writeUnalignedSeqs(self):
        self.fh.write('-- Unaligned Sequences --\n\n')

        for sequence in self.u_sequences:
            self.fh.write('Description: ' + sequence['desc'] + '\n')
            self.fh.write('Filename: ' + sequence['filename'] + '\n')
            self.fh.write(sequence['seq'] + '\n\n')


class FASTASeqWriter(SequenceWriter):
    fasta_linelen = 80

    def write(self):
        for sequence in self.a_sequences:
            self.writeSequence(sequence)

        for sequence in self.u_sequences:
            self.writeSequence(sequence)

        self.fh.close()

    def writeSequence(self, sequence):
        # write the sequence description
        desc_str = '>' + self.getDescStr(sequence)

        if len(desc_str) > self.fasta_linelen:
            self.fh.write(desc_str[:self.fasta_linelen] + '\n')
        else:
            self.fh.write(desc_str + '\n')

        # write the sequence data
        cnt = 0
        while cnt < len(sequence['seq']):
            if (cnt + self.fasta_linelen) > len(sequence['seq']):
                self.fh.write(sequence['seq'][cnt:] + '\n')
            else:
                self.fh.write(sequence['seq'][cnt:cnt+self.fasta_linelen] + '\n')
            cnt += self.fasta_linelen
        self.fh.write('\n')


# This class makes some simplifying assumptions about the data it will be getting (e.g.,
# that missing bases are always indicated with 'N').  As defined in the published NEXUS file
# specification, all unaligned sequences are placed in an UNALIGNED block.  Interestingly,
# Mesquite produces the error "Unrecognized Block: UNALIGNED" when it attempts to open a file
# with an UNALIGNED block!
class NEXUSSeqWriter(SequenceWriter):
    def write(self):
        self.fh.write('#NEXUS\n')

        # add date/time info to the file
        dt = datetime.now()
        self.fh.write('[file written on ' + dt.strftime('%B %d, %Y %I:%M:%S %p') + ']\n\n')

        # first, get all unique taxa names
        names = list()
        for sequence in self.a_sequences:
            name = self.getTaxaName(sequence)
            if name not in names:
                names.append(name)
        for sequence in self.u_sequences:
            name = self.getTaxaName(sequence)
            if name not in names:
                names.append(name)

        # write the TAXA block
        self.fh.write('BEGIN TAXA;\n')
        self.fh.write('    DIMENSIONS NTAX=' + str(len(names)) + ';\n')
        self.fh.write('    TAXLABELS\n    ')
        for name in names:
            self.fh.write(name + ' ')
        self.fh.write('\n    ;\nEND;\n')

        # write the sequence data
        if len(self.a_sequences) != 0:
            self.writeCharactersBlock()

        if len(self.u_sequences) != 0:
            self.writeUnalignedBlock()

        self.fh.write('\n')
        self.fh.close()

    def getTaxaName(self, sequence):
        name = self.getDescStr(sequence)

        if len(name) == 0:
            raise SequenceWriterError('NEXUS files require either a description or file name for each sequence.')

        return "'" + name + "'"

    def writeCharactersBlock(self):
        self.fh.write('\nBEGIN CHARACTERS;\n')
        self.fh.write('    DIMENSIONS NCHAR=' + str(self.a_length) + ';\n')
        self.fh.write('    FORMAT DATATYPE=DNA GAP=- MISSING=N;\n')
        self.fh.write('    MATRIX\n')

        for sequence in self.a_sequences:
            self.fh.write('    ' + self.getTaxaName(sequence) + ' ')
            self.fh.write(sequence['seq'] + '\n')

        self.fh.write('    ;\nEND;')

    def writeUnalignedBlock(self):
        self.fh.write('\nBEGIN UNALIGNED;\n')
        self.fh.write('    FORMAT DATATYPE=DNA MISSING=N;\n')
        self.fh.write('    MATRIX\n')

        for sequence in self.u_sequences:
            self.fh.write('    ' + self.getTaxaName(sequence) + ' ')
            self.fh.write(sequence['seq'] + '\n')

        self.fh.write('    ;\nEND;')


# A file save/save as dialog that is aware of the various sequence formats
# supported by this module.  It can also display additional options to the user.
# Finally, it can ensure that all file names returned have an appropriate extension.
class SeqWriterFileDialog(gtk.FileChooserDialog):
    formats = {
            'FASTA (*.fasta)': [FORMAT_FASTA, '.fasta'],
            'NEXUS (*.nex)': [FORMAT_NEXUS, '.nex'],
            'plain text (*.txt)': [FORMAT_PLAINTEXT, '.txt']
            }

    def __init__(self, parent=None, title=None):
        gtk.FileChooserDialog.__init__(self, title, parent, gtk.FILE_CHOOSER_ACTION_SAVE,
                (gtk.STOCK_SAVE, gtk.RESPONSE_OK, gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))

        self.set_do_overwrite_confirmation(True)

        self.check_extension = True
        self.show_options = False

        # add file filters for the supported sequence formats
        for name, details in self.formats.items():
            ff = gtk.FileFilter()
            ff.set_name(name)
            ff.add_pattern('*' + details[1])
            self.add_filter(ff)

        # add a checkbox to allow the user to choose whether or not to include file names
        self.fnames_toggle = gtk.CheckButton("include trace file names in exported file")
        self.fnames_toggle.set_active(True)
        self.set_extra_widget(self.fnames_toggle)
        self.fnames_toggle.set_visible(self.show_options)

    def setCheckExtension(self, newval):
        self.check_extension = newval

    def setShowOptions(self, newval):
        self.show_options = newval
        self.fnames_toggle.set_visible(self.show_options)

    def getFileFormat(self):
        ff = self.get_filter()

        return self.formats[ff.get_name()][0]

    def getIncludeFileNames(self):
        return self.fnames_toggle.get_active()

    def get_filename(self):
        name = gtk.FileChooserDialog.get_filename(self)

        if name and self.check_extension:
            ff = self.get_filter()
            extension = self.formats[ff.get_name()][1]

            # make sure the file name has the proper extension for the chosen file type
            if not(name.endswith(extension)):
                name += extension

        return name

