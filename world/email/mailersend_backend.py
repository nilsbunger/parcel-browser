from typing import List

import django
from django.core.mail.backends.base import BaseEmailBackend
from mailersend import emails

from mygeo.settings import env

## Backend for sending email.
## Example of how to send an email:
#  email = EmailMessage(
#             subject="Mail sent from Django",
#             body="Sent this email from Django, using Mailersend under the hood!",
#             from_email="nils@home3.co",
#             to=["founders@home3.co"],
#             cc=[],
#             bcc=[],
#  )
#  email.send()


class MailerSendBackend(BaseEmailBackend):
    def __init__(self, fail_silently: bool = False, **kwargs: object) -> None:
        self.api_key = env("MAILERSEND_API_KEY")
        super().__init__(fail_silently, **kwargs)

    def send_messages(self, email_messages: List[django.core.mail.message.EmailMessage]) -> str:

        mailer = emails.NewEmail(mailersend_api_key=self.api_key)
        assert len(email_messages) == 1, "We only support sending one email at a time at the moment"
        email_message = email_messages[0]
        assert len(email_message.cc) == 0, "We don't support cc at the moment"
        assert len(email_message.bcc) == 0, "We don't support bcc at the moment"
        mail_body = {}  # dict in which mail content gets stored by next lines
        mailer.set_mail_from({"name": email_message.from_email, "email": email_message.from_email}, mail_body)
        mailer_to_list = [{"name": to_item, "email": to_item} for to_item in email_message.to]
        mailer.set_mail_to(mailer_to_list, mail_body)
        mailer.set_subject(email_message.subject, mail_body)
        mailer.set_plaintext_content(email_message.body, mail_body)
        # TODO: Support HTML content
        resp = mailer.send(mail_body)
        code, messages = resp.split("\n")
        if int(code) > 299:
            raise Exception(messages)
        print("Sent email to", email_message.to)
        return resp
