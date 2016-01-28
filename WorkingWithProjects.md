# Working with SeqTrace projects #

SeqTrace projects provide a convenient way to organize your work and allow you to quickly process large numbers of trace files.  Furthermore, setting up a project is required in order to take advantage of SeqTrace's more advanced features, such as automatic end quality trimming and forward/reverse trace matching.  Projects also allow you to save your work to an external SeqTrace project file.

From start to finish, using a SeqTrace project will usually proceed with the following work flow.
  1. [Create a new project.](WorkingWithProjects#Creating_a_new_project.md)
  1. [Add your trace files to the project.](WorkingWithProjects#Adding_trace_files_to_the_project.md)
  1. [Identify and group matching forward and reverse trace files.](WorkingWithProjects#Identifying_and_grouping_matching_forward_and_reverse_trace_file.md)
  1. [Adjust settings for generating finished sequences.](WorkingWithProjects#Adjusting_settings_for_generating_finished_sequences.md)
  1. [Process all trace files in the project.](WorkingWithProjects#Processing_all_trace_files_in_the_project.md)
  1. [Export the resulting finished sequences.](WorkingWithProjects#Exporting_the_finished_sequences.md)

This document discusses each of these steps in detail.  Note:  SeqTrace can only have one project open at a time.  However, you can easily work on two or more projects simultaneously by simply launching another instance of SeqTrace.

## Creating a new project ##

From the main SeqTrace window, select "New project.." from the "File" menu, or click the corresponding toolbar button.  SeqTrace will then display the project settings window for the new project.

![http://seqtrace.googlecode.com/svn/wiki/images/project_settings-1.png](http://seqtrace.googlecode.com/svn/wiki/images/project_settings-1.png)

There are two pieces of information that are important for setting up the new project, indicated by the numbered circles in the image above.
  1. You need to tell SeqTrace where your sequencing trace files are located.  You can either type in a directory name or click "Choose..." to select one.  The "use relative folder path" checkbox tells SeqTrace how to remember the trace file location.  If this box is checked, then SeqTrace will save the location of the trace file folder relative to the location of the project file.  This is useful if you later move the project file and trace files to a different location on your system or a different computer.  If you use this option and then use "Save project" or "Save project as..." to change the location of the project file, the relative directory path will automatically be updated to correspond with the project file's location.  If this box is not checked, SeqTrace will use the absolute path to the trace file location.
  1. If your project has both forward and reverse sequencing reads of the same PCR products, then you will want to tell SeqTrace how to identify which trace files are forward reads and which are reverse reads.  Usually, the sequencing trace filenames indicate whether the file is a forward or reverse read, and you can specify the portion of the filename that identifies the direction of the read.  SeqTrace will then automatically identify trace files as forward or reverse sequences.

For now, you can just accept the default values for the other project settings.

## Adding trace files to the project ##

Adding files to the project is simple.  Select "Add trace file(s)..." from the "Traces" menu, or click the corresponding toolbar button, then select the sequencing trace files you want to add.  You can also remove trace files from the project by selecting the file or files you want to remove in the project window, then choosing "Remove selected trace file(s)" from the "Traces" menu.

![http://seqtrace.googlecode.com/svn/wiki/images/project_window-1.png](http://seqtrace.googlecode.com/svn/wiki/images/project_window-1.png)

The image above shows the main SeqTrace window after adding several trace files to a new project.  Each of the columns in the list of trace files, numbered in the image above, is explained below.
  1. This column contains the file name or group name (explained in the next section).  Note that you can click on the column heading of this or any other column to sort the file list by that column.
  1. Here, you can type any notes about the trace file, such as a specimen number, primer information, etc.  Notes are saved along with the rest of the project.
  1. This column indicates whether a finished sequence has been saved for the trace file.  "Finished sequence" means a DNA sequence after removing low-quality base calls, end trimming, etc.
  1. This column contains a checkbox that indicates if you want to use the finished sequence when you export the DNA sequences to an external file.  For example, if you determine that a particular PCR product did not sequence properly, you will want to leave this unchecked.

## Identifying and grouping matching forward and reverse trace files ##

If you correctly set the forward and reverse search strings in the project settings, SeqTrace will automatically identify the direction of the sequencing reads when you add files to the project.  If not, you can open the project settings (File -> Project settings...), set the correct search strings, then have SeqTrace re-identify forward and reverse files (Traces -> Find and mark forward/reverse).

An arrow next to the trace file's name indicates whether SeqTrace thinks the file is a forward or reverse sequencing read.  A right-pointing blue arrow (![http://seqtrace.googlecode.com/svn/wiki/images/forward_arrow.png](http://seqtrace.googlecode.com/svn/wiki/images/forward_arrow.png)) identifies a forward sequence; a left-pointing orange arrow (![http://seqtrace.googlecode.com/svn/wiki/images/reverse_arrow.png](http://seqtrace.googlecode.com/svn/wiki/images/reverse_arrow.png)) identifies a reverse sequence.

You can also manually specify whether a trace file is a forward or reverse read.  Clicking on the indicator arrow next to the trace file name will toggle the arrow's direction and whether the sequence is treated as a forward or reverse sequencing read.

Next, you can group together matching forward and reverse trace files (that is, forward and reverse reads of the same PCR product).  SeqTrace can attempt to automatically identify and group matching forward and reverse reads by looking for trace files with matching file names (besides the part of the name that indicates forward or reverse).  To have SeqTrace automatically group matching forward and reverse files, choose one of the "Auto-group trace files" options from the "Traces" menu.

To manually group matching forward and reverse files together, first select the two files you want to group.  You can do this by holding down the CTRL key while clicking on the file names.  Then, choose "Group selected forward/reverse files" from the "Traces" menu.  You will then be prompted to provide a name for the new group.

![http://seqtrace.googlecode.com/svn/wiki/images/project_window-2.png](http://seqtrace.googlecode.com/svn/wiki/images/project_window-2.png)

The image above shows the same project illustrated previously after grouping together matching forward and reverse trace files.  The bottom two groups are expanded to show their file names.

## Adjusting settings for generating finished sequences ##

You can view any file or forward/reverse group in your project by selecting it in the project window, then choosing "View selected trace file(s)..." from the "Traces" menu or clicking on the corresponding toolbar button.  This will open the trace file or group in the trace view window.  For more information about using the trace view window, read the [quick start guide](QuickStartGuide.md) or the [full trace window documentation](TraceViewWindow.md).

Sequence traces that are identified as reverse reads will automatically be reverse complemented before being displayed in the trace view window.  If you select a forward/reverse group to display, the forward and reverse reads will display together in the trace view window, along with an alignment of the two sequences and a single consensus sequence.

After inspecting several of the files in your project, you might want to adjust the settings that SeqTrace uses to generate finished sequences from the trace files.  Select "Project settings..." from the "File" menu or click the settings toolbar button to open the project settings window.

![http://seqtrace.googlecode.com/svn/wiki/images/project_settings-2.png](http://seqtrace.googlecode.com/svn/wiki/images/project_settings-2.png)

There are four settings that control how SeqTrace generates finished sequences from the "raw" base call reads in a trace file.

  1. The minimum confidence score indicates the threshold for what SeqTrace considers to be a "good" base call.  Base calls with confidence scores below this threshold will either be removed from the finished sequence (if they are at one of the ends) or replaced with an "N".
  1. This checkbox controls whether or not SeqTrace will trim the ends of the finished sequence to eliminate regions with a high percentage of low-quality base calls.
  1. If automatic end trimming is enabled (2, above), these two settings specify the number of low-quality base calls SeqTrace will allow at the ends of the finished sequence.
  1. This setting only applies to consensus sequences generated from aligned forward and reverse sequencing reads.  If enabled, this setting will cause SeqTrace to eliminate the ends of the finished sequence that are not supported by both reads.  In other words, the end gap regions of the alignment, where the two sequences do not overlap, will be removed.  This ensures the highest quality consensus sequence and should also guarantee that no primer sequence will be present in the finished sequence.

After adjusting SeqTrace's sequence settings, you can tell SeqTrace to re-calculate the working sequence to see how the new settings change the finished sequence (in the trace view window, choose Edit -> Recalculate working seq.).

## Processing all trace files in the project ##

Once you have the sequence settings correctly adjusted, you can tell SeqTrace to generate finished sequences for all of the files or forward/reverse groups in your project.  Simply choose one of the "Generate finished sequences" options from the "Sequences" menu.  You can either select files in the project window (hold down the CTRL key to select multiple files or groups) or have SeqTrace generate finished sequences for all files or groups in the project.

After generating finished sequences, it's a good idea to inspect them in the trace view window to make sure that everything worked as expected.  If not, you can adjust the sequence settings and re-calculate the finished sequences, or edit the finished sequences by hand in the trace view window.

## Exporting the finished sequences ##

If you are satisfied with your finished sequences, then the final step is to export the sequences to a format you can use with other software for further analyses.  Choose one of the "Export sequences" options from the "Sequences" menu, or click the export toolbar button.  Then, provide a file name, choose a file format (FASTA, etc.), and click "Save".  Note also that there is a checkbox in the save dialog that lets you specify whether or not you want the sequence trace file names included in the exported sequence file.