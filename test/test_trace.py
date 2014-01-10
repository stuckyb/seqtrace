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


from seqtrace.core.sequencetrace import *

import unittest
import random
import os.path


# set the location of the test data files
test_data = os.path.dirname(__file__) + '/test_data/'


class TestSequenceTraceOpen(unittest.TestCase):
    def setUp(self):
        self.trace = ZTRSequenceTrace()

    def test_open(self):
        self.assertRaises(IOError, self.trace.loadFile, 'does_not_exist.ztr')


class TestSequenceTraceFactory(unittest.TestCase):
    def test_getTraceFileType(self):
        self.assertEqual(SequenceTraceFactory.getTraceFileType(test_data + 'forward.ztr'), ST_ZTR)
        self.assertEqual(SequenceTraceFactory.getTraceFileType(test_data + 'forward.ab1'), ST_ABI)
        self.assertEqual(SequenceTraceFactory.getTraceFileType(test_data + 'error-invalid_file.ztr'), ST_UNKNOWN)

    def test_error(self):
        self.assertRaises(UnknownFileTypeError, SequenceTraceFactory.loadTraceFile, test_data + 'error-invalid_file.ztr')


class TestSequenceTraceMethods(unittest.TestCase):
    """
    Defines tests for individual sequence trace methods that do not require
    actually loading a trace file.
    """
    def test_reverseCompBases(self):
        """
        Tests the reverse complement function for bases.
        """
        st = SequenceTrace()

        # A test case with all 4 single nucleotide codes and all 11 IUPAC ambiguity codes.
        st.basecalls = 'AWSCTCHGAMCTKRCTTBAYGCDATVT'
        st.reverseCompBases()
        self.assertEqual(st.basecalls, 'ABATHGCRTVAAGYMAGKTCDGAGSWT')

