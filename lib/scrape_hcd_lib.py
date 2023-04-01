import json
import logging
import re
import string
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pprint import pformat, pprint
from typing import Any, TypeVar, cast

from pyairtable import Table
from pyairtable.utils import date_to_iso_str
from pydantic import BaseModel
from requests import HTTPError

from lib.power_bi import BIRow, BITable, PowerBIScraper, SelectColumns, WhereCondition
from mygeo.settings import env

log = logging.getLogger(__name__)


def date_to_iso_str_safe(date: datetime | None) -> str | None:
    return date_to_iso_str(date) if date else None


JAN_1_2023 = datetime(2023, 1, 1, tzinfo=UTC)


# Scrape HCD data from HCD website, and dump it into these AirTables:

# AIRTABLES
#   Base: he_status_bot  - owned by Yimby Law
#       Tables are dashboardSync and underReview
#       https://airtable.com/app9boMvblYpDS3Du/tblAUo4gVNmcESrUV/viwAZtEwucQQomLw6?blocks=hide
#       API key is AIRTABLE_API_KEY
#       Used internally by Home3.
#   Base: yimby_law_housing_elements
#       Table is Cities
#       View is Website View HE Status
#       https://airtable.com/appRD2z3VXs78iq80/tblptIMb2VnnFotnm/viwH5W5SQCJC08pTm?blocks=bip4r67brjWReva5n
#       API key is AIRTABLE_YIMBY_LAW_HE_API_KEY
#       Used at fairhousingelements.org/he-status, and used by YIMBY law internally
#       We update HE Compliance field either from HCD or from the manual HE Compliance Override field if populated.


################################################
# Connect to Airtable
################################################


@dataclass
class AirtableBase:
    base_id: str
    api_key: str
    table_names: list
    tables: dict = field(default_factory=lambda: {})
    view_name: str | None = None

    def __post_init__(self) -> None:  # noqa: ANN101
        # Add the Airtable Table objects for each listed table
        self.tables = {
            table_name: Table(self.api_key, self.base_id, table_name) if self.api_key else None
            for table_name in self.table_names
        }
        if not self.api_key:
            print("** WARNING: No API key for Airtable base " + self.base_id + ", skipping **")


@dataclass
class AirtableBases:
    yimby_law_housing_elements: AirtableBase
    he_status_bot: AirtableBase


airtable_bases = AirtableBases(
    he_status_bot=AirtableBase(
        base_id="app9boMvblYpDS3Du",
        # TODO: Rename environnment var here, in settings.py, and in deployments to AIRTABLE_HE_STATUS_BOT_API_KEY
        api_key=env("AIRTABLE_API_KEY"),
        table_names=["dashboardSync", "underReview", "scrapeLog"],
        tables={},
    ),
    yimby_law_housing_elements=AirtableBase(
        base_id="appRD2z3VXs78iq80",
        api_key=env("AIRTABLE_YIMBY_LAW_HE_API_KEY"),
        table_names=["HCD Cities", "HCD HE Status Sync"],
        tables={},
        view_name="Website View HE Status",
    ),
)


def diff_he_statuses(hcd_status_table: BITable, airtable_status_raw: list, dry_run: bool) -> list[str]:
    # Determine the difference between the HCD status table and the Airtable "he_status_bot" base dashboardSync table.

    # {} in lines below are 'set' comprehensions
    hcd_jurisdictions = {string.capwords(cast(str, x[0])) for x in hcd_status_table.rows}
    airtable_jurisdictions = {string.capwords(x["fields"]["jurisdiction"]) for x in airtable_status_raw}
    # ensure no jurisdiction is listed twice (eg the set didn't remove any dupes)
    assert len(hcd_jurisdictions) == len(hcd_status_table.rows)
    assert len(airtable_jurisdictions) == len(airtable_status_raw)
    juris_in_both_sets = hcd_jurisdictions & airtable_jurisdictions
    juris_in_airtable_only = airtable_jurisdictions - hcd_jurisdictions
    juris_in_hcd_only = hcd_jurisdictions - airtable_jurisdictions
    airtable_element_status_table = airtable_bases.he_status_bot.tables["dashboardSync"]
    # didn't build out adding new jurisdictions to Airtable yet... but this should be v rare!
    assert len(juris_in_airtable_only) == 0
    assert len(juris_in_hcd_only) == 0
    assert hcd_status_table.column_names == ["Jurisdiction", "5th Cycle", "6th Cycle"]

    status_diff = []
    for juri in juris_in_both_sets:
        hcd_row = next(row for row in hcd_status_table.rows if string.capwords(cast(str, row[0])) == juri)
        airtable_row = next(
            row for row in airtable_status_raw if string.capwords(row["fields"]["jurisdiction"]) == juri
        )
        old_status = airtable_row["fields"]["6thCycle"]
        new_status = str(hcd_row[2])
        if old_status != new_status:
            status_diff.append(juri + " | From **" + old_status + "** to **" + new_status + "**")
            if not dry_run:
                airtable_element_status_table.update(airtable_row["id"], {"6thCycle": new_status})
            else:
                print("Dry run: elementStatus " + airtable_row["id"] + " to " + new_status)
    pprint(status_diff)
    return status_diff


