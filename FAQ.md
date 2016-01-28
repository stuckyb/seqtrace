# Frequently asked questions #

  1. [My sequencing trace files do not have base call quality scores.  Can I still use them in SeqTrace?](#My_sequencing_trace_files_do_not_have_base_call_quality_scores..md)
  1. [Why can't I adjust the y-axis scale when I'm viewing forward and reverse traces together?](#Why_can't_I_adjust_the_y-axis_scale_when_I'm_viewing_f.md)

## My sequencing trace files do not have base call quality scores.  Can I still use them in SeqTrace? ##

Not quite (but you're not just out of luck, either -- see below).  If the trace files have no quality data at all, then SeqTrace will not open them.  Some files without quality data will have all zeros for the quality scores, and in those cases, you should be able to at least open the files and view the traces.  Either way, though, you will not be able to get consensus sequences from the files.  This is because all of SeqTrace's consensus algorithms require quality information about the base calls.  In general, algorithms based on the quality scores are far superior to and much more robust than algorithms that do not use them.

For just about all new sequencing data, this should be no problem.  Following the introduction of the software program [Phred](http://www.phrap.org/phredphrapconsed.html) in the 1990s, quality scores for base calls have become absolutely ubiquitous.  All modern Sanger sequencing platforms of which I am aware produce trace files with base call quality scores.

However, if you have old sequencing data without quality scores or you are still using old base calling software that does not calculate quality information, you do have a couple of options.  First, if all you want are the raw base calls (that is, the raw sequence) from the trace file, and your trace files have all zeros for the quality scores, you should be able to export the raw sequences directly from SeqTrace.  Open the trace files(s) in the trace view window, then select "Export raw sequence(s)..." from the "File" menu.

A better option (and, if your trace files have no quality data at all, your only option) is to add quality scores to your trace data.  If you only have a few trace files, you might try the [free online service](http://www.nucleics.com/peaktrace-sequencing/) offered by [Nucleics](http://www.nucleics.com/).  You evidently upload your ABI trace files and then get back trace files with base calls and quality scores added.  I have not personally tried this and cannot vouch for how well it works, but they claim their software is accurate.

A more general solution is to use base-calling software to add the quality information to the trace files yourself.  I recommend using [TraceTuner](http://sourceforge.net/projects/tracetuner/), which has been used for some very large sequencing projects and has a proven track record of success.  This software was originally developed by a company called Paracel, which became part of Celera, and was released as an open source project in 2006.

You can process ABI files directly with TraceTuner, have it call the bases and calculate quality scores, and output the results as SCF trace files.  When you run TraceTuner, use the -cv3 option to have it output the results using version 3.0 of the SCF standard, which SeqTrace requires.  Unfortunately, when I tried this, I still got SCF 2 output files.  If that happens, you can use the program convert\_trace in the [Staden Package](http://staden.sourceforge.net/) to easily convert these files to a format that SeqTrace can use.  I recommend the ZTR format because of its efficient compression and small file size.

Here's an example of the simplest way to run TraceTuner with SCF 3.0 output.

```
ttuner -cv3 -c trace_file.ab1
```

That will generate an output file called "trace\_file.scf".  If you need to convert the results to ZTR format, use this command.

```
convert_trace -out_format ZTR < trace_file.scf > trace_file.ztr
```

You should then be able to open the files and work with them in SeqTrace as usual.

If you don't want to use TraceTuner, you can also try the program Phred.  Be sure to run Phred with the "-cv 3" option to tell it to generate its output as SCF version 3 trace files.  Phred is available at no cost for academic users, but it is unfortunately not free and open source software (FOSS).  It also looks like actually [obtaining the software](http://www.phrap.org/consed/consed.html#howToGet) is sort of a pain.

## Why can't I adjust the y-axis scale when I'm viewing forward and reverse traces together? ##
You can, but you can only adjust the y-axis scale for one trace at a time.  In the trace view window toolbar, you will notice a drop-down list box (item number 3 in the [documentation for the trace view window](TraceViewWindow.md)) with the options "Both:", "Forward:", and "Reverse:".  Make sure that either "Forward:" or "Reverse:" is selected, and you should then be able to adjust the y-axis scale for the selected trace.  This is also covered in the [documentation for the trace view window](TraceViewWindow.md).