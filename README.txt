# Default: log to standard output.
processor.logfile = "~/.maildirproc.log"

processor.maildir_base = "~/maildirs"
processor.maildirs = ["incoming"]

for mail in processor:
    if mail["X-Spam-Status"].matches("^Yes"):
        mail.delete()
    elif mail.target.contains("foo@example.com"):
        mail.forward_copy("gazonk@example.com")
        mail.move("~/MaildirFoo")
    elif mail["from"].matches("fie|fum"):
        mail.copy("~/MaildirBar")
        mail.forward("bar@example.com")