class HEReviewDiffs(BaseModel):
    new_reviews: list[str]
    exited_reviews: list[str]
    messages: list[str]


def latest_received_review(hcd_review_table: BITable, cycle_name: str, min_date: datetime) -> BITable:
    # get the latest received review for each jurisdiction from the data pulled from HCD
    hcd_latest_cycle_table = sorted(
        [row for row in hcd_review_table.rows if row["CYCLE"] == cycle_name and row["RECEIVED_DATE"] >= min_date],
        key=lambda r: r["RECEIVED_DATE"],  # sort by received date (index 3 in row)
        reverse=True,  # most recent first so that we can just take the first one below.
    )
    # hcd_6th_cycle_latest: list[BIRow] = []
    hcd_6th_cycle_latest: BITable = BITable(column_names=hcd_review_table.column_names, index_col=0)
    seen_juris = set()
    for row in hcd_latest_cycle_table:
        if row["JURISDICTION"] not in seen_juris:
            hcd_6th_cycle_latest.add_row(row)
            seen_juris.add(row["JURISDICTION"])
    return hcd_6th_cycle_latest


def diff_6th_cycle_he_reviews(hcd_review_table: BITable, airtable_review_raw: list, dry_run: bool) -> HEReviewDiffs:
    airtable_review_table = airtable_bases.he_status_bot.tables["underReview"]
    messages = []

    hcd_latest_6th_reviews: BITable = latest_received_review(hcd_review_table, "6th Cycle", JAN_1_2023)

    hcd_jurisdictions = {string.capwords(cast(str, bi_row["JURISDICTION"])) for bi_row in hcd_latest_6th_reviews.rows}
    airtable_jurisdictions = {string.capwords(x["fields"]["jurisdiction"]) for x in airtable_review_raw}
    # ensure no jurisdiction is listed twice (eg the set didn't remove any dupes)
    assert len(hcd_jurisdictions) == len(hcd_latest_6th_reviews.rows)
    assert len(airtable_jurisdictions) == len(airtable_review_raw)
    juris_in_airtable_only = airtable_jurisdictions - hcd_jurisdictions

    # we expect jurisdictions to exist in airtable only after we've added them via HCD data.
    assert len(juris_in_airtable_only) == 0
    exited_reviews = []
    new_reviews = []
    # Use IN REVIEW status to determine if a jurisdiction is in review or not
    for juri in hcd_jurisdictions:
        hcd_row = next(row for row in hcd_latest_6th_reviews.rows if string.capwords(row["JURISDICTION"]) == juri)
        airtable_row = (
            next(row for row in airtable_review_raw if string.capwords(row["fields"]["jurisdiction"]) == juri)
            if juri in airtable_jurisdictions
            else None
        )
        review_status = hcd_row["REVIEW_STATUS"]
        rx_date: str = date_to_iso_str_safe(hcd_row["RECEIVED_DATE"])
        adopted_date: str = date_to_iso_str_safe(hcd_row["ADOPTED_DATE"])  # noqa: F841
        due_date: str = date_to_iso_str_safe(hcd_row["FINAL_DUE_DATE"])

        if review_status == "IN REVIEW" and airtable_row:
            # jurisdiction is in review, and it's already in airtable. Check for changes.
            if (
                hcd_row["TYPE"] != airtable_row["fields"]["type"]
                or rx_date != airtable_row["fields"]["receivedDate"]
                or due_date != airtable_row["fields"]["finalDueDate"]
            ):
                if due_date == "2023-03-30" and airtable_row["fields"]["finalDueDate"] == "2023-03-31":
                    # this is a hack because I think we fixed something in datetime conversion, so we're getting
                    # some false alarms. it should be removable after running once since we still update airtable.
                    print("not creating message for this special case (due date is 3/30 in HCD but 3/31 in airtable)")
                else:
                    messages.append(
                        f"Jurisdiction {juri} in review has changed in HCD dashboard. "
                        f"(Type | Received date | Final due date)"
                        f"\n  Old: {airtable_row['fields']['type']} | {airtable_row['fields']['receivedDate']} "
                        f"| {airtable_row['fields']['finalDueDate']}"
                        f"\n  New: {hcd_row['TYPE']} | {rx_date} | {due_date}"
                    )
                if not dry_run:
                    airtable_review_table.update(
                        airtable_row["id"],
                        {
                            "type": hcd_row["TYPE"],
                            "receivedDate": rx_date,
                            "finalDueDate": due_date,
                        },
                    )
        elif review_status == "IN REVIEW" and not airtable_row:
            # jurisdiction is newly in review
            new_reviews.append(
                f"{juri} | type: {hcd_row['TYPE']} | " f"received date: {rx_date} " f"| final due date: {due_date}"
            )
            n = {
                "jurisdiction": juri,
                "type": hcd_row["TYPE"],
                "receivedDate": rx_date,
                "finalDueDate": due_date,
            }
            if not dry_run:
                airtable_review_table.create(n)
            else:
                print("Dry run: reviewTable.create(" + json.dumps(n) + ")")

        elif review_status != "IN REVIEW" and airtable_row:
            # jurisdiction has exited review
            of = airtable_row["fields"]
            exited_reviews.append(
                f'{juri} | type: {of["type"]} | received date: {of["receivedDate"]} '
                f'| final due date: {of["finalDueDate"]}'
            )
            if not dry_run:
                airtable_review_table.delete(airtable_row["id"])
            else:
                print(f"Dry run: reviewTable.delete({airtable_row['id']})")

        elif review_status != "IN REVIEW" and not airtable_row:
            # jurisdiction isn't in review at all - nothing to do
            pass
        else:
            raise ValueError("This shouldn't happen")

    # breakpoint()
    return HEReviewDiffs(new_reviews=new_reviews, exited_reviews=exited_reviews, messages=messages)


