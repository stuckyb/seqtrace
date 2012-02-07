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


import gtk
from seqtrace.gui.maingui import MainWindow

from optparse import OptionParser



argp = OptionParser(
        usage='''usage:  %prog [filename]
\n    If [filename] is provided and appears to be a project file
(from its extension), ___ will attempt to load the project.  Otherwise,
____ will treat the file as a sequencing trace file and attempt to load
the trace file directly.''')

# parse command-line arguments
(options, args) = argp.parse_args()
if len(args) == 0:
    filein = ''
elif len(args) > 1:
    argp.error('unrecognized command argument(s)')
else:
    filein = args[0]

mainwin = MainWindow()

if filein != '':
    # see if the file name looks like a project file
    if filein.endswith(mainwin.getFileExtension()):
        mainwin.openProject(filein)
    else:
        # not a project file, so attempt to open it as a sequence trace file
        mainwin.openTraceFile(filein)

gtk.main()

