# Using the trace view window #

The trace view window allows you to view sequencing chromatograms, base calls, and quality scores, and edit the final DNA sequence.  This document provides more comprehensive documentation for the trace view window than the brief treatment found in the [quick start guide](QuickStartGuide.md).

Let's take a look at the trace view window for a matched pair of forward and reverse sequencing reads.  Each numbered item on the image is explained in detail below.

![http://seqtrace.googlecode.com/svn/wiki/images/traceview_window-full.png](http://seqtrace.googlecode.com/svn/wiki/images/traceview_window-full.png)

  1. file information toolbar button:  This button launches a separate window that displays detailed information about the trace file (or in this case, both trace files).  This is equivalent to selecting "Information..." from the "File" menu.
  1. save sequence toolbar button:  Saves the working sequence as a finished sequence in the project.  "Save working sequence to project" in the "File" menu does the same thing.  If you close the trace view window and later re-open it, the working sequence will be exactly as it was when you saved it to the project.  This feature is only available when trace files are opened from within a SeqTrace project.
  1. A drop-down list that specifies if the zoom, y-axis scale, and confidence score controls should be applied to one or both sequencing traces.  If only one trace file is displayed in the trace view window (i.e., not a forward/reverse group), this control is not visible.
  1. zoom controls:  You can either use the +/- buttons to zoom in or out incrementally, or choose a zoom level from the drop-down list.
  1. This slider controls the scale of the y-axis on the chromatogram display.  It can only be applied to one sequence at a time, so if a forward/reverse group is displayed, you must choose either the forward or reverse sequence from the drop-down list described in 3 above.
  1. chromatogram display:  This panel displays the actual sequencing chromatogram.  The base calls are indicated beneath each peak, and the quality scores for the base calls are given above the peaks.  The color of the quality score and the size of the gray bar behind it provide visual indicators of the quality score.  Low scores are red and have a very short bar, while high scores are blue and have a longer bar.  Notice also that the forward and reverse traces are identified.  Reverse traces are automatically reverse complemented prior to display.
  1. "raw" base calls:  Displays the unmodified base calls as stored in the trace file.  In the case of a forward/reverse pair (as shown in the illustration), SeqTrace does a pairwise alignment of the two sequences first.  You can click on any base and the chromatogram views will jump to and highlight the corresponding peaks.
  1. working sequence:  This is the sequence after SeqTrace has computed a consensus sequence from the forward and reverse reads, filtered out low quality base calls, quality trimmed the sequence ends, and after any user edits.  You can use the mouse to select one or more bases from the working sequence and delete them or edit them manually (e.g., replace one base with another).  The working sequence is the sequence that is saved to the project when you click the save toolbar button (or choose File -> Save working sequence to project).

The trace view window supports multi-level undo and redo of all edits made to the working sequence.  Note, though, that if you close the trace view window, the undo history for the working sequence is lost.

If you have a working sequence open in a trace view window and you change the project's sequence processing settings, you will probably want to update the working sequence to reflect the changes.  You can do this by choosing "Recalculate working seq." from the "Edit" menu.

Finally, there are several export options available in the "File" menu.  These allow you to export the working sequence, the raw base calls, or the forward/reverse alignment to a variety of file formats, such as FASTA.