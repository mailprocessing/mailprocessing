NAME
----

imapproc - filter emails in remote IMAP folders

SYNOPSIS
--------

::

  imapproc -H <host> -u <user> --password <password>    [options]
  imapproc -H <host> -u <user> --password-command <cmd> [options]

DESCRIPTION
-----------

include(reference/description_imapproc.rst)

OPTIONS
-------

Common options
~~~~~~~~~~~~~~

include(reference/options_common.rst)

imapproc specific options
~~~~~~~~~~~~~~~~~~~~~~~~~

include(reference/options_imapproc.rst)

EXAMPLES
--------

For some examples, see the `examples <examples/>`__ directory.

SIGNALS
-------

Both SIGINT and SIGTERM will cause imapproc to shut down cleanly, i.e. it will
close the IMAP connection and write the current in-memory cache to disk upon
receiving either of these signals.

SIGHUP will cause imapproc to close and re-open its log file. This can be used
for online log rotation in continuous mode.

SEE ALSO
--------

maildirproc(1), mailprocessing(5)
