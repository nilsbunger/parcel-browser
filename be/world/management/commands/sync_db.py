import logging
import sys
from enum import Enum

from django.core.paginator import Paginator
from django.db.models import DateField, DateTimeField
from lib.mgmt_lib import Home3Command
from parsnip.settings import LOCAL_DB

from world.models import (
    Parcel,
    PropertyListing,
    RentalData,
)
from world.models.models import AnalyzedParcel, AnalyzedRoad


class SyncCmd(Enum):
    cloud2local = 1
    local2cloud = 2


class Command(Home3Command):
    help = (
        "Sync tables from cloud to local to simplify local development: PropertyListing, AnalyzedListing, RentalData"
    )

    def add_arguments(self, parser):
        parser.add_argument("cmd", choices=SyncCmd.__members__)
        parser.add_argument("tables", nargs="*", help="Tables to sync (for local2cloud only")
        parser.add_argument("--verbose", action="store_true", help="Do verbose logging (DEBUG-level logging)")

    def handle(self, cmd, tables, *args, **options):
        logging.basicConfig(stream=sys.stdout, level=logging.DEBUG if options["verbose"] else logging.INFO)
        logging.getLogger().setLevel(logging.DEBUG if options["verbose"] else logging.INFO)
        logging.debug("DEBUG log level")
        logging.info("INFO log level")
        assert LOCAL_DB == 0
        if cmd == "cloud2local":
            self.handle_cloud2local(*args, **options)
        elif cmd == "local2cloud":
            self.handle_local2cloud(*args, **options)
        else:
            raise Exception(f"Unknown command {cmd}")

    def handle_local2cloud(self, *args, **options):
        for model in [AnalyzedParcel, AnalyzedRoad]:
            logging.info(f"{model}: Deleting all entries from CLOUD DB")
            model.objects.using("cloud_db").all().delete()
            logging.info(f"{model}: Getting all entries from LOCAL DB and writing to Cloud DB")
            items = model.objects.using("local_db").all()
            model.objects.using("cloud_db").bulk_create(items)
        logging.info("DONE migrating data")

    def handle_cloud2local(self, *args, **options):
        # Remove auto_now and auto_now_add so that dates move over correctly.
        logging.info("Eliminating pre-save hooks on dates")

        def pre_save_datefield(self, model_instance, add):
            return super(DateField, self).pre_save(model_instance, add)

        DateField.pre_save = pre_save_datefield

        def pre_save_datetimefield(self, model_instance, add):
            return super(DateTimeField, self).pre_save(model_instance, add)

        DateTimeField.pre_save = pre_save_datetimefield

        for model in [
            Parcel,
            PropertyListing,
            RentalData,
            # Other models we might want to sync if we're recreating a local parcel DB:
            # AnalyzedListing,
            # ZoningBase,
            # HousingSolutionArea,
            # TransitPriorityArea,
            # ZoningMapLabel,
            # TpaMapLabel,
            # BuildingOutlines,
            # AnalyzedParcel
        ]:
            logging.info(f"{model}: Deleting all entries from LOCAL DB")
            model.objects.using("local_db").all().delete()

            logging.info(f"{model}: Getting all entries from CLOUD DB and writing to Local DB")
            items = model.objects.using("cloud_db").all().order_by("pk")
            paged = Paginator(items, 1000)
            for page in paged.page_range:
                logging.info(f"{model}: Page {page} of {paged.num_pages}")
                page_items = paged.page(page).object_list
                model.objects.using("local_db").bulk_create(page_items)

            # # NOTE: many-to-many fields are NOT handled by bulk create; check for
            # # them and use the existing implicit through models to copy them
            # for m2mfield in model._meta.many_to_many:
            #     m2m_model = getattr(model, m2mfield.name).through
            #     batch_migrate(m2m_model)

        logging.info("DONE migrating data")
