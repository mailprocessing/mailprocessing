maildirproc continuously monitors one or more `maildirs
<http://en.wikipedia.org/wiki/Maildir>`__ and processes mail in them according
to logic in an *rc file*, a user defined piece of Python code. It also logs its
actions to a log file.  By default maildirproc operates continuously: when
there is no more mail to process, maildirproc sleeps one second and then checks
again. And so on. To make maildirproc exit after the first filtering run, pass
the --once option.

maildirproc keeps a list of maildir directories to process. At least one
maildir directory must be specified for maildirproc to run. A maildir
directory path can be absolute (starting with a slash) or non-absolute.
In the latter case, it will be considered relative to the *maildir base
directory*, which defaults to the current working directory. There are
two ways to specify this information: by passing command line options,
or by setting attributes on the processor object in the rc file. The rc
file has priority over the command line options.

In a `Maildir++ <http://en.wikipedia.org/wiki/Maildir#Maildir.2B.2B>`__-style
setup, the maildir base directory should typically be set to ~/Maildir
and the maildir list should include the directory . to make maildirproc process
the inbox.

The default location of the rc file for maildirproc is
``~/.mailprocessing/maildir.rc`` and the default location of its log file is
``~/.mailprocessing/log-maildir``.

imapproc can optionally reload the rc file whenever a modification is detected
(that is, the file's mtime has changed). This automatic reloading is turned off
by default and can be enabled either by passing the ``--auto-reload-rcfile``
command line option or by setting the ``auto_reload_rcfile`` property to
``True`` on the processor object in the rc file.
