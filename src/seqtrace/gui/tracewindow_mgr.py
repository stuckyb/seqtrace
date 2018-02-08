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


from seqtrace.gui.tracewindow import TraceWindow


class TraceWindowManager:
    """
    Keeps track of all open trace windows and handles tasks such as checking if
    a window is already open for a given trace file from a project, closing all
    open windows, etc.
    """
    def __init__(self):
        self.tracewindows = {}
        self.last_id = 0

    def newTraceWindow(self, mod_cons_seq, project_rowid=-1):
        newwin = TraceWindow(mod_cons_seq, is_mainwindow=False, id_num=self.last_id)
        newwin.connect('destroy', self.traceWindowDestroyed)

        self.tracewindows[self.last_id] = (newwin, project_rowid)
        self.last_id += 1

        return newwin

    def findByItemId(self, rowid):
        for tw_id in self.tracewindows.keys():
            if self.tracewindows[tw_id][1] == rowid:
                return self.tracewindows[tw_id][0]

        return None

    def getItemId(self, tracewindow):
        tw_id = tracewindow.getIdNum()

        return self.tracewindows[tw_id][1]

    def closeByItemId(self, rowid):
        tw = self.findByItemId(rowid)

        if tw != None:
            tw.destroy()

    def closeProjectTraceWindows(self):
        # close all project-related trace windows that are still open
        idnums = self.tracewindows.keys()
        for idnum in idnums:
            if self.tracewindows[idnum][1] != -1:
                self.tracewindows[idnum][0].destroy()

    def closeAllTraceWindows(self):
        # close any trace windows that are still open
        idnums = self.tracewindows.keys()
        for idnum in idnums:
            self.tracewindows[idnum][0].destroy()

    def traceWindowDestroyed(self, window):
        idnum = window.getIdNum()
        #print idnum
        del self.tracewindows[idnum]

