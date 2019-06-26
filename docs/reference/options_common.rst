maildirproc and imapproc both take the following common command line
options:

--version
    show program's version number and exit
-h, --help
    show this help message and exit
--auto-reload-rcfile
    turn on automatic reloading of the rc file when it has been modified
--dry-run
    just log what should have been done; implies --once
-l FILE, --logfile=FILE
    send log to FILE instead of the default (~/.maildirproc/log-imap for
    imapproc and ~/.maildirproc/log-maildir for maildirproc). If you are
    running multiple maildirproc or imapproc instances, you must specify a
    dedicated log file for each of these.
--log-level=INTEGER
    only include log messages with this log level or lower; defaults to
    1
--once
    only process the maildirs once and then exit; without this flag,
    maildirproc will scan the maildirs continuously
-r FILE, --rcfile=FILE
    use the given rc file instead of the default
    (~/.maildirproc/default.rc)
--test
    test mode; implies --dry-run, --once, --logfile=- and --verbose
-v, --verbose
    increase log level one step
