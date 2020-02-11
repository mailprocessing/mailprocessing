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

from mailprocessing.mail.target import MailTarget
from mailprocessing.mail.header import MailHeader


class MailBase(object):
    """
    This is the base class representing email messages. If you want to create your
    own class for representing email messages you should inherit this class and
    implement the methods it mandates.
    """
    def __init__(self, processor, **kwargs):
        self._processor = processor
        self._target = MailTarget(self)
        if self.parse_mail():
            self._log_processing()

    @property
    def processor(self):
        return self._processor

    @property
    def target(self):
        return self._target

    def __getitem__(self, header_name):
        return MailHeader(
            self, header_name, self._headers.get(header_name.lower(), ""))

    def from_mailing_list(self, list_name):
        """
        Checks message is from the mailing list list_name.
        """
        list_name = list_name.lower()
        for headername in [
                "delivered-to", "mailing-list", "x-beenthere",
                "x-mailing-list"]:
            if self[headername].contains(list_name):
                self._processor.log_debug(
                    "... Mail is on mailing list {0}".format(list_name))
                return True
        self._processor.log_debug(
            "... Mail is not on mailing list {0}".format(list_name))
        return False

    def strict_mailing_list(self, list_name):
        """
        Stricter version of from_mailing_list(): only consider header names that
        only occur on mailing list messages.
        """
        list_name = list_name.lower()
        for headername in [
                "list-archive", "list-help", "list-id", "list-post",
                "list-subscribe", "x-mailing-list"]:
            if self[headername].contains(list_name):
                self._processor.log_debug(
                    "... Mail is on mailing list {0}".format(list_name))
                return True
        self._processor.log_debug(
            "... Mail is not on mailing list {0}".format(list_name))
        return False

    # Methods to implement ###

    def copy(self, folder, create=False):
        """
        Copy the message to a folder.

        The notion of what constitutes a folder depends on what your email
        messages are stored in. It may for example be a maildir, an mbox file or
        an IMAP folder.

        @folder: the destination folder to copy the message to.
        """

        message = ("You need to implement a copy() method in your "
                   "MailBase subclass.")
        raise NotImplementedError(message)

    def delete(self):
        """
        Deletes a message.
        """

        message = ("You need to implement a delete() method in your "
                   "MailBase subclass.")
        raise NotImplementedError(message)

    def forward(self, addresses, env_sender=None):
        """
        Forwards a message.

        This method forwards a message to one or more email addresses. The
        original message will be deleted.

        @addresses: list of email addresses to forward the message to.
        @env_sender: the envelope sender address to use when forwarding the
                     message.
        """

        message = ("You need to implement a forward() method in your "
                   "MailBase subclass.")

        raise NotImplementedError(message)

    def forward_copy(self, addresses, env_sender=None):
        """
        Forwards a copy of a message.

        This method forwards a message to one or more email addresses. The
        original message will remain in place.

        @addresses: list of email addresses to forward the message to.
        @env_sender: the envelope sender address to use when forwarding the
                     message.
        """

        message = ("You need to implement a forward_copy() method in your "
                   "MailBase subclass.")
        raise NotImplementedError(message)

    def move(self, folder, create=False):
        """
        Move the message to a folder.

        The notion of what constitutes a folder depends on what your email
        messages are stored in. It may for example be a maildir, an mbox file or
        an IMAP folder.

        @folder: the destination folder to move the message to.
        """

        message = ("You need to implement a move() method in your "
                   "MailBase subclass.")
        raise NotImplementedError(message)

    def parse_mail(self):
        """
        Parse and store message headers.

        This method will parse an email's headers and store them in the
        self._headers dict. Keys are header names converted to lower case,
        values are these header's contents. Returns True upon success, False
        upon failure.
        """

        message = ("You need to implement a parse_mail() method in your "
                   "MailBase subclass.")
        raise NotImplementedError(message)

    def log_processing(self):
        """
        Log message metadata as MailBase subclasses are initialized.

        This message is invoked by the MailBase constructor to write message
        metadata (typically a selection of headers) to the log file.
        """

        message = ("You need to implement a log_processing() method in your "
                   "MailBase subclass.")
        raise NotImplementedError(message)

    def is_seen(self):
        """
        Check whether a message has been read.

        This method returns True if a message has been read by the user, False
        otherwise. What constitutes having been read (commonly some sort of
        flag) is left up to the subclass' implementation.
        """

        message = ("You need to implement a is_seen() method in your "
                   "MailBase subclass.")
        raise NotImplementedError(message)

    def is_flagged(self):
        """
        Check whether a message has been flagged.

        This method returns True if a message has been explicitly flagged by
        the user, False otherwise. What constitutes having been flagged
        (commonly some sort of message attribute that gets set after the user
        flags the message) is left up to the subclass' implementation.
        """

        message = ("You need to implement a is_seen() method in your "
                   "MailBase subclass.")
        raise NotImplementedError(message)
    # ----------------------------------------------------------------
