imapproc continuously monitors one or more remote IMAP folders and processes
mail in them according to user defined Python code in an *rc file*, a user
defined piece of Python code. It also logs its actions to a log file. When
there is no more mail to process, imaproc sleeps one second and then checks
again. And so on. To make imapproc exit after the first filtering run, pass the
--once option.

imapproc keeps a list of folders in the IMAP account to process. At least least
one IMAP folder must be specified for imapproc to run. Folder paths are always
absolute. There are two ways to specify this information: by passing command
line options, or by setting attributes on the processor object in the rc file.
The rc file has priority over the command line options.

The typical folder to run imapproc on is ``INBOX`` but you can of course
specify multiple folders to process.

The default location of the rc file for imapproc is
``~/.mailprocessing/imap.rc`` and the default location of its log file is
``~/.mailprocessing/log-imap``.

imapproc can optionally reload the rc file whenever a modification is detected
(that is, the file's mtime has changed). This automatic reloading is turned off
by default and can be enabled either by passing the ``--auto-reload-rcfile``
command line option or by setting the ``auto_reload_rcfile`` property to
``True`` on the processor object in the rc file.

imapproc writes its process ID to ``~/.mailprocessing/imapproc.pid`` and uses
that PID file for locking as well. If you want to run multiple imapproc
instances in parallel, use the ``--pidfile`` and ``--logfile`` options to give
each process a different PID and log file.