class TestSequenceTrace:
    """
    Defines tests that apply to all concrete subclasses of SequenceTrace.  This class should not be instantiated
    directly; only its subclasses that target concrete subclasses of SequenceTrace should be run.  To help reinforce
    this, TestSequenceTrace does not inherit from unittest.TestCase.  All subclasses of TestSequenceTrace should
    inherit from unittest.TestCase and treat TestSequenceTrace as a sort of "mixin" class that provides testing routines.
    """
    max_trace_val = 1856
    num_base_calls = 730
    trace_length = 10757
    base_calls = 'TCGTTTAGGAGCTTGATCTGGATAGTAGGAACTTCTTTAAGAATTCTTATTCGAGCTGAATTAGGACATCCAGGAGCACTAATTGGTGATGATCAAATTTATAATGTAATTGTTACAGCTCATGCATTTATTATAATTTTTTTTATAGTAATACCTATTATAATTGGAGGATTTGGAAATTGGTTAGTTCCAATTATATTAGGAGCTCCAGATATAGCTTTTCCACGAATAAATAATATAAGATTTTGGCTTCTTCCACCTGCTTTAACATTACTACTAGTGAGTAGTATAGTAGAAAATGGAGCTGGAACTGGATGAACTGTTTACCCTCCTCTATCATCTAATATCGCTCATGGTGGAGCTTCTGTTGATTTAGCAATTTTCTCTCTTCATTTAGCAGGAATCTCTTCTATTTTAGGAGCAGTTAATTTTATTACAACAGTTATTAATATACGATCTTCAGGAATTACCTTTGATCGAATACCTTTATTTGTTTGATCCGTAGTAATTACAGCTTTACTATTACTTCTTTCTTTACCGGTATTAGCAGGAGCAATTACTATATTATTAACAGATCGAAATATTAATACTTCATTTTTTGACCCTGCTGGAGGAGGAGATCCTATTTTATACCAACATTTATATTGATTCTTGTACAATATCAATTAACACGGGGGAAACGGTGCGTGGTAGTCGAAAACGTGAGGCGCGACATACGGTCAGGTAGCTA'

    rev_compl = 'TAGCTACCTGACCGTATGTCGCGCCTCACGTTTTCGACTACCACGCACCGTTTCCCCCGTGTTAATTGATATTGTACAAGAATCAATATAAATGTTGGTATAAAATAGGATCTCCTCCTCCAGCAGGGTCAAAAAATGAAGTATTAATATTTCGATCTGTTAATAATATAGTAATTGCTCCTGCTAATACCGGTAAAGAAAGAAGTAATAGTAAAGCTGTAATTACTACGGATCAAACAAATAAAGGTATTCGATCAAAGGTAATTCCTGAAGATCGTATATTAATAACTGTTGTAATAAAATTAACTGCTCCTAAAATAGAAGAGATTCCTGCTAAATGAAGAGAGAAAATTGCTAAATCAACAGAAGCTCCACCATGAGCGATATTAGATGATAGAGGAGGGTAAACAGTTCATCCAGTTCCAGCTCCATTTTCTACTATACTACTCACTAGTAGTAATGTTAAAGCAGGTGGAAGAAGCCAAAATCTTATATTATTTATTCGTGGAAAAGCTATATCTGGAGCTCCTAATATAATTGGAACTAACCAATTTCCAAATCCTCCAATTATAATAGGTATTACTATAAAAAAAATTATAATAAATGCATGAGCTGTAACAATTACATTATAAATTTGATCATCACCAATTAGTGCTCCTGGATGTCCTAATTCAGCTCGAATAAGAATTCTTAAAGAAGTTCCTACTATCCAGATCAAGCTCCTAAACGA'

    base_pos = [2, 20, 41, 57, 73, 101, 117, 129, 143, 154, 170, 181, 196, 203, 219, 233, 241, 256, 267, 283, 298, 314, 329,
            340, 353, 366, 377, 390, 405, 419, 428, 438, 450, 464, 477, 490, 504, 517, 528, 537, 549, 563, 573, 583, 596, 608, 621,
            634, 645, 657, 670, 683, 697, 708, 721, 733, 746, 758, 771, 782, 792, 805, 815, 829, 843, 855, 865, 875, 887, 900, 913,
            922, 935, 949, 963, 974, 987, 998, 1008, 1021, 1032, 1044, 1056, 1069, 1082, 1096, 1108, 1121, 1133, 1143, 1156, 1169,
            1179, 1192, 1201, 1213, 1224, 1236, 1249, 1261, 1272, 1284, 1294, 1306, 1318, 1332, 1344, 1355, 1367, 1378, 1391, 1404,
            1416, 1429, 1440, 1451, 1461, 1474, 1487, 1500, 1513, 1523, 1535, 1547, 1560, 1571, 1583, 1595, 1608, 1619, 1630, 1643,
            1654, 1666, 1677, 1688, 1701, 1713, 1726, 1738, 1751, 1763, 1776, 1788, 1798, 1809, 1820, 1833, 1846, 1857, 1868, 1880,
            1891, 1903, 1916, 1929, 1940, 1953, 1966, 1977, 1989, 2000, 2012, 2024, 2037, 2050, 2063, 2076, 2088, 2101, 2113, 2123,
            2135, 2147, 2160, 2174, 2186, 2197, 2209, 2220, 2232, 2245, 2258, 2270, 2282, 2293, 2306, 2318, 2330, 2342, 2354, 2364,
            2376, 2388, 2401, 2412, 2424, 2435, 2447, 2460, 2471, 2485, 2498, 2510, 2522, 2534, 2546, 2558, 2570, 2580, 2592, 2606,
            2617, 2628, 2639, 2651, 2664, 2676, 2689, 2701, 2713, 2726, 2737, 2749, 2759, 2770, 2782, 2795, 2807, 2819, 2830, 2841,
            2853, 2864, 2876, 2888, 2899, 2911, 2922, 2934, 2946, 2959, 2971, 2982, 2994, 3006, 3018, 3031, 3044, 3055, 3068, 3080,
            3092, 3103, 3115, 3127, 3139, 3149, 3160, 3172, 3185, 3196, 3209, 3222, 3234, 3245, 3256, 3267, 3279, 3289, 3301, 3313,
            3325, 3337, 3349, 3360, 3372, 3384, 3395, 3408, 3421, 3433, 3445, 3457, 3469, 3480, 3492, 3504, 3515, 3526, 3538, 3551,
            3563, 3574, 3587, 3599, 3611, 3622, 3634, 3645, 3657, 3670, 3682, 3694, 3706, 3718, 3730, 3743, 3755, 3766, 3777, 3789,
            3801, 3814, 3827, 3838, 3850, 3862, 3873, 3885, 3897, 3909, 3921, 3933, 3945, 3956, 3967, 3979, 3991, 4004, 4016, 4028,
            4040, 4052, 4064, 4075, 4086, 4098, 4108, 4120, 4132, 4145, 4155, 4167, 4179, 4190, 4201, 4214, 4227, 4239, 4251, 4263,
            4274, 4285, 4297, 4310, 4322, 4334, 4347, 4359, 4371, 4382, 4394, 4406, 4418, 4430, 4443, 4454, 4466, 4479, 4491, 4501,
            4513, 4525, 4536, 4549, 4560, 4572, 4583, 4595, 4607, 4619, 4631, 4643, 4655, 4667, 4680, 4691, 4704, 4715, 4727, 4738,
            4749, 4761, 4773, 4784, 4797, 4809, 4820, 4832, 4845, 4857, 4869, 4879, 4891, 4904, 4916, 4928, 4940, 4953, 4965, 4976,
            4987, 4999, 5011, 5023, 5034, 5047, 5060, 5071, 5083, 5095, 5106, 5119, 5130, 5142, 5154, 5166, 5177, 5189, 5201, 5213,
            5225, 5236, 5248, 5260, 5272, 5283, 5295, 5307, 5318, 5331, 5343, 5356, 5368, 5378, 5391, 5403, 5414, 5426, 5438, 5449,
            5461, 5474, 5486, 5499, 5510, 5523, 5535, 5548, 5560, 5571, 5583, 5596, 5608, 5620, 5630, 5643, 5654, 5666, 5678, 5690,
            5703, 5716, 5728, 5740, 5751, 5764, 5777, 5788, 5800, 5811, 5823, 5834, 5846, 5859, 5871, 5884, 5896, 5907, 5919, 5931,
            5945, 5955, 5968, 5980, 5993, 6005, 6015, 6028, 6040, 6054, 6065, 6077, 6089, 6101, 6112, 6124, 6135, 6148, 6160, 6171,
            6183, 6196, 6208, 6220, 6232, 6244, 6256, 6268, 6279, 6290, 6301, 6316, 6328, 6340, 6352, 6365, 6377, 6389, 6401, 6414,
            6426, 6437, 6450, 6462, 6474, 6485, 6497, 6510, 6523, 6535, 6546, 6557, 6570, 6582, 6595, 6606, 6618, 6630, 6643, 6655,
            6668, 6680, 6691, 6703, 6714, 6727, 6739, 6750, 6764, 6775, 6787, 6799, 6811, 6824, 6835, 6846, 6860, 6871, 6884, 6895,
            6907, 6920, 6932, 6943, 6956, 6970, 6981, 6993, 7005, 7015, 7027, 7038, 7050, 7062, 7075, 7087, 7099, 7111, 7123, 7136,
            7150, 7161, 7171, 7184, 7197, 7209, 7221, 7234, 7247, 7259, 7269, 7282, 7294, 7306, 7318, 7331, 7343, 7355, 7368, 7381,
            7391, 7404, 7416, 7427, 7440, 7452, 7463, 7475, 7485, 7496, 7508, 7520, 7531, 7539, 7556, 7569, 7581, 7592, 7603, 7614,
            7625, 7635, 7646, 7658, 7671, 7682, 7693, 7705, 7716, 7729, 7739, 7746, 7763, 7775, 7789, 7800, 7809, 7819, 7831, 7840,
            7859, 7871, 7881, 7894, 7904, 7914, 7926, 7936, 7946, 7957, 7968, 7981, 7993, 8011, 8023, 8041, 8052, 8061, 8071, 8088,
            8105, 8117, 8135, 8152, 8165, 8184, 8198, 8212, 8225, 8236, 8245, 8261, 8279, 8291, 8300, 8313, 8321, 8332, 8342, 8360,
            8374, 8387, 8396, 8414, 8423, 8436, 8448, 8460, 8472, 8488, 8501, 8509, 8518, 8530, 8544, 8557, 8572, 8584, 8593, 8606,
            8623, 8635, 8645, 8653, 8668, 8678, 8689, 8697, 8708, 8717, 8733, 8748, 8764, 8780, 8791, 8803, 8816, 8832]

    bc_conf = [3, 8, 4, 7, 6, 5, 4, 24, 15, 12, 28, 20, 13, 8, 43, 13, 24, 42, 36, 57, 42, 37, 13, 33, 36, 53, 53, 52, 61, 31,
            29, 33, 61, 61, 61, 53, 61, 39, 43, 47, 61, 61, 37, 55, 61, 61, 61, 49, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61,
            61, 61, 59, 59, 61, 61, 61, 61, 61, 61, 59, 49, 61, 61, 59, 61, 61, 61, 61, 61, 61, 61, 61, 61, 59, 59, 61, 61, 59, 59,
            61, 61, 61, 59, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 59, 61, 59, 61, 61, 59,
            59, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 59, 55, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 59, 61, 61, 61,
            61, 61, 61, 61, 61, 59, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 59, 59, 61, 61, 61, 61, 61, 59, 61, 61,
            61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 59, 61, 61, 59, 59, 45,
            61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 44, 59, 61, 59, 55, 59, 59, 61, 61, 61, 61, 59,
            59, 55, 55, 61, 61, 61, 59, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 59, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61,
            61, 59, 61, 61, 61, 61, 61, 59, 59, 36, 59, 61, 61, 61, 61, 61, 59, 61, 61, 61, 61, 61, 61, 61, 59, 61, 61, 61, 61, 61,
            61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 59,
            59, 59, 59, 61, 59, 59, 59, 61, 61, 59, 61, 61, 61, 61, 59, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 59, 61,
            61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 59, 61, 61, 59, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61,
            61, 59, 61, 61, 61, 61, 59, 59, 61, 49, 61, 61, 61, 61, 61, 61, 61, 61, 59, 55, 61, 61, 61, 61, 61, 61, 61, 59, 61, 61,
            61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61,
            61, 61, 61, 61, 61, 61, 61, 61, 61, 55, 55, 61, 55, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 55, 55,
            61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 47, 47, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61,
            61, 61, 53, 61, 61, 61, 61, 61, 61, 61, 61, 61, 47, 47, 61, 61, 61, 61, 53, 50, 50, 61, 53, 50, 61, 37, 61, 61, 61, 61,
            61, 61, 50, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 61, 57, 53, 53, 57, 57, 57, 43, 57, 57, 42, 53, 53, 57, 47, 57, 57,
            57, 57, 53, 57, 57, 53, 57, 53, 53, 57, 30, 42, 53, 47, 57, 53, 52, 53, 57, 57, 33, 34, 52, 50, 38, 57, 57, 57, 57, 57,
            57, 57, 47, 57, 57, 53, 57, 57, 57, 46, 57, 52, 39, 52, 57, 27, 57, 57, 50, 25, 18, 57, 57, 30, 30, 8, 30, 57, 50, 53,
            50, 53, 43, 34, 34, 52, 57, 37, 53, 57, 52, 37, 8, 4, 13, 41, 31, 36, 19, 34, 21, 11, 5, 4, 4, 4, 5, 5, 5, 5, 7, 5, 4,
            8, 7, 4, 4, 4, 5, 5, 5, 5, 4, 4, 5, 4, 4, 6, 16, 19, 8, 4, 4, 10, 8, 5, 12, 8, 12, 12, 18, 25, 14, 9, 7, 9, 9, 9, 10,
            12, 10, 13, 5, 16, 10, 6, 11, 7, 7, 5, 11, 7, 7, 5, 6, 8, 7, 12, 14, 7, 8, 7, 12, 29, 10, 5, 5, 5, 5, 7]

    start_tracesamps_A = [52, 54, 57, 62, 69, 76, 82, 85, 86, 86, 87, 90, 93, 96, 97, 97, 95, 93, 89, 86, 83, 80, 77, 73, 69,
            64, 59, 54, 49, 45, 40, 35, 31, 26, 22, 18, 15, 12, 9, 6, 4, 2, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            1, 1, 3, 4, 5, 6, 6, 6, 6, 6, 8, 11, 13, 16, 18, 19, 19, 19, 19, 20, 21, 23, 24, 25, 26, 26, 26, 26, 26, 27, 29, 30, 32,
            34, 36, 38, 39, 40, 40, 39, 38, 37, 36, 35, 36, 37, 37, 37, 37, 36, 35, 34, 35, 36, 37, 38, 39, 39, 38, 37, 37, 38, 38,
            38, 37, 36, 33, 31, 29, 27, 25, 24, 23, 25, 28, 35, 46, 61, 80, 103, 129, 158, 189, 224, 262, 302, 345, 390, 434, 477,
            515, 546, 569, 582, 583, 575, 556, 529, 495, 455, 411, 364, 316, 269, 224, 182, 144, 112, 84, 61, 43, 30, 21, 15, 12,
            10, 9, 8, 7, 7, 7, 8, 8, 10, 11, 13, 15, 18, 20, 23, 25, 28, 31, 34, 38, 42, 47, 52, 56, 59, 60, 61, 60, 58, 55, 51, 47,
            43, 39, 35, 32, 29, 27, 27, 27, 30, 36, 45, 60, 81, 110, 148, 195, 250, 311, 375, 439, 499, 553, 598, 631, 650, 655,
            643, 617, 576, 523, 461, 393, 323, 255, 193, 139, 96, 63, 40, 26, 18, 14, 12, 11, 10, 10, 9, 9, 9, 10, 11, 12, 13, 15,
            15, 15, 14, 14, 14, 15, 18, 22, 26, 30, 34, 39, 44, 49, 55, 61, 67, 71, 73, 73, 71, 67, 63, 57, 51, 44, 38, 31, 25, 20,
            15, 10, 6, 2, 0, 0, 6, 21, 47, 86, 139, 206, 288, 384, 491, 606, 724, 838, 941, 1029, 1097, 1143, 1168, 1174, 1163,
            1139, 1103, 1056, 1000, 934, 858, 772, 677, 579, 481, 391, 317, 266, 242, 248, 284, 347, 433, 533, 637, 736, 817, 873,
            895, 881, 834, 758, 661, 553, 443, 339, 247, 171, 113, 72, 46, 32, 26, 26, 29, 32, 34, 36, 36, 34, 32, 29, 28, 32, 44,
            67, 105, 160, 232, 320, 421, 528, 632, 721, 785, 817, 812, 772, 700, 606, 500, 391, 288, 198, 125, 70, 33, 11, 0, 0, 0,
            3, 7, 10, 12, 12, 11, 9, 7, 5, 3, 1, 0, 0, 0, 7, 26, 62, 120, 201, 307, 433, 576, 724, 868, 992, 1084, 1137, 1148, 1122,
            1071, 1010, 951, 903, 868, 841, 813, 778, 727, 658, 574, 481, 385, 294, 214, 148, 97, 62, 39, 26, 19, 16, 14, 13, 13,
            13, 14, 16, 19, 23, 26, 29, 30, 30, 28, 25, 21, 18, 16, 14, 14, 15, 15, 16, 16, 15, 13, 11, 10, 9, 9, 10, 10, 11, 12,
            13, 15, 18, 21, 25, 28, 31, 32, 31, 29, 25, 19, 14, 10, 7, 6, 7, 9, 13, 16, 18, 19, 20, 19, 18, 16, 14, 13, 12, 12, 13,
            14, 14, 14, 12, 9, 6, 2, 0, 0, 6, 22, 52, 98, 161, 239, 327, 416, 496, 559, 599, 615, 610, 591, 568, 550, 540, 541, 548,
            554, 552, 534, 494, 433, 355, 267, 181, 105, 49, 15, 0, 0, 0, 1, 0, 0, 12, 55, 138, 269, 443, 648, 865, 1066, 1228,
            1329, 1357, 1314, 1212, 1075, 931, 806, 718, 672, 661, 667, 670, 654, 608, 531, 430, 320, 215, 126, 62, 23, 4, 0, 0, 4,
            8, 13, 18, 25, 33, 41, 48, 53, 55, 57, 57, 56, 54, 52, 48, 42, 36, 29, 22, 17, 14, 13, 12, 12, 12, 11, 10, 8, 5, 3, 1,
            0, 0, 0, 0, 1, 2, 2, 3, 2, 0, 0, 0, 0, 1, 2, 1, 0, 0, 7, 38, 101, 201, 333, 488, 646, 784, 881, 922, 899, 816, 686, 530,
            370, 228, 119, 47, 10, 0, 0, 2, 5, 7, 7, 7, 7, 7, 6, 4, 1, 0, 1, 3, 7, 11, 13, 13, 11, 8, 4, 1, 0, 0, 0, 1, 1, 0, 0, 0,
            3, 10, 20, 31, 38, 41, 39, 33, 25, 17, 10, 2, 0, 0, 13, 56, 137, 260, 418, 594, 761, 891, 961, 957, 880, 745, 575, 399,
            243, 124, 47, 9, 0, 0, 4, 7, 6, 4, 1, 0, 0, 1, 3, 5, 9, 15, 21, 29, 36, 42, 45, 46, 44, 41, 38, 34, 31, 28, 26, 24, 22,
            22, 22, 24, 26, 26, 23, 17, 9, 2, 0, 0, 2, 5, 3, 0, 0, 16, 70, 175, 333, 531, 742, 929, 1058, 1105, 1063, 950, 798, 647,
            534, 483, 497, 557, 634, 693, 707, 663, 567, 437, 298, 174, 82, 25, 0, 0, 4, 16, 27, 34, 38, 37, 33, 25]

    def test_dataLoaded(self):
        # test several properties of the loaded data
        self.assertEqual(self.trace.getNumBaseCalls(), self.num_base_calls)
        self.assertEqual(self.trace.getTraceLength(), self.trace_length)
        self.assertEqual(self.trace.getMaxTraceVal(), self.max_trace_val)

        # test if the base calls are correct
        self.assertEqual(self.trace.getBaseCalls(), self.base_calls)

        for cnt in range(len(self.base_calls)):
            self.assertEqual(self.trace.getBaseCall(cnt), self.base_calls[cnt])

        # test if the base call locations are correct
        for cnt in range(len(self.base_pos)):
            self.assertEqual(self.trace.getBaseCallPos(cnt), self.base_pos[cnt])

        # test if the confidence scores are correct
        for cnt in range(len(self.bc_conf)):
            self.assertEqual(self.trace.getBaseCallConf(cnt), self.bc_conf[cnt])

        # test if the loaded trace values are correct (only tests the first 800 sample values)
        for cnt in range(len(self.start_tracesamps_A)):
            self.assertEqual(self.trace.getTraceSample('A', cnt), self.start_tracesamps_A[cnt])

    def test_getFileName(self):
        self.assertEqual(self.trace.getFileName(), os.path.basename(self.filename))

    def test_reverseComplement(self):
        self.assertFalse(self.trace.isReverseComplemented())

        # test reverse complementing
        self.trace.reverseComplement()
        self.assertTrue(self.trace.isReverseComplemented())
        self.assertEqual(self.trace.getBaseCalls(), self.rev_compl)

        # test reverse complementing back to the original
        self.trace.reverseComplement()
        self.assertFalse(self.trace.isReverseComplemented())
        self.assertEqual(self.trace.getBaseCalls(), self.base_calls)

    def test_getPrevBaseCallIndex(self):
        # test that exact base call locations work
        for cnt in range(len(self.base_pos)):
            index = self.trace.getPrevBaseCallIndex(self.base_pos[cnt])
            self.assertEqual(index, cnt)

        # test that non-base call locations work
        for cnt in range(len(self.base_pos) - 1):
            # randomly pick a sample between the base call locations of cnt and cnt + 1
            distance = self.base_pos[cnt + 1] - self.base_pos[cnt]
            sampnum = random.randint(1, distance - 1) + self.base_pos[cnt]

            # see if we get the correct base call index back
            index = self.trace.getPrevBaseCallIndex(sampnum)
            self.assertEqual(index, cnt)

        # test extreme values at the beginning and end of the trace
        index = self.trace.getPrevBaseCallIndex(1)
        self.assertEqual(index, 0)
        endsamp = self.base_pos[len(self.base_calls) - 1] + 2
        index = self.trace.getPrevBaseCallIndex(endsamp)
        self.assertEqual(index, len(self.base_calls) - 1)

    def test_getNextBaseCallIndex(self):
        # test that exact base call locations work
        for cnt in range(len(self.base_pos)):
            index = self.trace.getNextBaseCallIndex(self.base_pos[cnt])
            self.assertEqual(index, cnt)

        # test that non-base call locations work
        for cnt in range(len(self.base_pos) - 1):
            # randomly pick a sample between the base call locations of cnt and cnt + 1
            distance = self.base_pos[cnt + 1] - self.base_pos[cnt]
            sampnum = random.randint(1, distance - 1) + self.base_pos[cnt]

            # see if we get the correct base call index back
            index = self.trace.getNextBaseCallIndex(sampnum)
            self.assertEqual(index, cnt + 1)

        # test extreme values at the beginning and end of the trace
        index = self.trace.getNextBaseCallIndex(1)
        self.assertEqual(index, 0)
        endsamp = self.base_pos[len(self.base_calls) - 1] + 2
        index = self.trace.getNextBaseCallIndex(endsamp)
        self.assertEqual(index, len(self.base_calls) - 1)

    def test_comments(self):
        self.assertEqual(self.trace.getComment('BCAL'), 'KB.bcp')
        self.assertEqual(self.trace.getComment('DATE'), 'Sat 12 Feb 17:31:32 2011 to Sat 12 Feb 18:28:03 2011')
        self.assertEqual(self.trace.getComment('DYEP'), 'KB_3730_POP7_BDTv3.mob')
        self.assertEqual(self.trace.getComment('LANE'), '1')
        self.assertEqual(self.trace.getComment('MACH'), 'AG-16113-006')
        self.assertEqual(self.trace.getComment('MODL'), '3730')
        self.assertEqual(self.trace.getComment('NAME'), 'O1')
        self.assertEqual(self.trace.getComment('RUND'), '20110212.173132 - 20110212.182803')
        self.assertEqual(self.trace.getComment('SIGN'), 'A=2828,C=2611,G=1599,T=5202')
        self.assertEqual(self.trace.getComment('VER1'), '3.0')
        self.assertEqual(self.trace.getComment('VER2'), 'KB 1.2')


