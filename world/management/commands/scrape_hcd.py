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
        changeSummary = run_scrape_hcd(dry_run)
        
        email_subs_raw = env("HCD_EMAIL_SUBS")
        email_subs = email_subs_raw.split(",")

        if not dry_run:
            email = EmailMessage(
                subject="HCD daily update summary",
                body=changeSummary,
                from_email="marcio@home3.co",
                to=[email_subs],
                cc=[],
                bcc=[],
            )
            email.send()
        else:
            print("DRY RUN: NOT SENDING TO LIST:" + ",".join(email_subs))
            
        email = EmailMessage(
            subject="HCD daily update summary (admin)" + (" (dry run)" if dry_run else ""),
            body="Sent to " + ",".join(email_subs) + "\n\n" + changeSummary,
            from_email="marcio@home3.co",
            to=["marcio@home3.co"] if dry_run else "founders@home3.co",
            cc=[],
            bcc=[],
        )
        email.send() 