def airtable_by_juri(airtable_raw: list) -> dict[str, Any]:
    # create a dict of jurisdiction to airtable row
    table_by_juri = {}
    error_count = 0
    for row in airtable_raw:
        juri = row["fields"].get("Jurisdiction", None)
        if juri:
            table_by_juri[juri] = row
        else:
            print("No Jurisdiction for row in airtable:", row)
            error_count += 1
    assert len(table_by_juri) == len(airtable_raw) - error_count, "Duplicate jurisdictions in Yimby Law Airtable"

    return table_by_juri


Column = TypeVar("Column")


def upper_strings(cols: list[Column]) -> list[Column]:
    return [x.upper() if isinstance(x, str) else x for x in cols]


def prepare_he_status_sync_airtable_record(
    hcd_status_table: BITable, hcd_review_table: BITable, juri: str
) -> dict[str, list[str]]:
    hcd_status_row: BIRow = hcd_status_table.row_dict[string.capwords(juri)]
    new_record = dict(zip(hcd_status_table.column_names, upper_strings(hcd_status_row.data), strict=True))
    hcd_latest_6th_reviews: BITable = latest_received_review(hcd_review_table, "6th Cycle", JAN_1_2023)

    if juri.upper() in hcd_latest_6th_reviews.row_dict:
        hcd_review_row: BIRow = hcd_latest_6th_reviews.row_dict[juri.upper()]
        # change column names underscores to spaces and replace with title case
        review_col_names = [string.capwords(x.replace("_", " ")) for x in hcd_review_table.column_names]
        new_record_pt2 = dict(zip(review_col_names, upper_strings(hcd_review_row.data), strict=True))
        new_record |= new_record_pt2
    # Iterate over this record's fields, adjusting their format for writing to Airtable.
    for k, v in new_record.items():
        # Convert datetimes to string
        if isinstance(v, datetime):
            new_record[k] = v.isoformat()
        # Create lists for multi-select fields (e.g. 6th Cycle)
        if k in ["6th Cycle"]:
            new_record[k] = re.split(r",\s*", v)
    return new_record


