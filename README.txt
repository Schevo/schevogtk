================================
 SchevoGtk - Tabula Rasa Branch
================================

Tabula rasa is a latin term meaning "blank slate."  The name was
chosen as a cute way of expressing the fact that this branch is
starting from a scratch to produce support for PyGTK based on lessons
learned from work with PyQt, other toolkits, and an earlier attempt at
creating a PyGTK-based Navigator.  Sometimes its good to start over
with an empty piece of paper and a fresh cup of coffee.  That is what
we have done here.  Tabula Rasa!  :-)

The Tabula Rasa branch can be checked out of the Subversion repository
at the following location:

svn://svn.orbtech.com/schevo/SchevoGtk/branches/tabula_rasa

The Tabula Rasa branch of SchevoGtk will provide support for the PyGTK
GUI toolkit through custom widgets and a Navigator application that
will allow you to view and interact with any Schevo database.  To
accomplish this, we will make use of Glade files so that both the
Navigator and custom applications can be created in any designer that
works with Glade files, such as the Gazpacho GUI Designer.  We will
also make use of the Kiwi library and framework, since Kiwi provides
widgets that go beyond those provided by PyGTK, and because the Kiwi
widgets are designed for database applications.

General information on Gazpacho and Kiwi can be found at the following
websites:

Gazpacho Website
http://gazpacho.sicem.biz/

Kiwi Website
http://async.com.br/projects/kiwi/


Installation on Windows
=======================

This Tabula Rasa branch is under development.  If you would like to
participate in that development, you will need to install several
software packages.  A detailed list for Windows users appears below.

Start by installing these three packages:

1) GTK+ 2.8.14
   http://gladewin32.sourceforge.net/

   Either of the two GTK+ installers (development or runtime) should
   work equally well, but I've only installed the development version.

2) PyCairo 1.0.2-1
   http://www.pcpm.ucl.ac.be/~gustin/win32_ports/pygtk.html

3) PyGTK 2.8.6-1
   http://www.pcpm.ucl.ac.be/~gustin/win32_ports/pygtk.html


The Gazpacho and Kiwi projects are also under heavy development and
Schevo's Pat O'Brien is participating in those projects to ensure that
they work well for Schevo.  That means that during the development of
the Tabula Rasa branch you will need to check out the Subversion
repositories for Gazpacho and Kiwi, and be prepared to update them on
a regular basis.  Do not install the packaged releases of these
applications as they are not current enough for our purposes.

Installation information about Gazpacho and Kiwi appears next.  Note
that you should NOT install either of these.  While they do include
setup.py files, you should not run them.  Instead, you should simply
check them out of Subversion, add them to your PYTHONPATH, and
configure a few environment variables, following the instructions
below.

Check out the two projects from the following locations:

1) Gazpacho Subversion Repository
   http://svn.sicem.biz/gazpacho/trunk

2) Kiwi Subversion Repository
   svn://svn.async.com.br/kiwi/trunk

Once you've checked those out, you will need to add them to your
PYTHONPATH.  You can accomplished that by creating a gazpacho.pth and
kiwi.pth file in your C:\Python24\Lib\site-packages directory, similar
to the following examples:

gazpacho.pth
------------
C:\Code\Gazpacho-svn

kiwi.pth
--------
C:\Code\Kiwi-svn

These .pth files are simple text files containing a single line with
the full path to your subversion checkouts.  You can create similar
files, or modify your PYTHONPATH environment variable.

You will also need to check out this Tabula Rasa branch.  The code can
be checked out of the Subversion repository at the following location:

svn://svn.orbtech.com/schevo/SchevoGtk/branches/tabula_rasa

After you check it out you will need to run its setup script with the
develop option:

C:\path\to\tabula_rasa> python setup.py develop

If you haven't checked out Schevo itself, that can be found here, and
has a setup script that must be run with the develop option as well:

svn://svn.orbtech.com/schevo/Schevo/trunk

The setup program will add the Tabula Rasa branch to your PYTHONPATH
(via the easy-install.pth file in Python24\Lib\site-packages) and will
add a "gnav" subcommand to the schevo commandline tool.  You should
then be able to run commands such as:

C:\> schevo gnav

C:\> schevo gnav --help

C:\> schevo gnav somedatabase.db

In order to use Kiwi and Schevo widgets within the Gazpacho designer
you will need to create a Windows environment variable whose value is
the set of paths to the Kiwi and Schevo plugins for Gazpacho.  The
environment variable must be named GAZPACHO_PATH, and should look
similar to the following example value:

C:\Code\Kiwi-svn\gazpacho-plugin;C:\Code\SchevoGtk\branches\tabula_rasa\schevo\gtk\gazpacho-plugin

To run the Gazpacho designer from your Subversion checkout requires
you to be in the topmost gazpacho directory (due to the way Gazpacho
finds resources and other files).  For example, if you checked out
Gazpacho to a directory named C:\Code\Gazpacho-svn\, then the
following commandline example should launch the designer application:

C:\Code\Gazpacho-svn> python C:\Code\Gazpacho-svn\bin\gazpacho

You could also create a Windows shortcut with properties such as:

Target: C:\Python24\pythonw.exe C:\Code\Gazpacho-svn\bin\gazpacho
Start in: C:\Code\Gazpacho-svn\

If everything is installed and configured properly you should be able
to run the Gazpacho designer and see buttons for "Kiwi Widgets" and
"Schevo Widgets".  Clicking on one of those should reveal a pallet of
custom widgets.  You should also be able to open the navigator.glade
file to see the design of the Navigator.  This file is located in the
tabula_rasa\schevo\gtk\glade directory.

Feel free to send any questions or suggestions to pobrien@orbtech.com.
