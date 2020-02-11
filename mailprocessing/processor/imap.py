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
import imaplib
import json
import ssl
import re
import sys

from email import errors as email_errors
from email import header as email_header
from email import parser as email_parser

from mailprocessing import signals

from mailprocessing.util import batch_list

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

        self.user = kwargs['user']
        self.password = kwargs['password']
        self.cache_file = kwargs.get('cache_file', None)
        self.header_cache = {}
        self._folders = {}
        self.uidvalidity = {}
        self.selected = None
        self.flag_batchsize = kwargs.get('flag_batchsize')
        self.header_batchsize = kwargs.get('header_batchsize')

        self.interval = kwargs['interval']
        self.host = kwargs['host']

        if kwargs['log_level'] > 2:
            imaplib.Debug = 1

        if kwargs['port']:
            self.port = kwargs['port']

        if kwargs['use_ssl']:
            if not kwargs['port']:
                self.port = 993
            self.ssl_context = ssl.SSLContext(getattr(ssl, 'PROTOCOL_TLS', ssl.PROTOCOL_SSLv23))
            if kwargs['insecure']:
                self.ssl_context.verify_mode = ssl.CERT_NONE
            else:
                self.ssl_context.verify_mode = ssl.CERT_REQUIRED
                self.ssl_context.check_hostname = True
            if kwargs['certfile']:
                self.ssl_context.load_cert_chain(kwargs['certfile'])
            else:
                self.ssl_context.load_default_certs()
            self.connect_ssl()
        else:
            self.ssl_context = None
            if not kwargs['port']:
                self.port = 143
            else:
                self.port=kwargs['port']
            self.connect_plain()

        if 'dry_run' in kwargs and kwargs['dry_run'] is True:
            self._mail_class = DryRunImap
        else:
            self._mail_class = ImapMail

        self.prefix = kwargs.get('folder_prefix', None)
        self.separator = kwargs.get('folder_separator', None)

        self._separator_prefix(cmd_separator=self.separator,
                               cmd_prefix=self.prefix)

        self.log("==> Separator character is `%s`" % self.separator)
        self.log("==> Folder name prefix is `%s`" % self.prefix)

        self.cache_delete = {}

        if kwargs['folders'] is not None:
            self.set_folders(kwargs['folders'])

    def authenticate(self):
        try:
            self.imap.login(self.user, self.password)
        except self.imap.error as e:
            self.fatal_imap_error("Login to IMAP server failed", e)

    def connect_plain(self):
        try:
            self.imap = imaplib.IMAP4(host=self.host, port=self.port)
        except Exception as e:
            self.fatal_error("Couldn't connect to IMAP server "
                             "imap://%s:%d: %s" % (self.host, self.port, e))
        self.authenticate()

    def connect_ssl(self, **kwargs):
        try:
            self.imap = imaplib.IMAP4_SSL(host=self.host,
                                          port=self.port,
                                          ssl_context=self.ssl_context)
        except Exception as e:
            self.fatal_error("couldn't connect to imap server "
                             "imaps://%s:%d: %s" % (self.host, self.port, e))
        self.authenticate()

    def reconnect(self):
        # Ignore errors when logging out: if the connection is already logged
        # out, we'll get a bad file descriptor.
        try:
            self.imap.logout()
        except OSError:
            pass

        if self.ssl_context is None:
            self.connect_plain()
        else:
            self.connect_ssl()

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
            if folder not in self.header_cache:
                self.header_cache[folder] = {}
            if folder not in self.cache_delete:
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
        self.log_debug("Listing messages in folder %s" % folder)

        try:
            ret, data = self.imap.uid('search', None, "ALL")
        except self.imap.error as e:
            self.fatal_error("Listing messages in folder %s "
                             "failed: %s" % (folder, e))
        if ret != 'OK':
            self.log_imap_error("Listing messages in folder %s failed: %s" % (folder,
                                                                              ret))
            return []

        messages = data[0].decode('ascii').split()

        self.log_debug("UIDs in folder %s: %s" % (folder, ",".join(messages)))

        return messages

    def __iter__(self):
        """
        Iterator method used to invoke the processor from the filter
        configuration file.
        """
        if not self._folders:
            self.fatal_error("Error: No folders to process")

        self.rcfile_modified = False

        while not signals.signal_event.is_set():
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
            else:
                self.clean_sleep()

            signals.signal_event.wait(self.interval)

            if signals.terminate():
                # Simply exit, since clean_sleep() will already have performed
                # all exit rites if get here.
                sys.exit(0)

            self.reconnect()
            self._cache_headers()

    # ----------------------------------------------------------------

    def _cache_headers(self):
        """
        This method updates the processor's header cache for all folders this
        processor is configured to process.
        """

        self.log_debug("==> Updating header cache...")

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

        self.log_debug("Saving header cache to disk.")

        # Delete UIDs marked for deletion when the messages where deleted/moved
        for folder in self.cache_delete:
            for uid in self.cache_delete[folder]:
                self.header_cache[folder]['uids'].pop(uid)
            self.cache_delete[folder] = []

        # Drop unserializable mail objects from header cache before saving.
        for folder in self.header_cache:
            if 'uids' in self.header_cache[folder]:
                for uid in self.header_cache[folder]['uids']:
                    try:
                        self.header_cache[folder]['uids'][uid].pop('obj')
                    except KeyError:
                        self.log_error("Couldn't drop Mail object for UID %s in "
                                       "folder %s from cache: Mail object "
                                       "missing" % (uid, folder))
        try:
            f = open(self.cache_file, mode='w')
            cache = json.dump(cache, f)
            f.close()
        except OSError as e:
            self.fatal_error("Couldn't save cache to "
                             "%s: %s" % (self.cache_file, e))

        self.log_debug("Header cache saved.")

    def _download_headers_batched(self, folder, uids):
        """
        This method downloads headers and flags for a list of message UIDs in a
        batched manner. It returns a dict of messages keyed by UID upon successful
        fetch and will fail hard otherwise. Entries in the dictionary returned will
        have a 'flags' and 'headers' key.
        """

        msgs = {}

        for batch in batch_list(uids, self.header_batchsize):
            uid_list = ",".join(uids)

            self.log_debug("==> Downloading headers for UIDs %s" % uid_list)

            try:
                self.select(folder)
                ret, data = self.imap.uid('fetch', uid_list,
                                          "(FLAGS BODY.PEEK[HEADER])")
            except self.imap.error as e:
                # Anything imaplib raises an exception for is fatal here.
                self.fatal_error("Error retrieving headers for message "
                                 "UIDs %s: %s" % (",".join(uid_list), e))

            if ret != 'OK':
                self.fatal_error(
                    "Error: Header retrieval failed with status "
                    "%s for messages: %s" % (ret, ",".join(uid_list)))

            for i in range(0, len(data), 2):
                next_decoded = data[i + 1].decode('ascii')

                # The data we are looking for may be in data[i][0] or data[i+1],
                # depending on the IMAP server. Let's find out where it is:

                if next_decoded == ')':
                    # Dovecot
                    uid_raw = data[i][0].decode('ascii')

                if 'UID' in next_decoded:
                    # Groupwise
                    uid_raw = next_decoded

                uid = re.search('UID (\d+)', uid_raw).group().split(" ")[1]

                flags = []
                flags_raw = imaplib.ParseFlags(data[i][0])

                for flag in flags_raw:
                    flags.append(flag.decode('ascii'))

                headers_raw = email_parser.Parser().parsestr(data[i][1].decode('ascii',
                                                                               'ignore'),
                                                             headersonly=True)
                headers = {}
                for name in headers_raw.keys():
                    value_parts = []
                    for header in headers_raw.get_all(name, []):
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
                                        "Error: Could not decode header {0} in message "
                                        "UID {1}".format(ascii(header), uid))
                                value_parts.append(header)
                    headers[name.lower()] = " ".join(value_parts)

                    msgs[uid] = {}
                    msgs[uid]['flags'] = flags
                    msgs[uid]['headers'] = headers

        self.log_debug("==> Header download finished for for UIDs %s" % uid_list)

        return msgs

    def _initialize_cache(self, folder):
        """
        This method initializes a cache data structure for a given folder.
        """
        cache = {}
        uids = self.list_messages(folder)
        messages = self._download_headers_batched(folder, uids)

        for message_uid in uids:
            if signals.terminate():
                self.clean_exit()
            msg_obj = self._mail_class(self, folder=folder,
                                       uid=message_uid,
                                       headers=messages[message_uid]['headers'],
                                       flags=messages[message_uid]['flags'])
            cache[message_uid] = {}
            cache[message_uid]['headers'] = msg_obj._headers
            cache[message_uid]['flags'] = msg_obj.message_flags
            cache[message_uid]['obj'] = msg_obj
        return cache

    def _update_cache(self, folder, cache):
        """
        This method updates an existing header cache data structure for a given
        folder. Message UIDs that do not exist in the cache, yet, will be
        added.
        """

        self.log_debug("Updating cache")

        message_list = self.list_messages(folder)
        uids_download = []

        # Remove stale cache entries
        stale = []
        for message in cache:
            if message not in message_list:
                stale.append(message)
        for message in stale:
            cache.pop(message)

        for message in message_list:
            if signals.terminate():
                self.clean_exit()
            if message in cache:
                cached_headers = cache[message]['headers']
                cached_flags = cache[message]['flags']
                msg_obj = self._mail_class(self, folder=folder,
                                           uid=message,
                                           headers=cached_headers,
                                           flags=cached_flags)
                cache[message]['obj'] = msg_obj

            else:
                uids_download.append(message)

        self.log_debug("Cache miss for the following UIDs: %s" % ",".join(uids_download))

        if len(uids_download) != 0:
            messages = self._download_headers_batched(folder, uids_download)
            for uid in uids_download:
                msg_obj = self._mail_class(self, folder=folder,
                                           uid=uid,
                                           headers=messages[uid]['headers'],
                                           flags=messages[uid]['flags'])
                cache[uid] = {}
                cache[uid]['headers'] = msg_obj._headers
                cache[uid]['flags'] = msg_obj.message_flags
                cache[uid]['obj'] = msg_obj
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

        self.log_debug("status: %s" % status)
        self.log_debug("data: %s" % data)

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

    def get_flags(self, folder):
        """
        Get message flags for a folder.
        """
        self.log_debug("%d UIDs in cache" % len(self.header_cache[folder]['uids']))

        uid_list = list(self.header_cache[folder]['uids'].keys())

        if len(uid_list) == 0:
          return ([], [])

        for batch in batch_list(uid_list, self.flag_batchsize):
            self.log_debug("%d UIDs in batch" % len(batch))
            ret_full = []
            data_full = []

            try:
                self.select(folder)
                uids = ",".join(batch)
                ret, data = self.imap.uid('fetch', uids, "FLAGS")
                ret_full.append(data)
                data_full.extend(data)
            except self.imap.error as e:
                self.fatal_error(
                    "Could not retrieve message flags for folder {0}, UIDs {1}: {2}"
                    "{1}".format(folder, uids, e))

            return (ret_full, data_full)

    def refresh_flags(self):
        """
        Refreshes message flags for all messages in header cache.
        """

        self.log_info("==> Updating message flags...")
        for folder in self.header_cache:
            try:
                ret, data = self.get_flags(folder)
            except self.imap.abort:
                self.log_error("IMAP connection aborted, reconnecting.")
                # Reconnect if the connection has timed out due to the header
                # cache update taking too long (may happen on mailboxes with
                # lots of messages).
                self.reconnect()
                ret, data = self.get_flags(folder)
            for msg in data:
                flags = []
                flags_raw = imaplib.ParseFlags(msg)
                for flag in flags_raw:
                    flags.append(flag.decode('ascii'))
                uid = re.search('UID (\d+)',
                                msg.decode('ascii')).group().split(" ")[1]
                self.log_debug("UID: %s" % uid)
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

    def clean_sleep(self):
        """
        Close IMAP connection and save cache before going to sleep.
        """

        self.log("==> Saving header cache...")
        self._save_cache(self.header_cache)
        self.log("==> Closing IMAP connection...")
        self.imap.close()
        self.imap.logout()
        self.log("==> ...done.")

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
