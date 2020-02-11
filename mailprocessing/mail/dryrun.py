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

from mailprocessing.mail.imap import ImapMail
from mailprocessing.mail.maildir import MaildirMail


class DryRunImap(ImapMail):
    def __init__(self, *args, **kwargs):
        super(DryRunImap, self).__init__(*args, **kwargs)

    def copy(self, maildir, **kwargs):
        maildir = self.processor.list_path(maildir,
                                           sep=self.processor.separator)
        self._processor.log("==> Copying to {0}".format(maildir))

    def delete(self):
        self._processor.log("==> Deleting")

    def forward(self, addresses, env_sender=None):
        self._forward(True, addresses, env_sender)

    def forward_copy(self, addresses, env_sender=None):
        self._forward(False, addresses, env_sender)

    def move(self, maildir, **kwargs):
        maildir = self.processor.list_path(maildir,
                                           sep=self.processor.separator)
        self._processor.log("==> Moving to {0}".format(maildir))

    # ----------------------------------------------------------------

    def _forward(self, delete, addresses, env_sender):
        if isinstance(addresses, str):
            addresses = [addresses]
        else:
            addresses = list(addresses)
        if not delete:
            copy = " copy"
        else:
            copy = ""
        self._processor.log(
            "==> Forwarding{0} to {1!r}{2}".format(
                copy,
                addresses,
                " (envelope sender: {0}".format(env_sender)
                if env_sender is not None else ""))


class DryRunMaildir(MaildirMail):
    def __init__(self, *args, **kwargs):
        super(DryRunMaildir, self).__init__(*args, **kwargs)

    def copy(self, maildir, **kwargs):
        maildir = self.processor.list_path(maildir,
                                           sep=self.processor.separator)
        self._processor.log("==> Copying to {0}".format(maildir))

    def delete(self):
        self._processor.log("==> Deleting")

    def forward(self, addresses, env_sender=None):
        self._forward(True, addresses, env_sender)

    def forward_copy(self, addresses, env_sender=None):
        self._forward(False, addresses, env_sender)

    def move(self, maildir, **kwargs):
        maildir = self.processor.list_path(maildir,
                                           sep=self.processor.separator)
        self._processor.log("==> Moving to {0}".format(maildir))

    # ----------------------------------------------------------------

    def _forward(self, delete, addresses, env_sender):
        if isinstance(addresses, str):
            addresses = [addresses]
        else:
            addresses = list(addresses)
        if not delete:
            copy = " copy"
        else:
            copy = ""
        self._processor.log(
            "==> Forwarding{0} to {1!r}{2}".format(
                copy,
                addresses,
                " (envelope sender: {0}".format(env_sender)
                if env_sender is not None else ""))
