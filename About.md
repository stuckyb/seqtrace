# About SeqTrace #

## What SeqTrace does (and what it does not do) ##

SeqTrace is designed to provide a user-friendly, graphical environment for efficiently processing Sanger DNA sequencing chromatogram files, or "trace files".  The first major data analysis step in many sequencing projects is deriving usable, "finished" sequences from the raw sequencing files.  It is this first step that SeqTrace is intended for.  The finished sequences can then be used by other software for further downstream analyses.

SeqTrace is entirely focused on processing sequencing files.  Thus, it does not do analyses such as multiple alignment or phylogenetic inference.  There is already plenty of good software for those tasks!

SeqTrace is best suited for sequencing projects that are primarily aimed at generating high quality sequences of one or more gene fragments (that is, single PCR products).  This sort of sequencing is common, for example, in phylogenetic studies or DNA barcoding efforts.  SeqTrace does not do sequence assembly, so projects that require building contigs and assembling overlapping reads will probably want to use other software.  Such projects have largely moved to "next generation" sequencing technologies, anyway.

## Where SeqTrace came from ##

SeqTrace is developed by Brian J. Stucky, currently a graduate student in the [Guralnick Lab](http://sites.google.com/site/robgur/) of the [Department of Ecology and Evolutionary Biology](http://ebio.colorado.edu/) at the [University of Colorado, Boulder](http://www.colorado.edu/).  I first started developing SeqTrace because it was something I needed for my own research.  I couldn't find any free software tools that quite matched what I was looking for, and I was unwilling to pay for proprietary solutions, so I began working on what eventually became SeqTrace.  After I finished implementing the basic functionality that I needed, I decided to continue developing the software with the hope that someone else might also find it useful.

If you have used SeqTrace for your research, have suggestions for improvement, or think you have found a bug, I would be happy to hear from you.  You can reach me at stuckyb AT colorado DOT edu.  SeqTrace is developed in my spare time, which is something I don't usually have much of, so I can't make any promises about when new versions of the software will be released, but I will try to fix any bugs as quickly as I can.

## Citing SeqTrace ##

If you happen to use SeqTrace for published research and would like to mention it in your methods, please use the following citation.

Stucky, B.J. 2012. [SeqTrace: A Graphical Tool for Rapidly Processing DNA Sequencing Chromatograms](http://www.ncbi.nlm.nih.gov/pmc/articles/PMC3413935/). _Journal of Biomolecular Techniques_ 23: 90-93.

Thank you!

## Similar software ##

There are a variety of open source and proprietary software packages that provide at least some of the functionality of SeqTrace.  This list only includes software that is available for free on the Web and, as a minimum level of functionality, allows the user to view trace files and export the called bases.  Although some of these programs have features not yet available in SeqTrace, none of them exactly duplicate SeqTrace's features and capabilities, as far as I know.

I do not claim that this list is comprehensive.  Also, note that even though all of these programs are free of charge, the majority of them are proprietary and _not_ free and open-source software (FOSS).  The open-source options are listed first.

  * trev, part of the [Staden package](http://staden.sourceforge.net/) (FOSS, multi-platform)
  * [Unipro UGENE](http://ugene.unipro.ru/) (FOSS, multi-platform)
  * [Chromaseq](http://mesquiteproject.org/packages/chromaseq/) (FOSS, but requires additional proprietary software, multi-platform)
  * [4Peaks](http://www.mekentosj.com/science/4peaks) (proprietary, OSX only)
  * [Chromas Lite](http://www.technelysium.com.au/chromas_lite.html) (proprietary, Windows only)
  * [Chromatogram Explorer Lite](http://www.dnabaser.com/download/chromatogram-explorer/index.html) (proprietary, Windows only)
  * [FinchTV](http://www.geospiza.com/Products/finchtv.shtml) (proprietary, multi-platform)
  * [Ridom TraceEdit](http://www.ridom.de/traceedit/) (proprietary, multi-platform)

It is worth noting that trev is the descendant of the first-ever non-commercial sequencing trace viewer, ted, developed as part of the [Staden package](http://staden.sourceforge.net/) and first announced in 1991.