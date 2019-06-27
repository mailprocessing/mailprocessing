NAME
----

maildirproc - filter emails in local Maildirs

SYNOPSIS
--------

::

  maildirproc -m <maildir> [-m <maildir> ... ] [options]

DESCRIPTION
-----------

include(reference/description_maildirproc.rst)

OPTIONS
-------

Common options
~~~~~~~~~~~~~~

include(reference/options_common.rst)

maildirproc specific options
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

include(reference/options_maildirproc.rst)

EXAMPLES
--------

For some mailprocessing configuration examples, see the
`examples <examples/>`__ directory. You will also find sample
logrotate configuration files for mailprocessing in there.

SIGNALS
-------

SIGHUP will cause imapproc to close and re-open its log file. This can be used
for online log rotation in continuous mode.

SEE ALSO
--------

imapproc(1), mailprocessing(5)
