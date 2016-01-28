# SeqTrace release history #

## SeqTrace 0.9.0 ##
**January 14, 2014**

0.9.0 is a major new release that includes many important improvements and new features as well as a few relatively minor bug fixes.  I'd like to thank all of the users who took the time to give me feedback on SeqTrace 0.8; your ideas and comments were very helpful in deciding what to focus on for the next version.

Major new features in SeqTrace 0.9.0 include the following.

  * A new algorithm for computing consensus sequences that is based on Bayesian statistical methods.  This algorithm produces robust consensus sequences by making full use of the probability information contained in the base call quality scores.  It can perform well even when the base call qualities are less than ideal.  To learn more, check out the [new documentation](ConsensusConstruction.md).
  * The new consensus algorithm also includes the ability to detect spurious gaps in the forward/reverse trace alignment and remove these positions from the final consensus sequence.  The details are covered in the [documentation](ConsensusConstruction.md).
  * Full support for all [IUPAC nucleotide codes](http://en.wikipedia.org/wiki/Nucleic_acid_notation) in trace files and in sequences.  This includes proper handling of ambiguous nucleotide codes by the alignment and consensus algorithms.
  * You can now specify the PCR primers that were used to amplify the sequenced DNA, and SeqTrace will attempt to align the primers to the sequences and display them in the trace window.  This can be very helpful for making a quick visual assessment of your sequencing data.
  * A new sequence trimming algorithm that allows you to explicitly and automatically trim primer sequences (and any trace data beyond them) from the final consensus sequence.
  * When viewing forward and reverse trace files together in the trace view window, scrolling between them is now synchronized by default, so that the two trace views automatically scroll simultaneously.  You can easily lock their scrolling together at any position in the alignment.  This makes navigating aligned forward and reverse trace files much easier.

There are also a few more minor improvements.

  * All trace drawings are now fully anti-aliased, which makes them much more visually appealing.
  * In the trace view window, if you select one or more bases in the consensus sequence, you can now copy the selected sequence to the system clipboard.
  * When sequences are exported from single trace files, reverse traces are exported as their reverse complements.
  * The project settings dialog has been reorganized into a tabbed interface.

Finally, there are also some bug fixes.

  * Entering invalid characters when editing a sequence in the trace view window no longer causes an error that leaves the viewer in an inconsistent state.
  * When reverse trace sequences are viewed in the trace view window, they are now displayed reverse complemented, as would be expected.
  * In the trace view window, the settings change notification in the status bar now always clears after a consensus sequence is recalculated.
  * In the main window, if a forward/reverse group and one or more of its child sequences are selected simultaneously, removing the forward/reverse group no longer causes a program crash.

## SeqTrace 0.8.1 ##
**May 14, 2012**

This is primarily a bug fix release.  This release includes the following bug fixes or enhancements.

  * The consensus and alignment modules can now handle "N"s in sequences.
  * Windows: The project settings dialog deals gracefully with project files and trace files on separate drives when "use relative path" is checked.
  * ABIF files (e.g., `*`.ab1) with "user-edited" sequence characters will now read properly.
  * Trace files with "N"s in the base calls will now read properly.
  * Building a consensus sequence no longer crashes if no quality scores exceed the minimum quality threshold.

## SeqTrace 0.8.0 ##
**February 22, 2012**

**initial release**