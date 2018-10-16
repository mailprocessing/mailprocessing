.. raw:: html

   <div id="content">

.. rubric:: mailprocessing
   :name: mailprocessing

The following programs are part of the mailprocessing package:
maildirproc is a program that processes one or several existing mail
boxes in the `maildir <http://en.wikipedia.org/wiki/Maildir>`__ format.
It is primarily focused on mail sorting — i.e., moving, copying,
forwarding and deleting mail according to a set of rules. It can be seen
as an alternative to `procmail <http://www.procmail.org>`__, but instead
of being a delivery agent (which wants to be part of the delivery
chain), maildirproc only processes already delivered mail. And that's a
feature, not a bug.

imapproc is a program that processes one or more folders on an
`IMAP <https://en.wikipedia.org/wiki/Internet_Message_Access_Protocol>`__
server. Much like maildirproc it sorts, e.g. moves, copies and forwards
email. It uses the same filter configuration mechanism as maildirproc: a
Python script that hooks into maildirprocs processing code.

maildirproc was written by Joel Rosdahl <joel@rosdahl.net> and is distributed
under the terms of the `GNU General Public Licence.
<http://www.gnu.org/licenses/gpl.html>`__

imapproc was written by `Johannes
Grassler <http://btw23.de/johannes/>`__ <johannes@btw23.de> and is
distributed under the terms of the `GNU General Public
Licence <http://www.gnu.org/licenses/gpl.html>`__, just like
maildirproc.

.. rubric:: Benefits
   :name: benefits

So, what's good about using maildirproc instead of a more conventional
setup, with a delivery agent like procmail? For me (the author) it's
this:

-  It's small. maildirproc and imapproc are just small
   `Python <http://www.python.org>`__ programs that are easy to
   understand.
-  It's robust. If there's a syntax error in the configuration, or a bug
   that makes the program crash, then nothing happens; the mail will not
   disappear. And as a consequence of using maildirs, no locks are
   needed.
-  The configuration language is relatively easy to understand and use,
   yet very powerful. The rules are expressed in a full-blown computer
   language (`Python <http://www.python.org>`__).
-  It's easy to test new configuration. Since maildirproc is not part of
   the delivery chain, it's just a matter of taking down or disabling
   the process, modifying the configuration and running maildirproc in
   test mode. When the new configuration is ready, just start or enable
   the process again.

.. rubric:: Download
   :name: download

-  `For Python 3.x <https://pypi.python.org/pypi/mailprocessing>`__

.. rubric:: Source code repository
   :name: source-code-repository

-  https://github.com/mailprocessing/mailprocessing (public
   `Git <http://git-scm.com>`__ repository)

.. rubric:: Background
   :name: background

For a long time, I used `procmail <http://www.procmail.org>`__ to sort
my mail, but I was not entirely happy with its configuration language. I
subscribe to a lot of mailing lists and I use several e-mail addresses,
so the .procmailrc file was quite large and complex and I found it hard
to express mail sorting rules elegantly. I wanted to be able to define
and use functions, data structures, if statements, loops and other
imperative language constructs and felt that procmail's rule-based
vocabulary was limiting. I thought about writing a program to generate
the configuration from some higher-level rules, but I never got to it. I
also didn't feel comfortable with e-mail sorting being part of the
delivery chain. (Granted, procmail can be used in other setups too.)

Then one day I stumbled upon a program called
`Maildird <http://www.lysator.liu.se/~jc/maildird.html>`__, written by
Jörgen Cederlöf, and I liked its basic design:

.. raw:: html

   <div class="quote">

"Maildird calmly waits until the mail is delivered, notices that a new
mail has arrived in the Maildir it monitors, writes something useful in
the log [...] and moves the mail safely to the correct Maildir."

.. raw:: html

   </div>

Since Maildird was not configurable (at least not at the time) in the
way I wanted, I decided to write my own program that worked somewhat
similarly but with a configuration style that suited me. If you like it,
you are welcome to use (or improve) it too.

.. rubric:: Documentation
   :name: documentation

See the `mailprocessing reference <reference.html>`__.

.. rubric:: Examples
   :name: examples

See the `examples <examples/>`__ directory.

.. rubric:: Installation
   :name: installation

mailprocessing has no other dependencies than a working
`Python <http://www.python.org>`__ on a Unixish system. No special
installation is needed: a simple pip install mailprocessing is
sufficient . You can also run run python setup.py install.

You can run maildirproc or imapproc in several diffent ways, e.g.:

-  Manually: You could, for example, run

   .. raw:: html

      <div class="code-example">

   maildirproc --once -r foo.rc -b . -m Maildir

   .. raw:: html

      </div>

   to apply the program in foo.rc once on a maildir directory called
   Maildir in the current directory.
-  By cron: Put a row like

   .. raw:: html

      <div class="code-example">

   \* \* \* \* \* maildirproc --once

   .. raw:: html

      </div>

   in your crontab to run maildirproc each minute (using the default RC
   file ~/.maildirproc/default.rc).
-  As a long-running process: Just start maildirproc (without the --once
   flag).
-  Using some service supervision framework, for example
   `runit <http://smarden.org/runit/>`__.

.. raw:: html

   </div>
