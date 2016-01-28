# Getting started with SeqTrace #

This document provides a streamlined introduction to using SeqTrace.  For a more in-depth discussion of SeqTrace and its features, see the "Using SeqTrace" wiki pages.

## Installing SeqTrace ##

Obviously, you will need to install SeqTrace first.  This is usually a simple process that might not involve much more than downloading the latest SeqTrace release and uncompressing the archive, depending on your system.  See the [installation guide](Installation.md) for details and follow the instructions for your operating system.

Some users will be interested in improving SeqTrace's performance or running SeqTrace's unit tests; these topics are covered in the [advanced installation instructions](AdvancedInstallationTopics.md).  Most users will not need to worry about these more complicated tasks.

## Viewing sequencing trace files ##

If you only have a small number of trace files to process or you simply want to view a sequencing chromatogram, you can open trace files directly in SeqTrace without first creating a SeqTrace project.  From the "File" menu, select "Open trace file...", then choose a trace file to open.  This will open the sequencing file and display it in the trace view window.

From the trace view window, you can:
  * zoom and scroll the sequencing chromatogram
  * edit the called DNA bases
  * export the DNA sequence to other file formats, such as FASTA.

![http://seqtrace.googlecode.com/svn/wiki/images/traceview_window-simple.png](http://seqtrace.googlecode.com/svn/wiki/images/traceview_window-simple.png)

The key components of the trace view window are numbered in the image above.
  1. chromatogram: This is the sequencing chromatogram, with the quality scores depicted above the peaks.  You can use the toolbar to zoom the view in and out and adjust the y-axis scale.
  1. "raw" sequence:  The unmodified DNA sequence as identified by the base caller and stored in the trace file.  You can click on any base to make the chromatogram view jump to the corresponding peak.
  1. working sequence:  This is the sequence after the removal of low-quality base calls, end trimming, and any other user edits.  You can select one or more bases on the working sequence and edit them directly.

For more information about the trace view window, see the [detailed explanation](TraceViewWindow.md) of its features and controls.

## Working with SeqTrace projects ##

If you have a large number of trace files to process, or you would like to use SeqTrace's more advanced features, such as automatic end quality trimming, you will want to organize your work in a SeqTrace project.  Projects allow you to save your work to a SeqTrace project file and batch process many trace files in one operation.

Using a SeqTrace project typically involves the following steps.
  1. Create a new project.
  1. Add your trace files to the project.
  1. Identify matching forward and reverse trace files.
  1. Adjust parameters for generating finished sequences.
  1. Process all trace files in the project.
  1. Export the resulting finished sequences.

This is too much to cover in this brief quick start guide, so please see the [complete project documentation](WorkingWithProjects.md) for more information.