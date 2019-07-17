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


class MailTarget(object):
    _target_headers = ["to", "cc"]

    def __init__(self, mail):
        self._mail = mail

    def contains(self, string):
        result = self._helper("contains", string)
        if result:
            result_text = "contains"
        else:
            result_text = "does not contain"
        self._mail.processor.log_debug(
            "... Target {0} {1}".format(result_text, ascii(string)))
        return result

    def matches(self, regexp):
        result = self._helper("matches", regexp)
        if result:
            result_text = "matches"
        else:
            result_text = "does not match"
        self._mail.processor.log_debug(
            "... Target {0} {1}".format(result_text, ascii(regexp)))
        return result

    # ----------------------------------------------------------------

    def _helper(self, method_name, arg):
        for header in self._target_headers:
            m = getattr(self._mail[header], method_name)
            if m(arg):
                return True
        return False
