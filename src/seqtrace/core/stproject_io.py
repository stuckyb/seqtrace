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


import pickle
from seqtrace.core.consens import ConsensSeqSettings


class SeqTraceProjWriter:
    """
    Writes project data to an external file.  The pickle module is currently
    used to serialize the data to a file, but no class instances are serialized
    directly.  Instead, only the relevant data are serialized, which makes the
    file format independent of any future changes to the names or structure of
    the project classes, modules, or packages.
    """
    def __init__(self):
        self.proj_data = {}
        self.proj_data['properties'] = {}
        self.proj_data['consseqsettings'] = {}
        self.proj_data['items'] = []

        self.proj_data['formatversion'] = '0.9'

    def addProperty(self, key, value):
        self.proj_data['properties'][key] = value

    def setConsensSeqSettings(self, settings):
        self.proj_data['consseqsettings']['min_confscore'] = settings.getMinConfScore()
        self.proj_data['consseqsettings']['consensus_algorithm'] = settings.getConsensusAlgorithm()
        self.proj_data['consseqsettings']['trim_consensus'] = settings.getTrimConsensus()
        self.proj_data['consseqsettings']['do_qualitytrim'] = settings.getDoQualityTrim()
        self.proj_data['consseqsettings']['qualitytrim_winsize'] = settings.getQualityTrimParams()[0]
        self.proj_data['consseqsettings']['qualitytrim_basecnt'] = settings.getQualityTrimParams()[1]
        self.proj_data['consseqsettings']['trim_endgaps'] = settings.getTrimEndGaps()
        self.proj_data['consseqsettings']['trim_primers'] = settings.getTrimPrimers()
        self.proj_data['consseqsettings']['primermatch_threshold'] = settings.getPrimerMatchThreshold()
        self.proj_data['consseqsettings']['forward_primer'] = settings.getForwardPrimer()
        self.proj_data['consseqsettings']['reverse_primer'] = settings.getReversePrimer()

    def addProjectItem(self, item):
        itemdata = ProjectItemData()
        itemdata.copyFromItem(item)
        self.proj_data['items'].append(itemdata.toDict())

    def write(self, filename):
        try:
            fout = open(filename, 'w')
        except:
            raise

        pickle.dump(self.proj_data, fout)
        fout.close()


class ReaderError(Exception):
    pass

class FileDataError(ReaderError):
    pass

class FileFormatVersionError(ReaderError):
    pass


class SeqTraceProjReader:
    def readFile(self, filename):
        try:
            fin = open(filename, 'r')
        except:
            raise

        try:
            self.proj_data = pickle.load(fin)
        except:
            raise FileDataError

        if 'formatversion' not in self.proj_data:
            raise FileDataError

        # Check the project data file format version.
        if self.proj_data['formatversion'] not in ('0.8', '0.9'):
            raise FileFormatVersionError

        # A simple check to make sure the required data are present.
        if (('properties' not in self.proj_data)
                or ('items' not in self.proj_data)
                or ('consseqsettings' not in self.proj_data)):
            raise FileDataError

    def getProperty(self, key):
        return self.proj_data['properties'][key]

    def getConsensSeqSettings(self):
        settings = ConsensSeqSettings()

        # Check if we got an old file format, and convert it if needed.
        if self.proj_data['formatversion'] == '0.8':
            self.convertSettings8To9()

        settings.setMinConfScore(self.proj_data['consseqsettings']['min_confscore'])
        settings.setConsensusAlgorithm(self.proj_data['consseqsettings']['consensus_algorithm'])

        settings.setTrimConsensus(self.proj_data['consseqsettings']['trim_consensus'])
        settings.setTrimEndGaps(self.proj_data['consseqsettings']['trim_endgaps'])

        settings.setTrimPrimers(self.proj_data['consseqsettings']['trim_primers'])
        settings.setPrimerMatchThreshold(self.proj_data['consseqsettings']['primermatch_threshold'])
        settings.setForwardPrimer(self.proj_data['consseqsettings']['forward_primer'])
        settings.setReversePrimer(self.proj_data['consseqsettings']['reverse_primer'])

        settings.setDoQualityTrim(self.proj_data['consseqsettings']['do_qualitytrim'])
        settings.setQualityTrimParams(
            self.proj_data['consseqsettings']['qualitytrim_winsize'], self.proj_data['consseqsettings']['qualitytrim_basecnt']
            )

        return settings

    def convertSettings8To9(self):
        """
        Converts a settings dictionary from the 0.8 format to the 0.9 format.
        """
        if self.proj_data['formatversion'] != '0.8':
            return

        # Handle settings for which the key name changed from 0.8 to 0.9.
        self.proj_data['consseqsettings']['do_qualitytrim'] = self.proj_data['consseqsettings']['do_autotrim']
        self.proj_data['consseqsettings']['qualitytrim_winsize'] = self.proj_data['consseqsettings']['autotrim_winsize']
        self.proj_data['consseqsettings']['qualitytrim_basecnt'] = self.proj_data['consseqsettings']['autotrim_basecnt']

        # Handle settings not included in the 0.8 version of the file format.
        self.proj_data['consseqsettings']['consensus_algorithm'] = 'legacy'
        self.proj_data['consseqsettings']['trim_consensus'] = self.proj_data['consseqsettings']['do_autotrim']
        self.proj_data['consseqsettings']['trim_primers'] = False
        self.proj_data['consseqsettings']['primermatch_threshold'] = 0.8
        self.proj_data['consseqsettings']['forward_primer'] = ''
        self.proj_data['consseqsettings']['reverse_primer'] = ''

    def __iter__(self):
        self.iter_index = 0
        return self

    def next(self):
        if self.iter_index < len(self.proj_data['items']):
            self.iter_index += 1
            item = ProjectItemData()
            item.fromDict(self.proj_data['items'][self.iter_index - 1])
            return item
        else:
            raise StopIteration