def sync_he_status_to_yimby_law_table(hcd_status_table: BITable, hcd_review_table: BITable) -> None:
    # Sync data from HCD (both status table and review table) to a Yimby Law Airtable table that we control.
    # Note that we write to this table even with a --dry-run flag, since this table just reflects the latest state.

    # table that WE control and directly write into:
    yimby_law_he_status_sync_airtable = airtable_bases.yimby_law_housing_elements.tables["HCD HE Status Sync"]

    airtable_records = yimby_law_he_status_sync_airtable.all()
    # ids = [r["id"] for r in airtable_records]
    # print("Deleting", len(ids), "records from HCD HE Status Sync table")
    # yimby_law_he_status_sync_airtable.batch_delete(ids)
    print("Syncing HCD tableso YIMBY Law Housing Elements 'HCD HE Status Sync' table")
    # Update airtable entries that already exist with new HCD data.
    processed_juris = set()
    for idx, record in enumerate(airtable_records):
        juri = record["fields"]["Jurisdiction"]
        if idx % 20 == 0:
            print(f"Updating {idx} of {len(airtable_records)} entries (currently on {juri})")
        if string.capwords(juri) in hcd_status_table.row_dict:
            new_record = prepare_he_status_sync_airtable_record(hcd_status_table, hcd_review_table, juri)
            try:
                yimby_law_he_status_sync_airtable.update(record["id"], new_record, replace=True)
            except HTTPError as e:
                if e.response.headers.get("Content-Type").startswith("application/json"):
                    log.error(f"Error updating {juri} in Airtable: {e.response.json()}")
                    log.error(f"Record: {pformat(new_record)}")
                    raise RuntimeError(f"Error updating {juri} in Airtable: {e.response.json()}") from e
                raise e
            processed_juris.add(juri)
        else:
            print(f"No HCD status row for {juri}; deleting airtable record")
            yimby_law_he_status_sync_airtable.delete(record["id"])
    # Add new jurisdictions we found from HCD that don't exist in airtable yet.
    for juri in hcd_status_table.row_dict:
        if juri.upper() in processed_juris:
            continue
        print(f"Adding new record for {juri} to Airtable... was missing before")
        new_record = prepare_he_status_sync_airtable_record(hcd_status_table, hcd_review_table, juri)
        yimby_law_he_status_sync_airtable.create(new_record)


def diff_yimby_law_housing_elements(hcd_status_table: BITable, dry_run: bool) -> list[str]:
    # Compare fetched HCD data with Yimby Law Airtable data. Update Airtable's HE Compliance field if needed.

    # Yimby Law's table that is used to update fairhousingelements.org and other places.
    yimby_law_airtable = airtable_bases.yimby_law_housing_elements.tables["HCD Cities"].all()

    yl_airtable_by_juri = airtable_by_juri(yimby_law_airtable)
    hcd_jurisdictions = {string.capwords(cast(str, x[0])) for x in hcd_status_table.rows}
    airtable_jurisdictions = {string.capwords(x) for x in yl_airtable_by_juri.keys()}

    juris_in_both_sets = hcd_jurisdictions & airtable_jurisdictions
    juris_in_airtable_only = airtable_jurisdictions - hcd_jurisdictions
    juris_in_hcd_only = hcd_jurisdictions - airtable_jurisdictions

    print("# of matched jurisdictions:", len(juris_in_both_sets))
    print("jurisdictions in airtable only:", juris_in_airtable_only)
    print("jurisdictions in hcd only:", juris_in_hcd_only)
    assert hcd_status_table.column_names == ["Jurisdiction", "5th Cycle", "6th Cycle"]
    changes = []
    # Find changes in 6th cycle HE compliance status between HCD dashboard (the master) and Yimby Law Airtable.
    for juri in juris_in_both_sets:
        hcd_row = next(row for row in hcd_status_table.rows if string.capwords(cast(str, row[0])) == juri)
        airtable_row = yl_airtable_by_juri[juri.upper()]
        # Assumption: Airtable's "HE Compliance" field is always referring to 6th cycle.
        airtable_6cycle_status: list[str] = [
            x.upper() for x in airtable_row["fields"].get("HE Compliance Home3", "N/A")
        ]
        # 6th cycle status is a multi-select field in Airtable, so we need to split it into a list.
        hcd_6cycle_status: list[str] = re.split(r",\s*", str(hcd_row["6th Cycle"]).upper())
        if hcd_6cycle_status != airtable_6cycle_status:
            changes.append(
                juri
                + " | From **"
                + ",".join(airtable_6cycle_status)
                + "** to **"
                + ",".join(hcd_6cycle_status)
                + "**"
            )
            if dry_run:
                print(
                    f"Dry run: Change YIMBY Law HE Airtable 6th cycle compliance for juri {juri}"
                    f" from {airtable_6cycle_status} to {hcd_6cycle_status}"
                )
            else:
                try:
                    airtable_bases.yimby_law_housing_elements.tables["HCD Cities"].update(
                        airtable_row["id"],
                        {"HE Compliance Home3": hcd_6cycle_status},
                    )
                except HTTPError as e:
                    if e.response.headers.get("Content-Type").startswith("application/json"):
                        log.error(f"Error updating {juri} in Airtable: {e.response.json()}")
                        log.error(f"Record: {pformat({'HE Compliance Home3': hcd_6cycle_status})}")
                        raise RuntimeError(f"Error updating {juri} in Airtable: {e.response.json()}") from e
                    raise e

    return changes


