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

import codecs
import errno
import imaplib
import json
import locale
import os
import random
import socket
import ssl
import re
import sys
import time

from mailprocessing import signals

from mailprocessing.util import iso_8601_now
from mailprocessing.util import safe_write

from mailprocessing.mail.dryrun import DryRunImap
from mailprocessing.mail.imap import ImapMail
from mailprocessing.processor.generic import MailProcessor

class ImapProcessor(MailProcessor):
    """
    This class is used for processing emails in IMAP mailboxes. It is chiefly
    concerned with folder and account level operations, such as establishing
    the IMAP session, creating and listing folders.
    """
    def __init__(self, *args, **kwargs):
        super(ImapProcessor, self).__init__(*args, **kwargs)

        self.cache_file = kwargs.get('cache_file', None)
        self.header_cache = {}
        self._folders = {}
        self.uidvalidity = {}
        self.selected = None

        self.interval = kwargs['interval']
        if kwargs['log_level'] > 2:
            imaplib.Debug = 1

        if kwargs['port']:
            port = kwargs['port']

        if kwargs['use_ssl']:
            if not kwargs['port']:
                port = 993
            ssl_context = ssl.SSLContext(getattr(ssl, 'PROTOCOL_TLS', ssl.PROTOCOL_SSLv23))
            if kwargs['insecure']:
                ssl_context.verify_mode = ssl.CERT_NONE
            else:
                ssl_context.verify_mode = ssl.CERT_REQUIRED
                ssl_context.check_hostname = True
            if kwargs['certfile']:
                ssl_context.load_cert_chain(kwargs['certfile'])
            else:
                ssl_context.load_default_certs()

            try:
                self.imap = imaplib.IMAP4_SSL(host=kwargs['host'],
                                              port=port,
                                              ssl_context=ssl_context)
            except Exception as e:
                self.fatal_error("Couldn't connect to IMAP server "
                                 "imaps://%s:%d: %s" % ( kwargs['host'],
                                                         port, e))
        else:
            try:
                if not kwargs['port']:
                    port = 143
                self.imap = imaplib.IMAP4(host=kwargs['host'], port=port)
            except Exception as e:
                self.fatal_error("Couldn't connect to IMAP server "
                                 "imap://%s:%d: %s" % ( kwargs['host'],
                                                        kwargs['port'], e))

        if 'dry_run' in kwargs and kwargs['dry_run'] is True:
            self._mail_class = DryRunImap
        else:
            self._mail_class = ImapMail

        try:
            self.imap.login(kwargs['user'], kwargs['password'])
        except self.imap.error as e:
            self.fatal_imap_error("Login to IMAP server", e)

        self.prefix = kwargs.get('folder_prefix', None)
        self.separator = kwargs.get('folder_separator', None)

        self._separator_prefix(cmd_separator=self.separator,
                               cmd_prefix=self.prefix)

        self.log("==> Separator character is `%s`" % self.separator)
        self.log("==> Folder name prefix is `%s`" % self.prefix)

        self.cache_delete = {}

        if kwargs['folders'] != None:
            self.set_folders(kwargs['folders'])


    def get_folders(self):
        return self._folders

    def set_folders(self, folders):
        """
        Setter method for the folders to operate on. Can be used to update the
        list of folders at runtime.
        """
        self._folders = folders

        self.log("==> Processing the following IMAP folders:")
        for folder in self.folders:
            self.log("    " + folder)
            self.log("")

        for folder in self.folders:
            if not folder in self.header_cache:
                self.header_cache[folder] = {}
            if not folder in self.cache_delete:
                self.cache_delete[folder] = []
        self._cache_headers()

    folders = property(get_folders, set_folders)

    # ----------------------------------------------------------------
    # Logging methods

    def log_imap_error(self, operation, errmsg):
        self.log_error(
            "IMAP Error: {0} failed: {1}".format(
                operation, errmsg))

    def fatal_imap_error(self, operation, errmsg):
        self.fatal_error(
            "Fatal IMAP Error: {0} failed: {1}".format(
                operation, errmsg))

    # ----------------------------------------------------------------


    def create_folder(self, folder, parents=True):
        """
        Creates a new IMAP folder.

        It can safely be invoked with an existing folder name since it checks
        for existence of the folder first and will do nothing if the folder
        exists. This method creates a folder's parent directories recursively
        by default. If you do not wish this behaviour, please specify
        parents=False.
        """

        folder_list = self.path_list(folder, sep=self.separator)

        if len(folder_list) == 0:
            return

        if parents:
            self.create_folder(folder_list[:-1], parents=parents)

        target = self.list_path(folder, sep=self.separator)

        exists, detail = self._status(target)

        if exists:
            self.log("==> Not creating folder %s: folder exists." % folder)
            return

        self.log("==> Creating folder %s" % target)
        try:
            status, data = self.imap.create(target)
        except self.imap.error as e:
            self.fatal_error("Couldn't create folder %s: %s", target, e)
        if status != 'OK':
            self.fatal_error("Couldn't create folder "
                             "%s: %s / %s" % (target,
                                              status, data[0].decode('ascii')))
        try:
            status, data = self.imap.subscribe(target)
        except self.imap.error as e:
            self.fatal_error("Couldn't subscribe to folder %s: %s", target, e)
        if status != 'OK':
            self.fatal_error("Couldn't subscribe to folder "
                             "%s: %s / %s" % (target,
                                              status, data[0].decode('ascii')))

        self.log("==> Successfully created folder %s" % target)

    def list_messages(self, folder):
        """
        Lists all messages in an IMAP folder.
        """

        self.select(folder)

        try:
            ret, data = self.imap.uid('search', None, "ALL")
        except self.imap.error as e:
            self.fatal_error("Listing messages in folder %s "
                             "failed: %s" % (folder, e))
        if ret != 'OK':
            self.log_imap_error("Listing messages in folder %s failed: %s" % (folder,
                                                                              ret))
            return []

        return data[0].decode('ascii').split()


    def __iter__(self):
        """
        Iterator method used to invoke the processor from the filter
        configuration file.
        """
        if not self._folders:
            self.fatal_error("Error: No folders to process")

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

            for folder in self.folders:
                for message in self.header_cache[folder]['uids']:
                    yield self.header_cache[folder]['uids'][message]['obj']

            if self._run_once:
                self.clean_exit()
            time.sleep(self.interval)
            self._cache_headers()


    # ----------------------------------------------------------------

    def _cache_headers(self):
        """
        This method updates the processor's header cache for all folders this
        processor is configured to process.
        """
        self.log("Updating header cache...")

        if self.cache_file is not None:
            self._cache_headers_file()
        else:
            self._cache_headers_memory()

    def _cache_headers_memory(self):
        """
        This method creates the run time memory header cache.
        """

        for folder in self.folders:
            uidvalidity = self._uidvalidity(folder)
            if folder not in self.header_cache:
                self.header_cache[folder] = {}
                self.header_cache[folder]['uids'] = self._initialize_cache(
                    folder)
                self.header_cache[folder]['uidvalidity'] = uidvalidity
                continue

            if uidvalidity == self.header_cache[folder]['uidvalidity']:
                self.header_cache[folder]['uids'] = self._update_cache(
                    folder, self.header_cache[folder]['uids'])
            else:
                self.header_cache[folder]['uids'] = self._initialize_cache(
                    folder)
                self.header_cache[folder]['uidvalidity'] = uidvalidity

        self.log("Header cache up to date.")

    def _cache_headers_file(self):
        """
        This method updates the header cache from a cache file. The cache file
        is created if it does not exist, yet.
        """

        self.header_cache = self._load_cache()
        self._cache_headers_memory()
        self.refresh_flags()

    def _load_cache(self):
        """
        This method loads a previously stored header cache from the cache file.
        """
        try:
            f = open(self.cache_file)
            cache = json.load(f)
            f.close()
            return cache
        except OSError as e:
            if e.errno == errno.ENOENT:
                return {}
            else:
                self.fatal_error("Couldn't load stored cache from "
                                 "%s: %s" % (self.cache_file, e))
        except Exception as e:
            self.fatal_error("Couldn't load stored cache from "
                             " %s: %s" % (self.cache_file, e))

    def _save_cache(self, cache):
        """
        This method dumps the current state of the header cache to the cache
        file.
        """

        # Delete UIDs marked for deletion when the messages where deleted/moved
        for folder in self.cache_delete:
            for uid in self.cache_delete[folder]:
                self.header_cache[folder]['uids'].pop(uid)

        # Drop unserializable mail objects from header cache before saving.
        for folder in self.header_cache:
            for uid in self.header_cache[folder]['uids']:
                self.header_cache[folder]['uids'][uid].pop('obj')
        try:
            f = open(self.cache_file, mode='w')
            cache = json.dump(cache, f)
            f.close()
        except OSError as e:
            self.fatal_error("Couldn't save cache to "
                             "%s: %s" % (self.cache_file, e))

    def _initialize_cache(self, folder):
        """
        This method initializes a cache data structure for a given folder.
        """
        cache = {}
        for message in self.list_messages(folder):
            if signals.signal_received is not None:
                self.clean_exit()
            msg_obj = self._mail_class(self, folder=folder,
                                       uid=message)
            cache[message] = {}
            cache[message]['headers'] = msg_obj._headers
            cache[message]['flags'] = msg_obj.message_flags
            cache[message]['obj'] = msg_obj
        return cache

    def _update_cache(self, folder, cache):
        """
        This method updates an existing header cache data structure for a given
        folder. Message UIDs that do not exist in the cache, yet, will be
        added.
        """

        message_list = self.list_messages(folder)


        # Remove stale cache entries
        stale = []
        for message in cache:
            if message not in message_list:
                stale.append(message)
        for message in stale:
            cache.pop(message)

        for message in message_list:
            if signals.signal_received is not None:
                self.clean_exit()
            if message in cache:
                cached_headers = cache[message]['headers']
                cached_flags = cache[message]['flags']
                msg_obj = self._mail_class(self, folder=folder,
                                                 uid=message,
                                                 headers=cached_headers,
                                                 flags=cached_flags)
            else:
                msg_obj = self._mail_class(self, folder=folder,
                                           uid=message)
                cache[message] = {}
                cache[message]['headers'] = msg_obj._headers
                cache[message]['flags'] = msg_obj.message_flags
            cache[message]['obj'] = msg_obj
        return cache

    def _uidvalidity(self, folder):
        """
        This message returns the IMAP UIDVALIDITY for a given folder. This
        information is needed to determine whether the cache for a given folder
        needs to be reinitialized.
        """
        if folder not in self.uidvalidity:
            self.select(folder)
        return self.uidvalidity[folder]

    def select(self, folder):
        """
        Performs an IMAP SELECT on folder.
        """

        # Make sure the folder name is prepended with prefix where applicable.
        folder = self.path_ensure_prefix(folder)
        folder = self.list_path(folder)

        self.log("==> Selecting folder %s" % folder)

        try:
            status, data = self.imap.select(mailbox=folder)
        except self.imap.error as e:
            self.fatal_error("Couldn't select folder %s: %s" % (folder, e))
        if status != 'OK':
            self.fatal_error("Couldn't select folder %s: %s / %s" % (folder,
                              status, data[0].decode('ascii')))

        v_string = self.imap.response('UIDVALIDITY')[1][0].decode('ascii')
        self.uidvalidity[folder] = v_string

        self.selected = folder
        self.log("==> Folder %s selected." % folder)

        return True

    def _separator_prefix(self, cmd_separator=None, cmd_prefix=None):
        """
        Retrieves name space prefix and separator from IMAP server and sets
        self.separator and self.prefix accordingly. If any of these is
        specified through a command line parameter, the value provided on the
        command line takes precedence.
        """

        try:
            status, data = self.imap.list('""', '%')
        except self.imap.error as e:
            self.fatal_error("Couldn't issue LIST command: %s" % e)
        if status != 'OK':
            self.fatal_error("Couldn't issue LIST command: "
                             "%s / %s" % (status, data[0].decode('ascii')))

        resp = data[0].decode('ascii').split(" ")
        attributes = resp[0]
        server_separator = resp[1].strip('"')
        root_folder = resp[2].strip('"')

        root_has_children = '\\HasChildren' in attributes

        if cmd_separator is None:
            self.separator = server_separator

        # This should catch at least some of these weird IMAP servers
        # that store everything under INBOX. Use --folder-prefix for
        # the rest for now.
        if cmd_prefix is None and root_has_children:
            self.prefix = root_folder
        else:
            self.prefix = ""

    def refresh_flags(self):
        """
        Refreshes message flags for all messages in header cache.
        """

        self.log_info("==> Updating message flags...")
        for folder in self.header_cache:
            self.select(folder)
            uids = ",".join(self.header_cache[folder]['uids'])
            try:
                ret, data = self.imap.uid('fetch', uids, "FLAGS")
            except self.imap.error as e:
                self.fatal_error(
                    "Error forwarding: Could not retrieve message flags for folder {0}: {1}"
                    "{1}".format(folder, e))
            for msg in data:
                flags = []
                flags_raw = imaplib.ParseFlags(msg)
                for flag in flags_raw:
                   flags.append(flag.decode('ascii'))
                uid = m = re.search('UID (\d+)',
                                    msg.decode('ascii')).group().split(" ")[1]
                self.log_debug ("UID: %s" % uid)
                self.log_debug("  server flags: %s" % flags)
                self.log_debug("   cache flags: %s" %
                               self.header_cache[folder]['uids'][uid]['flags'])
                self.header_cache[folder]['uids'][uid]['flags'] = flags
                self.header_cache[folder]['uids'][uid]['obj'].message_flags = flags
        self.log_info("==> Message flags updated.")

    def _status(self, folder):
        """
        Performs an IMAP STATUS on folder. Primarily useful for checking folder
        existence.
        """
        try:
            status, data = self.imap.select(mailbox=folder)
        except self.imap.error as e:
            self.fatal_error("Couldn't query status for "
                             "folder %s: %s" % (folder, e))
        data = data[0].decode('ascii')
        # STATUS ends SELECT state, so return to previously selected folder.
        self.select(self.selected)
        return (status == 'OK', data)

    def clean_exit(self):
        """
        Close connnection and exit in a clean manner.
        """

        self.log("==> Saving header cache...")
        self._save_cache(self.header_cache)
        self.log("==> Closing IMAP connection...")
        self.imap.close()
        self.imap.logout()
        self.log("==> ...done.")
        sys.exit(0)
