import django
from django.core.mail import EmailMessage
from django.core.management.base import BaseCommand

from lib.scrape_hcd_lib import run_scrape_hcd


class Command(BaseCommand):
    help = "Scrape HCD housing element compliance data and save it to Airtable. Intended to run nightly."

    def add_arguments(self, parser: django.core.management.base.CommandParser) -> None:
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Get all the data but print it to the console instead of updating Airtable.",
        )
        parser.add_argument(
            "--try_exception",
            action="store_true",
            help="Instead of doing something useful, raise an exception to make sure we get alerted.",
        )
        super().add_arguments(parser)

    def handle(self, dry_run, try_exception, *args, **kwargs) -> None:
        if dry_run:
            print("Dry run: not updating Airtable.")
        if try_exception:
            raise Exception("This is a test exception in scrape_hcd.py")
        run_scrape_hcd(dry_run)

        ## Dummy email message sending example... adjust to your needs
        email = EmailMessage(
            subject="Mail sent from Django",
            body="Sent this email from Django, using Mailersend under the hood!",
            from_email="nils@home3.co",
            to=["founders@home3.co"],
            cc=[],
            bcc=[],
        )
        # email.send()      ## uncomment to make the email actually send