class TestZTRSequenceTrace(unittest.TestCase, TestSequenceTrace):
    def setUp(self):
        self.filename = test_data + 'forward.ztr'

        self.trace = ZTRSequenceTrace()
        self.trace.loadFile(self.filename)

    # This does not attempt to test every possible error that can be raised while reading a ZTR file.
    # Doing so would require a ridiculous number of test files.  Instead, it just tests the most likely
    # errors.
    def test_errors(self):
        self.assertRaises(ZTRVersionError, self.trace.loadFile, test_data + 'error-wrong_version.ztr')
        self.assertRaises(ZTRMissingDataError, self.trace.loadFile, test_data + 'error-damaged_file.ztr')

    def test_comments(self):
        super(TestZTRSequenceTrace, self).test_comments()

        # The Staden code seems to add an extra ' ' at the end of the spacing value, so we need to 
        # customize that test in the subclasses.
        self.assertEqual(self.trace.getComment('SPAC'), '12.91 ')


class TestABISequenceTrace(unittest.TestCase, TestSequenceTrace):
    def setUp(self):
        self.filename = test_data + 'forward.ab1'

        self.trace = ABISequenceTrace()
        self.trace.loadFile(self.filename)

    # This does not attempt to test every possible error that can be raised while reading an ABI file.
    # Doing so would require a ridiculous number of test files.  Instead, it just tests the most likely
    # errors.
    def test_errors(self):
        self.assertRaises(ABIVersionError, self.trace.loadFile, test_data + 'error-wrong_version.ab1')
        self.assertRaises(ABIIndexError, self.trace.loadFile, test_data + 'error-bad_index.ab1')

    # Test a trace file where the user-edited base calls differ from the basecaller-assigned base calls.
    # In this case, the user-edited base calls should be used.
    def test_mismatch_bases(self):
        self.trace.loadFile(test_data + 'mismatch_base_calls.ab1')
        self.assertEqual(self.trace.getBaseCalls(), self.base_calls)

    def test_comments(self):
        super(TestABISequenceTrace, self).test_comments()

        # The Staden code seems to add an extra ' ' at the end of the spacing value, so we need to 
        # customize that test in the subclasses.
        self.assertEqual(self.trace.getComment('SPAC'), '12.91')

        # a few tests that are specific to the ABI test file
        self.assertEqual(self.trace.getComment('Data coll. dates/times'), 'Sat 12 Feb 17:51:01 2011 to Sat 12 Feb 18:28:01 2011')
        self.assertEqual(self.trace.getComment('Run name'), 'Run_AG_2011-02-12_17-31_0662')


