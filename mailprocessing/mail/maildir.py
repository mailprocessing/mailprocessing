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

import os
import shutil
import subprocess

from email import errors as email_errors
from email import header as email_header
from email import parser as email_parser

from mailprocessing.mail.base import MailBase
from mailprocessing.util import iso_8601_now
from mailprocessing.util import sha1sum


class MaildirMail(MailBase):
    def __init__(self, processor, **kwargs):
        self._maildir = kwargs['maildir']
        self._path = kwargs['mail_path']
        self._headers = {}
        super(MaildirMail, self).__init__(processor, **kwargs)

    @property
    def maildir(self):
        return self._maildir

    @property
    def path(self):
        return self._path

    def copy(self, maildir, **kwargs):
        sep = kwargs.get('sep', self._processor.separator)

        # Take care of prefix here and ensure create_folder() does not mess
        # with it.
        folder_list = self._processor.path_ensure_prefix(maildir, sep=sep)
        maildir = self._processor.list_path(folder_list, sep=sep)

        self._processor.log("==> Copying to {0}".format(target))
        self._copy(maildir, *kwargs)

    def delete(self):
        self._processor.log("==> Deleting")
        self._delete()

    def forward(self, addresses, env_sender=None):
        self._forward(True, addresses, env_sender)

    def forward_copy(self, addresses, env_sender=None):
        self._forward(False, addresses, env_sender)

    def move(self, maildir, **kwargs):
        sep = kwargs.get('sep', self._processor.separator)

        # Take care of prefix here and ensure create_folder() does not mess
        # with it.
        folder_list = self._processor.path_ensure_prefix(maildir, sep=sep)
        maildir = self._processor.list_path(folder_list, sep=sep)

        if kwargs.get('create', False) and not os.path.isdir(maildir):
            try:
                self._processor.create_folder(folder_list, **kwargs)
            except OSError as e:
                raise
                self._processor.fatal_error("Couldn't create maildir "
                                            "%s: %s" % (maildir, e))
        self._processor.log("==> Moving to {0}".format(maildir))
        flagpart = self._get_flagpart()
        target = os.path.join(
            self._processor.maildir_base,
            maildir,
            self.path.split(os.sep)[-2],  # new/cur
            self._processor.create_maildir_name() + flagpart)
        try:
            self._processor.rename(self.path, target)
            self._processor.log("==> Moved: \n(src) {0} -->\n(tgt) {1}".format(self.path, target))
        except IOError as e:
            self._processor.log_io_error(
                "Could not rename {0} to {1}".format(self.path, target),
                e)

    def parse_mail(self):
        # We'll just use some encoding that handles all byte values
        # without bailing out. Non-ASCII characters should not exist
        # in the headers according to email standards, but if they do
        # anyway, we mustn't crash.
        encoding = "iso-8859-1"

        self._processor.log("")
        self._processor.log("New mail detected at {0}:".format(iso_8601_now()))
        self._processor.log("Path:       {0}".format(ascii(self.path)))
        try:
            fp = open(self.path, encoding=encoding)
        except IOError as e:
            # The file was probably (re)moved by some other process.
            self._processor.log_mail_opening_error(self.path, e)
            return False
        headers = email_parser.Parser().parse(fp, headersonly=True)
        fp.close()
        for name in headers.keys():
            value_parts = []
            for header in headers.get_all(name, []):
                try:
                    for (s, c) in email_header.decode_header(header):
                        # email.header.decode_header in Python 3.x may
                        # return either [(str, None)] or [(bytes,
                        # None), ..., (bytes, encoding)]. We must
                        # compensate for this.
                        if not isinstance(s, str):
                            s = s.decode(c if c else "ascii")
                        value_parts.append(s)
                except (email_errors.HeaderParseError, LookupError,
                        ValueError):
                    self._processor.log_error(
                        "Error: Could not decode header {0}".format(
                            ascii(header)))
                    value_parts.append(header)
            self._headers[name.lower()] = " ".join(value_parts)
        return True

    # ----------------------------------------------------------------

    def _copy(self, maildir, **kwargs):
        if kwargs.get('create', False) and not os.path.isdir(maildir):
            try:
                self._processor.create_folder(maildir, **kwargs)
            except OSError as e:
                self._processor.fatal_error("Couldn't create maildir "
                                            "%s: %s" % (target, e))
        try:
            source_fp = open(self.path, "rb")
        except IOError as e:
            # The file was probably (re)moved by some other process.
            self._processor.log_mail_opening_error(self.path, e)
            return

        tmp_target = os.path.join(
            self._processor.maildir_base,
            maildir,
            "tmp",
            self._processor.create_maildir_name())
        try:
            tmp_target_fp = os.fdopen(
                os.open(tmp_target, os.O_WRONLY | os.O_CREAT | os.O_EXCL),
                "wb")
        except IOError as e:
            self._processor.log_io_error(
                "Could not open {0} for writing".format(tmp_target),
                e)
            return
        try:
            shutil.copyfileobj(source_fp, tmp_target_fp)
            source_fp.close()
            tmp_target_fp.close()
        except IOError as e:
            self._processor.log_io_error(
                "Could not copy {0} to {1}".format(self.path, tmp_target),
                e)
            return

        flagpart = self._get_flagpart()
        target = os.path.join(
            self._processor.maildir_base,
            maildir,
            self.path.split(os.sep)[-2],  # new/cur
            self._processor.create_maildir_name() + flagpart)
        try:
            self._processor.rename(tmp_target, target)
        except IOError as e:
            self._processor.log_io_error(
                "Could not rename {0} to {1}".format(tmp_target, target),
                e)

    def _delete(self):
        try:
            os.unlink(self.path)
        except OSError as e:
            # The file was probably moved.
            self._processor.log_io_error(
                "Could not delete {0}; some other process probably (re)moved"
                " it".format(self.path),
                e)

    def _forward(self, delete, addresses, env_sender):
        if isinstance(addresses, str):
            addresses = [addresses]
        else:
            addresses = list(addresses)
        if delete:
            copy = ""
        else:
            copy = " copy"
        flags = self._processor.sendmail_flags
        if env_sender is not None:
            flags += " -f {0}".format(env_sender)

        self._processor.log(
            "==> Forwarding{0} to {1!r}".format(copy, addresses))
        try:
            source_fp = open(self.path, "rb")
        except IOError as e:
            # The file was probably moved.
            self._processor.log_mail_opening_error(self.path, e)
            return

        p = subprocess.Popen(
            "{0} {1} -- {2}".format(self._processor.sendmail,
                                    flags,
                                    " ".join(addresses)
                                    ),
            shell=True,
            stdin=subprocess.PIPE)
        shutil.copyfileobj(source_fp, p.stdin)
        p.stdin.close()
        p.wait()
        source_fp.close()

        if delete:
            self._delete()

    def is_flagged(self):
        flags = self._get_flagpart()
        if 'F' in flags:
            self._processor.log_debug("... Mail is flagged")
            return True
        else:
            self._processor.log_debug("... Mail is not flagged")
            return False

    def is_seen(self):
        flags = self._get_flagpart()
        if 'S' in flags:
            self._processor.log_debug("... Mail is seen")
            return True
        else:
            self._processor.log_debug("... Mail is not seen")
            return False

    def _get_flagpart(self):
        parts = os.path.basename(self.path).split(":2,")
        if len(parts) == 2:
            return ":2," + parts[1]
        else:
            return ""

    def _log_processing(self):
        try:
            fp = open(self.path, "rb")
        except IOError as e:
            # The file was probably (re)moved by some other process.
            self._processor.log_mail_opening_error(self.path, e)
            return
        self._processor.log("SHA1:       {0}".format(ascii(sha1sum(fp))))
        for name in "Message-ID Subject Date From To Cc".split():
            self._processor.log(
                "{0:<11} {1}".format(name + ":", ascii(self[name])))
