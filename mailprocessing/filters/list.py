import re

class ListFilter:
    def __init__(self, list_substring, **kwargs):
      self.list_substring = list_substring

      self.folder_prefix = kwargs.get('folder_prefix', [self.list_substring])
      self.only_seen = kwargs.get('only_seen', True)
      self.archive_all_on = kwargs.get('archive_all_on', [])
      self.year_subfolder = kwargs.get('year_subfolder', False)
      self.month_subfolder = kwargs.get('month_subfolder', False)
      self.retain_keywords = kwargs.get('retain_keywords', [])
      self.strict_match = kwargs.get('strict_match', True)


    def listid_listname(self, mail):
       m = re.search("<(.*)>", '%s' % mail['List-Id'])
       return m.group(1).split('.')[0]


    def should_archive(self, mail):
        # Read email is always archived
        if mail.is_seen():
            return True

        # Never archive unread emails with subjects of interest.
        for keyword in self.retain_keywords:
            if mail['Subject'].contains(keyword):
                return False

        # If this is set, we will archive all email on all lists, regardless of
        # whether it is unread or not.
        if self.only_seen is False:
            return True

        # Archive all email from lists mentioned in archive_all_on
        for listname in self.archive_all_on:
            if mail.strict_mailing_list(listname):
                return True


    def filter(self, mail):
        # Only process mailing list emails.
        if self.strict_match is True:
            if not mail.strict_mailing_list(self.list_substring):
                return
        else:
            if not mail.from_mailing_list(self.list_substring):
                return

        try:
            listname = self.listid_listname(mail)
        except AttributeError:
            # This may happen when the regex for matching the list name does not
            # work properly. In this case we play it safe, log the headers and skip
            # the email in question.
            mail.processor.log_error("ERROR: Could not determine mailing list for email. Relevant headers follow.")
            try:
               for header in ['From', 'To', 'Subject', 'Message-ID', 'List-Id']:
                   mail.processor.log_error("%s: %s", header, mail[header])
            except AttributeError:
                # Just in case we encounter an email with missing headers.
                pass
            mail.processor.log_error("ERROR: list processing for the above email has been skipped.")
            return

        if self.should_archive(mail):
            prefix = self.folder_prefix + [self.listid_listname(mail)]
            mail.archive(max_days=0,
                         folder_prefix=prefix,
                         year_subfolder=self.year_subfolder,
                         month_subfolder=self.month_subfolder,
                         move_unread=True)
