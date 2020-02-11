# -*- coding: utf-8; mode: python -*-

# Copyright (C) 2017 Johannes Grassler <johannes@btw23.de>
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

"""imapproc -- IMAP folder processor

imapproc filters email in an IMAP folder according to a set of sorting rules
defined by a snippet of Python code. It provides hooks that let your program
access the emails' headers along with functions for moving, copying  and
forwarding.
"""

import locale
import os
import subprocess
import sys
from optparse import OptionParser

from mailprocessing.processor.imap import ImapProcessor

from mailprocessing.util import iso_8601_now
from mailprocessing.util import write_pidfile
from mailprocessing.version import PKG_VERSION


def main():
    imapproc_directory = "~/.mailprocessing"
    default_rcfile_location = os.path.join(imapproc_directory, "imap.rc")
    default_logfile_location = os.path.join(imapproc_directory, "log-imap")
    default_pidfile_location = os.path.join(imapproc_directory, "imapproc.pid")

    if not os.path.isdir(os.path.expanduser(imapproc_directory)):
        os.mkdir(os.path.expanduser(imapproc_directory))

    parser = OptionParser(
        version=PKG_VERSION,
        description=(
            "imapproc is a program that scans one or more folders in an"
            " IMAP mailbox and processes found mail as defined by an rc file."
            " See http://mailprocessing.github.io/mailprocessing for more information."))
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
        "-f",
        "--folder",
        action="append",
        type="string",
        default=[],
        dest="folders",
        metavar="FOLDER",
        help=(
            "add FOLDER to the set of IMAP folders to process (can"
            " be passed multiple times). Using `.` as a folder should"
            " work for most IMAP servers."))
    parser.add_option(
        "--once",
        action="store_true",
        default=False,
        help=(
            "only process the maildirs once and then exit; without this flag,"
            " mailprocessing will scan the folders in regular intervals (set these"
            " with the --interval option)"))
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

    # IMAP specific options
    parser.add_option(
        "--cache-file",
        type="string",
        help=("File to store header cache in. By default "
              "~/.mailprocessing/<HOST>.cache will be used, "
              "where <HOST> is the IMAP server's host name."))
    parser.add_option(
        "-C",
        "--cache-headers",
        action="store_true",
        help="Cache mail headers retrieved from imap_server")
    parser.add_option(
        "-c",
        "--certfile",
        type="string",
        help="Certificate file to verify server's certificate against (only relevant for IMAPS)")
    parser.add_option(
        "-H",
        "--host",
        type="string",
        help="IMAP server to log in to.")
    parser.add_option(
        "-i",
        "--interval",
        type="int",
        default=300,
        metavar="INTERVAL",
        help=(
            "Scan IMAP folders every INTERVAL seconds for new mail. Will be"
            " ignored if --once is specified as well."))
    parser.add_option(
        "-p",
        "--password",
        type="string",
        help="Password to log into IMAP server with.")
    parser.add_option(
        "--password-command",
        type="string",
        metavar="COMMAND",
        help="Execute COMMAND and read the password to log in to IMAP "
             "server with from its standard output.")
    parser.add_option(
        "-P",
        "--port",
        type="int",
        help="IMAP port to use. Defaults to 143 if --use-ssl is not specified "
             "and 993 if it is.")
    parser.add_option(
        "--folder-prefix",
        type="string",
        metavar="PREFIX",
        help="Name space prefix for IMAP folder names")
    parser.add_option(
        "--folder-separator",
        type="string",
        metavar="SEP",
        help="Name space separator for IMAP folder names")
    parser.add_option(
        "--header-batchsize",
        type="int",
        default=200,
        metavar="BATCHSIZE",
        help="Batch size to use for downloading message headers")
    parser.add_option(
        "--flag-batchsize",
        type="int",
        metavar="BATCHSIZE",
        default=200,
        help="Batch size to use for downloading message flags")
    parser.add_option(
        "-u",
        "--user",
        type="string",
        help="IMAP User to log into IMAP server as.")
    parser.add_option(
        "-s",
        "--use-ssl",
        action="store_true",
        default=False,
        help="Use SSL to connect to IMAP server.")
    parser.add_option(
        "--insecure",
        action="store_true",
        default=False,
        help="Skip SSL certificate validation when connecting to IMAP server (unsafe).")
    parser.add_option(
        "--pidfile",
        type="string",
        default=default_pidfile_location,
        metavar="FILE",
        help="File to write imapproc process ID to")

    (options, _) = parser.parse_args(sys.argv[1:])

    bad_options = False

    for opt in ("host", "user"):
        if not options.__dict__[opt]:
            print("Please specify --%s option." % opt, file=sys.stderr)
            bad_options = True

    if not (options.password or options.password_command):
        print("Please specify either --password or --password-command.", file=sys.stderr)
        bad_options = True

    if options.password and options.password_command:
        print("Please specify only one of --password or --password-command.", file=sys.stderr)
        bad_options = True

    if options.insecure and options.certfile:
        print("Please specify only one of --insecure or --certfile.", file=sys.stderr)
        bad_options = True

    if bad_options:
        sys.exit(1)

    processor_kwargs = {}

    if options.password:
        processor_kwargs['password'] = options.password

    if options.password_command:
        try:
            p = subprocess.check_output(options.password_command, shell=True)
            p = p.decode(locale.getpreferredencoding()).rstrip("\n")
        except subprocess.CalledProcessError as e:
            print("Password command failed with exit status %d, "
                  "output follows." % e.returncode, file=sys.stderr)
            sys.stderr.buffer.write(e.output)
            sys.exit(1)
        except Exception as e:
            print("Could not execute command %s: %s" % (options.password_command, e))
            sys.exit(1)
        processor_kwargs['password'] = p

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

    pidfile = os.path.expanduser(options.pidfile)

    if not os.path.isabs(pidfile):
        print("Error: pid file %s is not an absolute path." % pidfile,
              file=sys.stderr)
        sys.exit(1)

    try:
        pidfile_fd = open(pidfile, 'a')
    except IOError as e:
        print("Couldn't open pid file %s for writing: %s" % (pidfile, e),
              file=sys.stderr)

    write_pidfile(pidfile_fd)

    processor_kwargs["log_level"] = options.log_level + options.verbosity

    rcfile = os.path.expanduser(options.rcfile)

    processor_kwargs["run_once"] = options.once

    for opt in ("auto_reload_rcfile", "certfile", "dry_run", "folders",
                "folder_prefix", "folder_separator", "header_batchsize",
                "flag_batchsize", "host", "interval", "port", "user",
                "use_ssl", "insecure", "verbosity"):
        processor_kwargs[opt] = options.__dict__[opt]

    if options.cache_headers:
        if options.cache_file:
            cache_file = options.cache_file
        else:
            cache_file = os.path.join(imapproc_directory,
                                      options.host + '.cache')
        processor_kwargs['cache_file'] = os.path.expanduser(cache_file)

    # Try to open rc file early on. Otherwise we'll process headers until we
    # get to the point where we open the rc-file, possibly wasting a lot of
    # time if it is missing.
    try:
        open(rcfile).close()
    except IOError as e:
        print("Error: Could not open RC file: {0}".format(e), file=sys.stderr)
        sys.exit(1)

    processor = ImapProcessor(rcfile, log_fp, **processor_kwargs)
    processor.log("")
    processor.log(
        "Starting imapproc {0} at {1}".format(
            parser.version, iso_8601_now()))

    if options.folders:
        processor.folders = options.folders
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
