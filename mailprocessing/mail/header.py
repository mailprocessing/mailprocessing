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

import re


class MailHeader(object):
    def __init__(self, mail, name, text):
        self._mail = mail
        self._name = name
        self._text = text

    def __eq__(self, x):
        return self._text == x

    def __ne__(self, x):
        return not self._text == x

    def __str__(self):
        return self._text

    def __repr__(self):
        return repr(self._text)

    def contains(self, string):
        result = string.lower() in self._text.lower()
        if result:
            result_text = "contains"
        else:
            result_text = "does not contain"
        self._mail.processor.log_debug(
            "... Header \"{0}\" {1} {2}".format(
                self._name, result_text, ascii(string)))
        return result

    def matches(self, regexp):
        result = re.search(
            regexp, self._text, re.IGNORECASE | re.MULTILINE | re.UNICODE)
        if result:
            result_text = "matches"
        else:
            result_text = "does not match"
        self._mail.processor.log_debug(
            "... Header \"{0}\" {1} {2}".format(
                self._name, result_text, ascii(regexp)))
        return result
