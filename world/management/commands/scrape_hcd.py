import django
from django.core.mail import EmailMessage
from django.core.management.base import BaseCommand

from lib.scrape_hcd_lib import run_scrape_hcd
from mygeo.settings import env


class Command(BaseCommand):
    help = "Scrape HCD housing element compliance data and save it to Airtable. Intended to run nightly."

    def add_arguments(self, parser: django.core.management.base.CommandParser) -> None:
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Get all the data but print it to the console instead of updating Airtable.",
        )
        parser.add_argument(
            "--no-emails",
            action="store_true",
            help="Skip emailing.",
        )
        parser.add_argument(
            "--try-exception",
            action="store_true",
            help="Instead of doing something useful, raise an exception to make sure we get alerted.",
        )
        super().add_arguments(parser)

    def handle(self, dry_run, no_emails, try_exception, *args, **kwargs) -> None:
        if dry_run:
            print("Dry run: not updating Airtable.")
        if try_exception:
            raise Exception("This is a test exception in scrape_hcd.py")
        changeSummary = run_scrape_hcd(dry_run)
        # change line endings to crlf to comply with email standards -- some email clients don't show
        # linebreaks otherwise.
        changeSummaryCrLf = "\r\n".join(changeSummary.splitlines(False))
        email_subs_raw = env("HCD_EMAIL_SUBS")
        email_subs = email_subs_raw.split(",")

        send_emails = not no_emails
        mail_exc = ""
        if not dry_run and send_emails:
            try:
                email = EmailMessage(
                    subject="HCD daily update summary",
                    body=changeSummaryCrLf,
                    from_email="marcio@home3.co",
                    to=["marcio@home3.co"],
                    cc=[],
                    bcc=email_subs,
                )
                email.send()
            except Exception as e:
                print("Exception sending email: " + str(e))
                mail_exc = str(e)
                # change line breaks on exception
                mail_exc = "\r\n\r\n*EXCEPTION DURING SEND*:\r\n" + "\r\n".join(mail_exc.splitlines(False))
        else:
            print("SKIPPING EMAILS: NOT SENDING TO LIST:" + ",".join(email_subs))
        if send_emails:
            email = EmailMessage(
                subject="HCD daily update summary (admin)"
                + (" (dry run)" if dry_run else "")
                + (" (FAILED)" if mail_exc else ""),
                body="Sent to " + ",".join(email_subs) + "\r\n\r\n" + changeSummaryCrLf + mail_exc,
                from_email="marcio@home3.co",
                to=["marcio@home3.co"] if dry_run else ["founders@home3.co"],
                cc=[],
                bcc=[],
            )
            email.send()