class ProjectItemData:
    def __init__(self):
        self.parent = None
        self.children = ()
        self.name = ''
        self.notes = ''
        self.itemtype = None
        self.has_cons = False
        self.use_cons = False
        self.compact_cons = ''
        self.full_cons = ''
        self.is_reverse = False

    def copyFromItem(self, item):
        self.setId(item.getId())
        self.setName(item.getName())
        self.setItemType(item.getItemType())
        self.setConsensusSequence(item.getCompactConsSequence(), item.getFullConsSequence())
        self.setHasSequence(item.hasSequence())
        self.setUseSequence(item.getUseSequence())
        self.setNotes(item.getNotes())
        self.setIsReverse(item.getIsReverse())
        
        children = item.getChildren()
        if len(children) == 2:
            child1 = ProjectItemData()
            child1.copyFromItem(children[0])
            child2 = ProjectItemData()
            child2.copyFromItem(children[1])

            self.setChildren(child1, child2)

    def toDict(self):
        """
        Convert the item's data, including any children, to a simple Python dictionary.
        The result will be similar, but not identical, to the __dict__ builtin.  This method
        is designed to be used for saving project data to an external file in a way that does
        not depend on package and module names and structures.  This makes it more robust than
        simply serializing a ProjectItemData instance directly.
        """
        res = {}
        res['id'] = self.getId()
        res['name'] = self.getName()
        res['itemtype'] = self.getItemType()
        res['compactcons'] = self.getCompactConsSequence()
        res['fullcons'] = self.getFullConsSequence()
        res['hasseq'] = self.hasSequence()
        res['useseq'] = self.getUseSequence()
        res['notes'] = self.getNotes()
        res['isreverse'] = self.getIsReverse()
        
        res['children'] = []
        children = self.getChildren()
        if len(children) == 2:
            res['children'].append(children[0].toDict())
            res['children'].append(children[1].toDict())

        return res

    def fromDict(self, dict_in):
        self.setId(dict_in['id'])
        self.setName(dict_in['name'])
        self.setItemType(dict_in['itemtype'])
        self.setConsensusSequence(dict_in['compactcons'], dict_in['fullcons'])
        self.setHasSequence(dict_in['hasseq'])
        self.setUseSequence(dict_in['useseq'])
        self.setNotes(dict_in['notes'])
        self.setIsReverse(dict_in['isreverse'])
        
        if len(dict_in['children']) == 2:
            child1 = ProjectItemData()
            child1.fromDict(dict_in['children'][0])
            child2 = ProjectItemData()
            child2.fromDict(dict_in['children'][1])

            self.setChildren(child1, child2)

    def getName(self):
        return self.name

    def setName(self, newname):
        self.name = newname

    def getItemType(self):
        return self.itemtype

    def setItemType(self, newtype):
        self.itemtype = newtype

    def isFile(self):
        return self.itemtype == 'file'

    def hasSequence(self):
        return self.has_cons

    def setHasSequence(self, newval):
        self.has_cons = newval

    def getUseSequence(self):
        return self.use_cons

    def setUseSequence(self, use_sequence):
        self.use_cons = use_sequence

    def setConsensusSequence(self, compact_consens, full_consens):
        self.compact_cons = compact_consens
        self.full_cons = full_consens

    def getCompactConsSequence(self):
        return self.compact_cons

    def getFullConsSequence(self):
        return self.full_cons

    def getId(self):
        return self.node_id

    def setId(self, newid):
        self.node_id = newid

    def getNotes(self):
        return self.notes

    def setNotes(self, newnotes):
        self.notes = newnotes

    def getChildren(self):
        return self.children

    def setChildren(self, item1, item2):
        self.children = (item1, item2)

    def getIsReverse(self):
        return self.is_reverse

    def setIsReverse(self, newval):
        self.is_reverse = newval

