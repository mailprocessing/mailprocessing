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

import errno
import os
import random
import socket
import time

from mailprocessing.processor.generic import MailProcessor
from mailprocessing.mail.dryrun import DryRunMaildir
from mailprocessing.mail.maildir import MaildirMail


class MaildirProcessor(MailProcessor):
    def __init__(self, *args, **kwargs):
        self._maildir_base = None
        self._maildirs = []
        self.separator = kwargs.get('folder_separator', '.')
        self.prefix = kwargs.get('folder_prefix', '.')
        if 'dry_run' in kwargs and kwargs['dry_run'] is True:
            self._mail_class = DryRunMaildir
        else:
            self._mail_class = MaildirMail
        super(MaildirProcessor, self).__init__(*args, **kwargs)

    def get_maildir_base(self):
        return self._maildir_base

    def set_maildir_base(self, path):
        self._maildir_base = os.path.expanduser(path)

    maildir_base = property(get_maildir_base, set_maildir_base)

    def get_maildirs(self):
        return self._maildirs

    def set_maildirs(self, maildirs):
        self._maildirs = maildirs

    maildirs = property(get_maildirs, set_maildirs)

    def __iter__(self):
        if not self._maildirs:
            self.fatal_error("Error: No maildirs to process")

        self.rcfile_modified = False
        mtime_map = {}
        while True:
            if self.auto_reload_rcfile:
                current_rcfile_mtime = self._get_previous_rcfile_mtime()
                if current_rcfile_mtime != self._previous_rcfile_mtime:
                    self._previous_rcfile_mtime = current_rcfile_mtime
                    self.rcfile_modified = True
                    self.log_info("Detected modified RC file; reloading")
                    break
            for maildir in self._maildirs:
                maildir_path = os.path.join(self._maildir_base, maildir)
                for subdir in ["cur", "new"]:
                    subdir_path = os.path.join(maildir_path, subdir)
                    cur_mtime = os.path.getmtime(subdir_path)
                    if cur_mtime != mtime_map.setdefault(subdir_path, 0):
                        if cur_mtime < int(time.time()):
                            # If cur_mtime == int(time.time()) we
                            # can't be sure that everything has been
                            # processed; a new mail may be delivered
                            # later the same second.
                            mtime_map[subdir_path] = cur_mtime
                        for mail_file in os.listdir(subdir_path):
                            mail_path = os.path.join(subdir_path, mail_file)
                            yield self._mail_class(self, maildir=maildir,
                                                   mail_path=mail_path)
            if self._run_once:
                break
            time.sleep(1)

    # ----------------------------------------------------------------
    # Interface used by MailBase and descendants:

    def create_folder(self, folder, **kwargs):
        """
        Creates a new maildir folder.

        It can safely be invoked with an existing folder name since it checks
        for existence of the folder first and will do nothing if the folder
        exists. This method creates a folder's parent folders recursively by
        default. If you do not wish this behaviour, please specify
        parents=False.
        """

        parents = kwargs.get('parents', True)

        folder_list = self.path_ensure_prefix(folder, sep=self.separator)

        if len(folder_list) == 0:
            return

        if parents:
            self.create_folder(folder_list[:-1], parents=parents)

        target = self.list_path(folder_list, sep=self.separator)

        self.log("==> Creating folder %s" % target)

        try:
            self.create_maildir(os.path.join(self.maildir_base, target))
        except OSError as e:
            self.fatal_error("Couldn't create maildir %s: %s" % (target, e))

        self.log("==> Successfully created folder %s" % target)

    def create_maildir(self, name, parents=True):
        """
        Creates a new maildir.
        """
        for d in ['cur', 'new', 'tmp']:
            try:
                if parents:
                    os.makedirs(os.path.join(name, d), mode=0o700)
                else:
                    os.mkdir(os.path.join(name, d), mode=0o700)
            except OSError as e:
                if e.errno == errno.EEXIST:
                    pass
                else:
                    raise

    def create_maildir_name(self):
        """Create and return a unique name for a Maildir message."""
        hostname = socket.gethostname()
        hostname = hostname.replace("/", "\\057")
        hostname = hostname.replace(":", "\\072")
        now = time.time()
        delivery_identifier = "M{0}P{1}Q{2}R{3:0>8x}".format(
            round((now - int(now)) * 1000000),
            os.getpid(),
            self._deliveries,
            random.randint(0, 0xffffffff))
        self._deliveries += 1
        return "{0}.{1}.{2}".format(now, delivery_identifier, hostname)

    def log_io_error(self, errmsg, os_errmsg):
        self.log_error(
            "Error: {0} (error message from OS: {1})".format(
                errmsg, os_errmsg))

    def log_mail_opening_error(self, path, errmsg):
        self.log_io_error(
            "Could not open {0}; some other process probably (re)moved"
            " it".format(path),
            errmsg)

    def rename(self, source, target):
        try:
            os.rename(source, target)
        except FileNotFoundError:
            self.log_error("Error: Moving file from {0} to {1}. Maybe it doesn't exist?".format(
                source, target))
