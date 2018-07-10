The following options are specific to maildirproc:

-m DIRECTORY, --maildir=DIRECTORY
    add DIRECTORY to the set of maildir directories to process (can be
    passed multiple times); if DIRECTORY is relative, it will be
    considered relative to the maildir base directory
-b DIRECTORY, --maildir-base=DIRECTORY
    set maildir base directory; defaults to the current working
    directory
-p PREFIX, --folder-prefix
    prefix Maildir names with PREFIX; defaults to '.'
-s SEP, --folder-separator=SEP
    use sep as a folder separator in maildir names; defaults to '.'.
    List style folder names passed to create\_folder() will be joined by
    this character, e.g. ["github", "jrosdahl", "maildirproc"] will
    become ".github.jrosdahl.maildirproc.
