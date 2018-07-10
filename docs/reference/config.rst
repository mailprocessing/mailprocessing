maildirproc's and imapproc's configuration, the *rc file*, is not a set
of declarative rules. Instead, it is a simple
`Python <http://www.python.org>`__ program that has access to a "maildir
processor" object which produces mail objects. The mail processing logic
is defined in terms of if/elif/else statements and actions are performed
by calling methods on the mail objects.

Maildir and IMAP specific functionality is implemented by the
MaildirProcessor and ImapProcessor classes, respecitively.

The MailProcessor class
~~~~~~~~~~~~~~~~~~~~~~~

Iteration over a MailProcessor instance yields Mail instances. imapproc and
maildirproc will create a MailProcessor instance for you which is available as
the global **processor** variable in the rc file's name space.

Readable and writable properties
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

auto\_reload\_rcfile
    Whether the rc file should be automatically reloaded when it has
    been modified. Assignment to this property overrides the
    corresponding command-line option.
maildir\_base
    The base directory of maildirs. Assignment to this property
    overrides the corresponding command-line option. This property is
    specific to MaildirProcessor instances.
maildirs
    A list of maildirs (subdirectories of the maildir base directory).
    Assignment to this property overrides the corresponding command-line
    option. This property is specific to MaildirProcessor instances.
folders
    A list of IMAP folders. Assignment to this property overrides the
    corresponding command-line option. This property is specific to
    ImapProcessor instances.

Methods
^^^^^^^

create\_folder(\ *folder*, *parents=True*, *prefix='.'*)
    Create folder *folder* (a string, or a list of namespace
    components). This method can safely be called for existing folders.
    If the folder exists already, the method will log that it exists and
    exit without trying to create it.
    For MaildirProcessor *folder* does not need to be on the same file
    system as the mail. If the *folder* path is relative, it will be
    considered relative to the maildir base directory.
    The boolean keyword argument *parents* governs whether parent
    folders should be created as well, e.g. if you create
    'github.jrosdahl.maildirproc', 'github' and 'github.jrosdahl' will
    be created as well. This is the default behaviour.
    The *prefix* keyword argument specifies a prefix to prepend the
    folder name with. This defaults to the processors *prefix* attribute
    which is set via the --prefix command line attribute for
    MaildirProcessor instances.

Writable properties
^^^^^^^^^^^^^^^^^^^

logfile
    Location of the log file. Assignment to this property overrides the
    corresponding command-line option.

The Mail class
~~~~~~~~~~~~~~

Indexing a ``Mail`` instance with a header name (a string) returns a ``Header``
instance. Example:

::
  
  for mail in processor:
    myheader = mail['From']

Readable properties
^^^^^^^^^^^^^^^^^^^

folder
    The IMAP folder in which the mail is situated. Only applicable for
    ImapProcessor.
maildir
    The maildir in which the mail is situated. Only applicable for
    MaildirProcessor.
path
    Full filesystem path to the mail. Only applicable for
    MaildirProcessor.
target
    A Target instance.

Methods
^^^^^^^

copy(\ *maildir*, *create=False*)
    Copy the mail to *maildir* (a string). *maildir* does not need to be
    on the same file system as the mail. If the *maildir* path is
    relative, it will be considered relative to the maildir base
    directory. If the optional *create* keyword argument is set to True,
    the folder (and its parent folders) will be created if it does not
    exist. By default non-existent folders are not created.
delete()
    Delete the mail.
forward(\ *addresses[, env\_sender]*)
    Forward the mail to one or several e-mail addresses **and delete the
    mail**. *addresses* can be either a string or a list of strings.
    *env\_sender* (optional) specifies which envelope sender address to
    use.
forward\_copy(\ *addresses[, env\_sender]*)
    Forward a copy of the mail to one or several e-mail addresses.
    *addresses* can be either a string or a list of strings.
    *env\_sender* (optional) specifies which envelope sender address to
    use.
from\_mailing\_list(\ *list*)
    Check whether the mail originated from the mailing list *list* (a
    string). Currently, the headers Delivered-To, Mailing-List,
    X-BeenThere and X-Mailing-List are checked. Returns a boolean.
strict\_mailing\_list(\ *list*)
    Check whether the mail originated from the mailing list *list* (a
    string). It is a bit stricter than ``from_mailing_list()`` and only
    matches the content of typical mailing list headers, namely
    List-Archive, List-Help, List-ID, List-Post, List-Subscribe and
    X-Mailing-List.
is\_seen()
    Returns True if the message has been seen by the user, False
    otherwise.
is\_flagged()
    Returns True if the message has been flagged by the user, False
    otherwise.
move(\ *maildir*, *create=False*)
    Move the mail to *maildir* (a string). *maildir* **must** be on the
    same file system as the mail, otherwise nothing will happen and an
    error will be logged. For MaildirProcessor, a relative *maildir*
    path, will be considered relative to the maildir base directory. If
    the optional *create* keyword argument is set to True, the folder
    (and its parent folders) will be created if it does not exist. By
    default non-existent folders are not created.

The Header class
~~~~~~~~~~~~~~~~

Methods
^^^^^^^

contains(\ *case-insensitive-string*)
    Check whether *case-insensitive-string* is part of the header.
    Returns a boolean.
matches(\ *case-insensitive-regexp*)
    Check whether *case-insensitive-regexp* (with an implicit .\*
    prefix) matches the header. Returns a boolean.

The Target class
~~~~~~~~~~~~~~~~

Methods
^^^^^^^

contains(\ *case-insensitive-string*)
    Check whether *case-insensitive-string* is part of the To or Cc
    header. Returns a boolean.
matches(\ *case-insensitive-regexp*)
    Check whether *case-insensitive-regexp* (with an implicit .\*
    prefix) matches the To or Cc header. Returns a boolean.
