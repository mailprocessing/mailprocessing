# -*- coding: utf-8; mode: python -*-

# Copyright (C) 2006-2010 Joel Rosdahl <joel@rosdahl.net>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA
# 02110-1301, USA.

"""maildirproc -- maildir processor

http://mailprocessing.github.io/mailprocessing

maildirproc is a small program that processes one or several existing
mail boxes in the maildir format. It is primarily focused on mail
sorting -- i.e., moving, copying, forwarding and deleting mail
according to a set of rules. It can be seen as an alternative to
procmail, but instead of being a delivery agent (which wants to be
part of the delivery chain), maildirproc only processes already
delivered mail. And that's a feature, not a bug.
"""

import locale
import os
import sys
from optparse import OptionParser

from mailprocessing.processor.maildir import MaildirProcessor

from mailprocessing.util import iso_8601_now

from mailprocessing.version import PKG_VERSION


def main():
    maildirproc_directory = "~/.mailprocessing"
    default_rcfile_location = os.path.join(maildirproc_directory, "maildir.rc")
    default_logfile_location = os.path.join(maildirproc_directory, "log-maildir")

    if not os.path.isdir(os.path.expanduser(maildirproc_directory)):
        os.mkdir(os.path.expanduser(maildirproc_directory))

    parser = OptionParser(
        version=PKG_VERSION,
        description=(
            "maildirproc is a program that scans a number of maildir mail"
            " boxes and processes found mail as defined by an rc file. See"
            " http://mailprocessing.github.io/mailprocessing for more"
            " information."))
    parser.add_option(
        "--auto-reload-rcfile",
        action="store_true",
        default=False,
        help=(
            "turn on automatic reloading of the rc file when it has been"
            " modified"))
    parser.add_option(
        "--dry-run",
        action="store_true",
        default=False,
        help=(
            "just log what should have been done; implies --once"))
    parser.add_option(
        "-l",
        "--logfile",
        type="string",
        dest="logfile",
        metavar="FILE",
        help="send log to FILE instead of the default ({0})".format(
            default_logfile_location),
        default=default_logfile_location)
    parser.add_option(
        "--log-level",
        type="int",
        metavar="INTEGER",
        help=(
            "only include log messages with this log level or lower; defaults"
            " to 1"),
        default=1)
    parser.add_option(
        "-m",
        "--maildir",
        action="append",
        type="string",
        default=[],
        dest="maildirs",
        metavar="DIRECTORY",
        help=(
            "add DIRECTORY to the set of maildir directories to process (can"
            " be passed multiple times); if DIRECTORY is relative, it is"
            " relative to the maildir base directory"))
    parser.add_option(
        "-b",
        "--maildir-base",
        type="string",
        default=".",
        dest="maildir_base",
        metavar="DIRECTORY",
        help="set maildir base directory; defaults to the current working"
             " directory")
    parser.add_option(
        "-s",
        "--folder-separator",
        type="string",
        default=".",
        metavar="SEP",
        help="Separate maildir folder names by SEP")
    parser.add_option(
        "-p",
        "--folder-prefix",
        type="string",
        default=".",
        metavar="PREFIX",
        help="Prefix maildir directory names by PREFIX")
    parser.add_option(
        "--once",
        action="store_true",
        default=False,
        help=(
            "only process the maildirs once and then exit; without this flag,"
            " maildirproc will scan the maildirs continuously"))
    parser.add_option(
        "-r",
        "--rcfile",
        type="string",
        dest="rcfile",
        metavar="FILE",
        help=(
            "use the given rc file instead of the default ({0})".format(
                default_rcfile_location)),
        default=default_rcfile_location)
    parser.add_option(
        "--test",
        action="store_true",
        default=False,
        help=(
            "test mode; implies --dry-run, --once, --logfile=- and"
            " --verbose"))
    parser.add_option(
        "-v",
        "--verbose",
        action="count",
        default=0,
        dest="verbosity",
        help="increase log level one step")
    (options, _) = parser.parse_args(sys.argv[1:])

    if options.test:
        options.dry_run = True
        options.logfile = "-"
        options.verbosity = max(1, options.verbosity)

    if options.dry_run:
        options.once = True

    if options.logfile == "-":
        log_fp = sys.stdout
    else:
        log_fp = open(
            os.path.expanduser(options.logfile),
            "a",
            encoding=locale.getpreferredencoding(),
            errors="backslashreplace")

    log_level = options.log_level + options.verbosity

    rcfile = os.path.expanduser(options.rcfile)
    processor = MaildirProcessor(
        rcfile=rcfile, log_fp=log_fp, log_level=log_level,
        dry_run=options.dry_run, run_once=options.once,
        auto_reload_rcfile=options.auto_reload_rcfile,
        folder_prefix=options.folder_prefix,
        folder_separator=options.folder_separator)
    processor.log("")
    processor.log(
        "Starting maildirproc {0} at {1}".format(
            parser.version, iso_8601_now()))

    processor.maildir_base = options.maildir_base
    if options.maildirs:
        processor.maildirs = options.maildirs
    if "SENDMAIL" in os.environ:
        processor.sendmail = os.environ["SENDMAIL"]
    if "SENDMAILFLAGS" in os.environ:
        processor.sendmail_flags = os.environ["SENDMAILFLAGS"]
    environment = {"processor": processor}

    if rcfile == "-":
        processor.log("RC file: <standard input>")
        rc = sys.stdin.read()
        exec(rc, environment)
    else:
        processor.log("RC file: {0}".format(ascii(rcfile)))
        while True:
            try:
                rc = open(rcfile).read()
            except IOError as e:
                processor.fatal_error(
                    "Error: Could not open RC file: {0}".format(e))
            else:
                exec(rc, environment)
                if not processor.rcfile_modified:
                    # Normal exit.
                    break
                # We should reload the RC file.
