# Advanced installation topics #

The basic [installation guide](Installation.md) is all that most users will need to quickly get SeqTrace up and running.  This document covers more advanced installation instructions for users who want the performance boost of SeqTrace's C pairwise alignment code or who want to run SeqTrace's unit tests.

## Using the C sequence alignment module ##
SeqTrace includes an implementation of its pairwise alignment algorithm in C, written using [Cython](http://cython.org/).  The C alignment code can be compiled into an external Python module which SeqTrace will then use automatically.  Use of this module dramatically increases the speed at which SeqTrace computes pairwise alignments.  In tests, the compiled module calculated alignments just over 9 times faster than the pure Python implementation.  Nevertheless, SeqTrace still works quite well without the compiled module.  The performance of the Python alignment code should be satisfactory except, perhaps, on very slow hardware.

To use the C alignment code, you will need to compile the external alignment module for your hardware.  On most GNU/Linux distributions, this is very easy.  First, make sure that you have the Python developer header files and library installed.  The following command will take care of this on [Debian](http://www.debian.org/) and Debian-derived distributions (Ubuntu, XUbuntu, etc.).
```
sudo apt-get install python2.7-dev
```

Then, make sure your working directory is the location of the C alignment code (seqtrace/core/align) and run the following command to compile the external module.
```
python setup.py build_ext --inplace
```

Assuming the module compiles successfully, the next time you run SeqTrace, the program will automatically detect that the compiled alignment module is available and use it instead of the Python alignment code.

I have not tried compiling or using the C alignment code on Windows or OSX, but it should work.  If you have success with this and would like to share how you got it working, I would be happy to hear from you.


## Running SeqTrace's unit tests ##

If you would like to run SeqTrace's unit tests, you will need to make sure that the SeqTrace package is in Python's search path.  A simple way to do this is to create a text file called "seqtrace.pth" with a single line containing the path to the seqtrace package directory.  Put this text file in a location included in Python's module search path.  On XUbuntu, /usr/local/lib/python2.x/dist-packages works well, and the following commands will set this up.
```
cd  /path/to/seqtrace/directory
sudo pwd > /usr/local/lib/python2.x/dist-packages/seqtrace.pth
```

Once the search path is set up properly, executing tests/run\_tests.py will run all unit tests.