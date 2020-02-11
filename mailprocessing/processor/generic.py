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

import fcntl
import os
import sys
import time

from mailprocessing import signals

from mailprocessing.util import safe_write


class MailProcessor(object):
    def __init__(
            self, rcfile, log_fp, **kwargs):

        defaults = {'log_level': 1,
                    'dry_run': False,
                    'run_once': False,
                    'auto_reload_rcfile': False}

        for key in defaults:
            if key not in kwargs:
                kwargs[key] = defaults[key]

        self._rcfile = rcfile
        self._log_fp = log_fp
        print("setting log level to %s" % kwargs['log_level'])
        self._log_level = kwargs['log_level']
        self._run_once = kwargs['run_once'] or kwargs['dry_run']
        self._auto_reload_rcfile = kwargs['auto_reload_rcfile']
        self._deliveries = 0
        self._sendmail = "/usr/sbin/sendmail"
        self._sendmail_flags = "-i"
        self.rcfile_modified = False
        self._previous_rcfile_mtime = self._get_previous_rcfile_mtime()

    def get_auto_reload_rcfile(self):
        return self._auto_reload_rcfile

    def set_auto_reload_rcfile(self, value):
        self._auto_reload_rcfile = value

    auto_reload_rcfile = property(
        get_auto_reload_rcfile, set_auto_reload_rcfile)

    def set_logfile(self, path_or_fp):
        if isinstance(path_or_fp, str):
            self._log_fp = open(
                os.path.expanduser(path_or_fp),
                "a",
                errors="backslashreplace")
            lock_acquired = False
            while not lock_acquired:
                try:
                    fcntl.flock(self._log_fp, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    lock_acquired = True
                except OSError:
                    print("Couldn't acquire lock on log file %s, sleeping "
                          "for 5s" % self._log_fp.name, file=sys.stderr)
                    time.sleep(5)
        else:
            self._log_fp = path_or_fp

    logfile = property(fset=set_logfile)

    def reopen_logfile(self):
        # log file is a stream, so no need to reopen
        if self._log_fp.fileno() < 3:
            return
        filename = self._log_fp.name
        self._log_fp.close()
        self.set_logfile(filename)

    @property
    def rcfile(self):
        return self._rcfile

    def get_sendmail(self):
        return self._sendmail

    def set_sendmail(self, sendmail):
        self._sendmail = sendmail

    sendmail = property(get_sendmail, set_sendmail)

    def get_sendmail_flags(self):
        return self._sendmail_flags

    def set_sendmail_flags(self, sendmail_flags):
        self._sendmail_flags = sendmail_flags

    sendmail_flags = property(get_sendmail_flags, set_sendmail_flags)

    def __iter__(self):
        """
        Iterator method used to invoke the processor from default.rc.

        The user must be able to treat your processor class as an iterable
        object that provides every message as a mailprocessing.mail.base.MailBase
        subclass.
        """

        message = ("You need to implement an __iter__ method in your "
                   "MailProcessor subclass.")
        raise NotImplementedError(message)

    def create_folder(self, folder, **kwargs):
        """
        Creates a new folder.

        This method is used to create a folder to store emails in. Depending on
        the `parents` parameter it also creates the folders parent folders if
        they do not exist. This should be the default behaviour.

        folder may either be a path name separated by the appropriate path
        component separator or a list of path name components. In the latter
        case it is the create_folder() implementation's responsibility to join
        the path components.
        """

        message = ("You need to implement a create_folder() method in your "
                   "MailProcessor subclass.")
        raise NotImplementedError(message)

    def log(self, text, level=1):
        if level <= self._log_level:
            safe_write(self._log_fp, text)
            self._log_fp.flush()

    def log_debug(self, text):
        if signals.hup_received():
            self.reopen_logfile()
        self.log(text, 2)

    def log_error(self, text):
        if signals.hup_received():
            self.reopen_logfile()
        try:
            self.log(text, 0)
        except:
            # Make sure the message gets out even if writing to the log file
            # fails.
            safe_write(sys.stderr, text)

    def log_info(self, text):
        if signals.hup_received():
            self.reopen_logfile()
        self.log(text, 1)

    def fatal_error(self, text):
        if signals.hup_received():
            self.reopen_logfile()
        try:
            self.log_error(text)
        except:
            # Make sure the message gets out even if writing to the log file
            # fails.
            pass
        safe_write(sys.stderr, text)
        sys.exit(1)

    def path_ensure_prefix(self, path, sep='.'):
        """
        Converts path to list form and returns path prepended with the
        processor's path prefix. If its leading component is already the prefix
        or there is no prefix set, the original path in list form is returned.
        """

        path = self.path_list(path)
        if len(path) == 0:
            return path

        if sep == '/':
            return path
        # Special case (mostly relevant for maildirs):
        # Return an empty first component if path and
        # prefix are identical.
        if self.prefix == self.separator:
            if path[0] == '':
                return path
            else:
                ret = ['']
                ret.extend(path)
                return ret

        if self.prefix != '':
            if path[0] == self.prefix:
                return path
            ret = [self.prefix]
            ret.extend(path)
            return ret
        return path

    def path_list(self, path, sep='/'):
        """
        Leaves a list of path components unchanged or converts a path name in
        string form to a list of path components.
        """

        if type(path) is list:
            return path

        return path.split(sep)

    def list_path(self, path, sep='/'):
        """
        Leaves a path name in string form unchanged and converts a list of path
        components into a path in string form.
        """

        if type(path) is list:
            return sep.join(path)
        return path

    # ----------------------------------------------------------------
    # Private methods:

    def _get_previous_rcfile_mtime(self):
        if self.rcfile == "-":
            return None
        else:
            try:
                return os.path.getmtime(self.rcfile)
            except OSError:
                # File does not exist.
                return None