class TestSCFSequenceTrace(unittest.TestCase, TestSequenceTrace):
    def setUp(self):
        self.filename = test_data + 'forward.scf'

        self.trace = SCFSequenceTrace()
        self.trace.loadFile(self.filename)

    def test_errors(self):
        self.assertRaises(SCFVersionError, self.trace.loadFile, test_data + 'error-wrong_version.scf')
        self.assertRaises(SCFError, self.trace.loadFile, test_data + 'error-bad_samp_size.scf')
        self.assertRaises(SCFError, self.trace.loadFile, test_data + 'error-bad_codeset.scf')
        self.assertRaises(SCFError, self.trace.loadFile, test_data + 'error-base_call_locs.scf')
        self.assertRaises(SCFDataError, self.trace.loadFile, test_data + 'error-missing_bases.scf')
        self.assertRaises(SCFError, self.trace.loadFile, test_data + 'error-missing_comments.scf')

    def test_comments(self):
        super(TestSCFSequenceTrace, self).test_comments()

        # The Staden code seems to add an extra ' ' at the end of the spacing value, so we need to 
        # customize that test in the subclasses.
        self.assertEqual(self.trace.getComment('SPAC'), '12.91 ')





if __name__ == '__main__':
    #unittest.main()
    suite = unittest.defaultTestLoader.loadTestsFromName(__name__)
    unittest.TextTestRunner(verbosity=2).run(suite)

