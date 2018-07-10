-C, --cache-headers
    Whether to cache the email headers retrieved from the IMAP server.
    By default caching is disabled.
--cache-file FILE
    Store the email header cache in FILE if caching is enabled. If this
    is not specified explicitly, ~/.maildirproc/\ *HOST*.cache will be
    used, where *HOST* is the IMAP server's host name passed set with
    the --host option.
-c CERT, --certfile
    Use SSL certificate file CERT to verify IMAP server's SSL
    certificate (only relevant for IMAPS)
-H HOST, --host
    Connect to IMAP server HOST. This option is mandatory
-i INTERVAL, --interval
    Scan IMAP folders for new email every INTERVAL seconds; defaults to
    300; will be ignored if --once is specified as well
--folder-prefix PREFIX
    Prefix folder names with the string PREFIX. This is relevant for
    some IMAP servers that store all folders as subfolders of INBOX.
    imapproc will attempt to detect this situation, but this detection
    may not work with all server side IMAP implementations. If this is
    the case for your IMAP server, use this option to specify a prefix
    explicitly.
--folder-separator SEP
    Use SEP as a separator for folder hierarchies. By default, imapproc
    will determine the folder separator from the server's LIST response.
    This should work fine for most IMAP servers.
-p PW, --interval
    Use password PW to authenticate against IMAP server; since this will
    show up in the process list, this is mainly intended for debugging.
    Use --password-command otherwise. Either this option or
    --password-command is mandatory.
--password-command CMD
    Run command CMD and send use its output as the password to
    authenticate against the IMAP server with. This is the recommended
    approach for specifying the IMAP password. Either this option or
    --password is mandatory.
-P PORT --port
    IMAP port to use. Defaults to 143 if --use-ssl is not specified and
    993 if it is.
-s --use-ssl
    Use SSL to connect to the IMAP server (default: no).
-U USER --user
    Log in to the IMAP server with user name USER. This option is mandatory.
--insecure
    Do no certificate validation when connecting to an SSL IMAP server
    (default: no). This means the certificate subject names will be
    ignored, as will any certificate authorities. Your connection will
    not be protected from active attackers.