def run_scrape_hcd(dry_run: bool = False) -> str:
    # Scrape the HCD website
    # big 12-page BI dashboard
    page_url = (
        "https://www.hcd.ca.gov/planning-and-community-development/housing-open-data-tools/"
        "housing-element-implementation-and-apr-dashboard"
    )
    # smaller 3-page BI dashboard with similar data (but not exactly the same formatting):
    # page_url = "https://www.hcd.ca.gov/planning-and-community-development/housing-open-data-tools/" \
    # "housing-element-review-and-compliance-report"

    # Check that we have API keys for the HCD BI dashboard
    assert airtable_bases.he_status_bot.api_key is not None
    assert airtable_bases.yimby_law_housing_elements.api_key is not None

    hcd_page_scraper = PowerBIScraper(page_url)

    # Useful information fetched from the server: list of sections, tables, and columns:
    sections = hcd_page_scraper.list_sections()  # noqa: F841
    tables = hcd_page_scraper.list_tables()  # noqa: F841
    review_table_cols = hcd_page_scraper.list_columns("Under Review")  # noqa: F841
    status_table_cols = hcd_page_scraper.list_columns("HE_Compliance")  # noqa: F841

    # Fetch "Under Review" table:
    select_columns = SelectColumns(
        [
            "JURISDICTION",
            "CYCLE",
            "TYPE",
            "RECEIVED_DATE",
            "REVIEWED_DATE",
            "REVIEW_STATUS",
            "FINAL_DUE_DATE",
            "ADOPTED_DATE",
            "COMPLIANCE_STATUS",
        ]
    )
    # Query filter: Each WhereCondition must be true (AND). Inside a WhereCondition, any one of the values will
    # match (OR)
    conditions = [
        WhereCondition(column_name="CYCLE", values=["5th Cycle", "6th Cycle"]),
        WhereCondition(column_name="TYPE", values=["ADOPTED", "SUBSEQUENT DRAFT", "DRAFT", "INITIAL DRAFT"]),
    ]
    hcd_review_table = hcd_page_scraper.fetch_table(
        "Under Review", columns=select_columns, index_col=0, conditions=conditions
    )

    # Fetch "HE Compliance" status table. The column naming isn't consistent between tables, likely due to
    #  inconsistency at HCD.
    select_columns = SelectColumns(["Jurisdiction", "5th Cycle", "6th Cycle"])
    hcd_status_table = hcd_page_scraper.fetch_table(
        "HE_Compliance", columns=select_columns, index_col=0, conditions=[]
    )

    # fetch he_status_bot Airtables
    airtable_status_raw = airtable_bases.he_status_bot.tables["dashboardSync"].all()
    airtable_review_raw = airtable_bases.he_status_bot.tables["underReview"].all()

    ############
    # diff Airtables and scraped data
    ############

    status_diff = diff_he_statuses(hcd_status_table, airtable_status_raw, dry_run)
    review_diff = diff_6th_cycle_he_reviews(hcd_review_table, airtable_review_raw, dry_run)
    yl_he_diff = diff_yimby_law_housing_elements(hcd_status_table, dry_run)

    # Sync HCD status to Yimby Law's airtable
    sync_he_status_to_yimby_law_table(hcd_status_table, hcd_review_table)

    ############
    # store changes in runLog
    ############
    change_summary = ""
    if status_diff:
        change_summary += "\n*Jurisdiction(s) with new 6th Cycle status:*\n" + "\n".join(status_diff)

    if review_diff.new_reviews:
        change_summary += "\n\n*Jurisdiction(s) newly IN review:*\n" + "\n".join(review_diff.new_reviews)

    if review_diff.exited_reviews:
        change_summary += "\n\n*Jurisdiction(s) OUT of review:*\n" + "\n".join(review_diff.exited_reviews)

    if review_diff.messages:
        change_summary += "\n\n*Jurisdiction(s) in review with a change::*\n" + "\n".join(review_diff.messages)

    if yl_he_diff:
        change_summary += "\n\n*Jurisdiction(s) with new YIMBY Law Housing Elements table status:*\n" + "\n".join(
            yl_he_diff
        )

    if not change_summary:
        change_summary = "No changes detected."

    run_time = datetime.now(UTC).strftime("%m/%d/%y %H:%M:%S")
    if not dry_run:
        airtable_log_table = airtable_bases.he_status_bot.tables["scrapeLog"]
        airtable_log_table.create({"runTime": run_time, "differences": change_summary})
    else:
        print("Dry run: logTable.create(" + run_time + ", " + change_summary)

    return change_summary
