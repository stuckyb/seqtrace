# Installation instructions #

SeqTrace is easy to install on all popular operating systems.  On Linux and Windows, installing SeqTrace typically requires nothing more than downloading the appropriate package and unzipping the archive.  Installing SeqTrace on OSX requires a bit more effort, but is still straightforward.  This document contains detailed installation instructions for all three operating systems.
  * [GNU/Linux](Installation#GNU/Linux.md)
  * [Windows](Installation#Windows.md)
  * [OSX](Installation#OSX.md)

SeqTrace includes a very fast pairwise alignment module written in C, but you must compile it for your hardware in order to use it.  If you would like to read more about this, check out the [advanced installation instructions](AdvancedInstallationTopics.md).

## General requirements ##

SeqTrace requires both [Python](http://www.python.org/) and [GTK+](http://www.gtk.org/) (and the Python package [PyGTK](http://www.pygtk.org/)), and will only run properly under the 2.x series of Python, not 3.0.  There are significant differences between 2.7 and 3.0 in Python's handling of low-level file I/O, and these differences matter a great deal when reading binary sequence trace file formats.  SeqTrace is currently written for the 2.x series of Python because it is widely installed and available just about everywhere.  In the future, though, I plan to port SeqTrace to Python 3.0.


## GNU/Linux ##

Installing SeqTrace on most GNU/Linux distributions is very simple, because they generally already have all necessary software libraries installed.  Of course, SeqTrace does require a windowing environment, so it will not work in command shell-only installations.

**0. Download SeqTrace:**  On most GNU/Linux distributions (such as [Ubuntu](http://www.ubuntu.com/) or [XUbuntu](http://xubuntu.org/)), installing SeqTrace requires nothing more than downloading and unzipping the [SeqTrace archive](http://seqtrace.googlecode.com/files/seqtrace-0.9.0.tar.gz).

**1. Run SeqTrace:**  Run seqtrace.py to launch SeqTrace.


## Windows ##

I provide a binary executable version of SeqTrace for Windows that does not require installing any additional software.

**0. Download SeqTrace:**  Download the [SeqTrace package for Windows](http://seqtrace.googlecode.com/files/seqtrace-win-0.9.0.zip) and unzip the archive wherever you would like to have SeqTrace located on your system.

**1. Run SeqTrace:**  Run seqtrace.exe to launch SeqTrace.

### Running SeqTrace from the source package on Windows ###

If for some reason you would like to run SeqTrace on Windows using the [source package](http://seqtrace.googlecode.com/files/seqtrace-0.9.0.zip), it is not at all difficult.  You will simply need to install a few dependencies first.

SeqTrace requires the Python runtime environment and the GTK+ library to run properly.  On Windows, you might need to install one or both of these before installing SeqTrace.  Fortunately, both Python and GTK+ are easy to install on Windows.  There are many other Windows programs that use Python or GTK+, so it is possible that your Windows environment already includes these packages.

**0. Install Python:**  If your system does not already have Python installed, you will need to download the latest [Python 2.7.x installer](http://www.python.org/download/) and install it.  Be sure to get the 32-bit version of Python, not the one with "X86-64" in its name.  The filename for the installer you want will be "python-2.7.x.msi" or something similar.

**1. Install GTK+ and PyGTK:**  Download the latest release of the [PyGTK all-in-one installer](http://ftp.gnome.org/pub/GNOME/binaries/win32/pygtk/2.24/) for Python 2.7 and install it.  At the time of this writing, the latest installer is named pygtk-all-in-one-2.24.1.win32-py2.7.msi.

**2. Download SeqTrace:**  Download the [SeqTrace archive file](http://seqtrace.googlecode.com/files/seqtrace-0.9.0.zip) and extract the contents wherever you would like to have SeqTrace located on your system.

**3. Run SeqTrace:**  That's it!  To run SeqTrace, you can either double click seqtrace.py in Windows Explorer, or run seqtrace.py from a command prompt.

## OSX ##

SeqTrace requires a Python interpreter and the GTK+ library in order to run.  OSX includes Python, but not GTK+, so at a minimum, you will need to install the GTK+ environment before you can use SeqTrace.  There are two ways to get GTK+ running on OSX.  One option is to use the X11 windowing system, and the other is to use the native GTK+ for OSX.  Both options work well, but in my (very) informal testing, the SeqTrace interface seemed slightly more responsive running through X11.  Using native GTK+ is currently the quickest and easiest way to get SeqTrace running, however.  Instructions for both approaches are provided here.

**0. Download SeqTrace:**  Either way, you should first download the [SeqTrace archive file](http://seqtrace.googlecode.com/files/seqtrace-0.9.0.tar.gz) and extract the contents wherever you would like to have SeqTrace located on your system.

### running SeqTrace with native GTK+ ###

**1. Install the latest Python (optional):**  OSX comes with Python pre-installed, but the included version is usually somewhat outdated.  If you are running a recent version of OSX, though, the Python that it came with will probably work just fine.  However, you can easily [download the latest OSX Python installer](http://www.python.org/download/releases/) and install it, which will ensure that you are running a recent release of Python.  Be sure to download the 2.7 series of Python, not the 3.x series.

**2. Install GTK+ and PyGTK:**  Next, you will need to install the GTK+ libraries.  Thanks to a package maintained by Anders Björklund, this is now very easy.  Download the [PyGTK package for OSX](http://sourceforge.net/projects/macpkg/files/PyGTK/2.24.0/PyGTK.pkg/download) and install it on your system.

**3. Run SeqTrace:**  That's it!  To launch SeqTrace, run seqtrace.py from a terminal window.

### running SeqTrace with X11 ###

**1. Install Xcode:**  You will need to have Apple's Xcode software development kit installed.  For OSX 10.7 ("Lion") you can install it through the "App Store", for previous versions of OSX you can find it on the installation DVD or the [Apple Developer website](https://developer.apple.com/xcode/).

**2. Install MacPorts (and possibly X11):**  Next, you will need to make sure that you have the [X11 windowing system](http://www.x.org/wiki/) and [MacPorts](http://www.macports.org/) installed.  X11 provides a standard UNIX windowing environment for SeqTrace, and MacPorts provides an easy way to get the GTK+ libraries for X11 on your system.  On recent versions of OSX, X11 is installed by default, but not MacPorts, so you will need to download and install the [MacPorts installer](http://www.macports.org/install.php).

**3. Install GTK+ and PyGTK:**  Now, start a terminal window and run the following commands.
```
sudo port install py27-pygtk
sudo port select python python27
```

The first command installs GTK+ and PyGTK along with any required dependencies, including the MacPorts version of Python 2.7.  This will take a few minutes to complete.  The second command tells your computer to use the newly-installed version of Python.

**4. Run SeqTrace:**  To run SeqTrace, run the following command, replacing "/path/to/seqtrace" with the location of SeqTrace on your system.
```
python /path/to/seqtrace/seqtrace.py
```

That is all that is required to get SeqTrace running.  OSX should automatically launch X11 when you start SeqTrace.  If not, try exiting the terminal and opening a new terminal window, then run SeqTrace.

**5. Install GTK+ themes (optional):**  If you would like SeqTrace to have a "prettier" look in X11, you can also use MacPorts to install GTK2 engines and themes.  For example, one of the OSX [screenshots of SeqTrace](ScreenShots.md) features the "Clearlooks" theme.  The following commands will let you choose a different theme for GTK+.
```
sudo port install gnome-themes
sudo port install gtk-theme-switch
switch2
```

**6. Update seqtrace.py (optional):**  If you would like to run seqtrace.py directly (that is, without explicitly calling the Python interpreter), you can easily do so by editing the first line of seqtrace.py to reflect the location of the MacPorts installation of Python.  In the terminal, run the command "which python", then copy the output and use it to replace everything after "#!" in the first line of seqtrace.py.