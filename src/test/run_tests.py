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


import sys
import os.path
import glob
import unittest
from argparse import ArgumentParser


# Make sure we can find the seqtrace modules.
seqtrace_dir = os.path.normpath(
    os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        '../'
    )
)
sys.path.append(seqtrace_dir)

# Discover all of the test module names.
testmod_fnames = glob.glob('test_*.py')
test_modules = [os.path.splitext(fname)[0] for fname in testmod_fnames]

# Define the command-line arguments.  The interface is simple -- there is a
# single positional argument that is the name of a single test module to run.
# This argument can be repeated to specify a set of test modules to run.  If no
# module names are provided, all test modules will be run.
argp = ArgumentParser(description="Runs SeqTrace's tests.")
argp.add_argument(
    'module_name', type=str, nargs='*', help='A test module to run.  Must be '
    'one of ({0}).'.format('"' + '", "'.join(sorted(test_modules)) + '"')
)

args = argp.parse_args()

for module_name in args.module_name:
    if module_name not in test_modules:
        print ('\nERROR: The name "{0}" is not a valid test module name.  Valid '
        'module names are:\n{1}.\n'.format(
            module_name, '"' + '"\n"'.join(sorted(test_modules)) + '"'
        ))
        sys.exit(1)

# Implements a very simple test runner for all test modules.  This could
# probably be done even more easily using a package such as nose, but the
# advantage here is that only unittest methods are needed, so the test suites
# are very easy to run on any platform without needing to install additional
# packages.

successful = True
total = failed = 0

runner = unittest.TextTestRunner(verbosity=2)

if len(args.module_name) > 0:
    mods_to_run = args.module_name
else:
    mods_to_run = test_modules

for test_module in mods_to_run:
    suite = unittest.defaultTestLoader.loadTestsFromName(test_module)
    res = runner.run(suite)

    total += res.testsRun
    # Get the approximate number of failed tests.  This is an approximation
    # because a single test might both trigger an exception and an assert*()
    # failure, depending on how the test is configured.
    failed += len(res.errors) + len(res.failures)

    if not res.wasSuccessful():
        successful = False


if successful:
    if total != 1:
        print '\n\n{0} tests were run.  All tests completed successfully.\n'.format(total)
    else:
        print '\n\n1 test was run.  All tests completed successfully.\n'
else:
    if total != 1:
        msgstr = '\n\nFAILED:  {0} tests were run, resulting in '.format(total)
        if failed == 1:
            msgstr += '1 test failure or unexpected exception.'
        else:
            msgstr += '{0} test failures or unexpected exceptions.'.format(failed)
        
        print msgstr + '  See output above for details.\n'
    else:
        print ('\n\nFAILED:  1 test was run.  The test was unsuccessful.  See '
            + 'output above for details.\n')

