from dataclasses import dataclass, field
import datetime
from datetime import timezone
import json
from pprint import pprint
import re
import string
from typing import Optional, cast

from pyairtable import Table
from pyairtable.utils import date_to_iso_str
from pydantic import BaseModel

from lib.power_bi import BITable, PowerBIScraper, WhereCondition
from mygeo.settings import env


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
    view_name: Optional[str] = None

    def __post_init__(self) -> None:
        # Add the Airtable Table objects for each listed table
        self.tables = {
            table_name: Table(self.api_key, self.base_id, table_name) if self.api_key else None
            for table_name in self.table_names
        }
        if not self.api_key:
            print("No API key for Airtable base " + self.base_id + ", skipping")


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
        tables=dict(),
    ),
    yimby_law_housing_elements=AirtableBase(
        base_id="appRD2z3VXs78iq80",
        api_key=env("AIRTABLE_YIMBY_LAW_HE_API_KEY"),
        table_names=["HCD Cities", "HCD HE Status Sync"],
        tables=dict(),
        view_name="Website View HE Status",
    ),
)


def diff_he_statuses(hcd_status_table, airtable_status_raw, dry_run) -> list[str]:
    # Determine the difference between the HCD status table and the Airtable "he_status_bot" base dashboardSync table.

    hcd_jurisdictions = set([string.capwords(cast(str, x[0])) for x in hcd_status_table.rows])
    airtable_jurisdictions = set([string.capwords(x["fields"]["jurisdiction"]) for x in airtable_status_raw])
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
        hcd_row = next((row for row in hcd_status_table.rows if string.capwords(cast(str, row[0])) == juri))
        airtable_row = next(
            (row for row in airtable_status_raw if string.capwords(row["fields"]["jurisdiction"]) == juri)
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


def latest_received_review(hcd_review_table: BITable, cycle_name: str, min_date: datetime):
    # get the latest received review for each jurisdiction from the data pulled from HCD
    hcd_6th_cycle_table = sorted(
        [row for row in hcd_review_table.rows if row[1] == cycle_name and cast(datetime, row[3]) >= min_date],
        key=lambda x: x[3],  # sort by received date (index 3 in row)
        reverse=True,  # most recent first
    )
    hcd_6th_cycle_latest = []
    seen_juris = set()
    for row in hcd_6th_cycle_table:
        if row[0] not in seen_juris:
            hcd_6th_cycle_latest.append(row)
            seen_juris.add(row[0])
    return hcd_6th_cycle_latest


def diff_he_reviews(hcd_review_table: BITable, airtable_review_raw, dry_run) -> HEReviewDiffs:
    airtable_review_table = airtable_bases.he_status_bot.tables["underReview"]
    messages = []

    jan_1_2023 = datetime.datetime(2023, 1, 1, tzinfo=datetime.timezone.utc)
    hcd_latest_6th_cycle_reviews = latest_received_review(hcd_review_table, "6th Cycle", jan_1_2023)

    hcd_jurisdictions = set([string.capwords(cast(str, x[0])) for x in hcd_latest_6th_cycle_reviews])
    airtable_jurisdictions = set([string.capwords(x["fields"]["jurisdiction"]) for x in airtable_review_raw])
    # ensure no jurisdiction is listed twice (eg the set didn't remove any dupes)
    assert len(hcd_jurisdictions) == len(hcd_latest_6th_cycle_reviews)
    assert len(airtable_jurisdictions) == len(airtable_review_raw)
    juris_in_both_sets = hcd_jurisdictions & airtable_jurisdictions
    juris_in_airtable_only = airtable_jurisdictions - hcd_jurisdictions
    juris_in_hcd_only = hcd_jurisdictions - airtable_jurisdictions

    # Remove items only found in airtable - they have exited review
    exited_reviews = []
    for juri in juris_in_airtable_only:
        oldItem = next(
            (row for row in airtable_review_raw if string.capwords(row["fields"]["jurisdiction"]) == juri)
        )
        of = oldItem["fields"]
        exited_reviews.append(
            f'{juri} | type: {of["type"]} | received date: {of["receivedDate"]} '
            f'| final due date: {of["finalDueDate"]}'
        )
        if not dry_run:
            airtable_review_table.delete(oldItem["id"])
        else:
            print("Dry run: reviewTable.delete(" + oldItem["id"] + ")")
    # Add new items being added to review (ones only found in HCD dashboard)
    new_reviews = []
    for juri in juris_in_hcd_only:
        hcd_row = next((row for row in hcd_latest_6th_cycle_reviews if string.capwords(cast(str, row[0])) == juri))
        new_reviews.append(
            f"{juri} | type: {hcd_row[2]} | received date: {hcd_row[3]} " f"| final due date: {hcd_row[4]}"
        )
        new_entry = {
            "jurisdiction": juri,
            "type": hcd_row[2],
            "receivedDate": date_to_iso_str(hcd_row[3]),
            "finalDueDate": date_to_iso_str(hcd_row[4]),
        }
        if not dry_run:
            airtable_review_table.create(new_entry)
        else:
            print("Dry run: reviewTable.create(" + json.dumps(new_entry) + ")")

    # Handle an update that exists in both sets. We don't expect any changes but we detect and report them.
    for juri in juris_in_both_sets:
        hcd_row = next((row for row in hcd_latest_6th_cycle_reviews if string.capwords(cast(str, row[0])) == juri))
        airtable_row = next(
            (row for row in airtable_review_raw if string.capwords(row["fields"]["jurisdiction"]) == juri)
        )
        if (
            hcd_row[2] != airtable_row["fields"]["type"]
            or hcd_row[3] != airtable_row["fields"]["receivedDate"]
            or hcd_row[4] != airtable_row["fields"]["finalDueDate"]
        ):
            messages.append(
                f"Jurisdiction {juri} in review has changed in HCD dashboard. "
                f"Old: {airtable_row['fields']} | New: {hcd_row}"
            )

    return HEReviewDiffs(new_reviews=new_reviews, exited_reviews=exited_reviews, messages=messages)


def airtable_by_juri(airtable_raw):
    # create a dict of jurisdiction to airtable row
    airtable_by_juri = dict()
    error_count = 0
    for row in airtable_raw:
        juri = row["fields"].get("Jurisdiction", None)
        if juri:
            airtable_by_juri[juri] = row
        else:
            print("No Jurisdiction for row in airtable:", row)
            error_count += 1
    assert (
        len(airtable_by_juri) == len(airtable_raw) - error_count
    ), "Duplicate jurisdictions in Yimby Law Airtable"

    return airtable_by_juri


def upper_strings(l: list):
    return [x.upper() if isinstance(x, str) else x for x in l]


def prepare_he_status_sync_airtable_record(hcd_status_table, hcd_review_table, juri):
    hcd_status_row = hcd_status_table.row_dict[string.capwords(juri)]
    new_record = dict(zip(hcd_status_table.column_names, upper_strings(hcd_status_row)))
    if juri.upper() in hcd_review_table.row_dict:
        hcd_review_row = hcd_review_table.row_dict[juri.upper()]
        # change column names underscores to spaces and replace with title case
        review_col_names = [string.capwords(x.replace("_", " ")) for x in hcd_review_table.column_names]
        new_record_pt2 = dict(zip(review_col_names, upper_strings(hcd_review_row)))
        new_record |= new_record_pt2
    # Iterate over this record's fields, adjusting their format for writing to Airtable.
    for k, v in new_record.items():
        # Convert datetimes to string
        if isinstance(v, datetime.datetime):
            new_record[k] = v.isoformat()
        # Create lists for multi-select fields (e.g. 6th Cycle)
        if k in ["6th Cycle"]:
            new_record[k] = re.split(r",\s*", v)
    return new_record


def sync_he_status_to_yimby_law_table(hcd_status_table: BITable, hcd_review_table: BITable, dry_run):
    # Sync data from HCD (both status table and review table) to a Yimby Law Airtable table that we control.

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
            yimby_law_he_status_sync_airtable.update(record["id"], new_record, replace=True)
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


def diff_yimby_law_housing_elements(hcd_status_table: BITable, hcd_review_table: BITable, dry_run):
    # Compare fetched HCD data with Yimby Law Airtable data. Update Airtable's HE Compliance field if needed.

    # Yimby Law's table that is used to update fairhousingelements.org and other places.
    yimby_law_airtable = airtable_bases.yimby_law_housing_elements.tables["HCD Cities"].all()

    yl_airtable_by_juri = airtable_by_juri(yimby_law_airtable)
    hcd_jurisdictions = set([string.capwords(cast(str, x[0])) for x in hcd_status_table.rows])
    airtable_jurisdictions = set([string.capwords(x) for x in yl_airtable_by_juri.keys()])

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
        hcd_row = next((row for row in hcd_status_table.rows if string.capwords(cast(str, row[0])) == juri))
        airtable_row = yl_airtable_by_juri[juri.upper()]
        # Assumption: Airtable's "HE Compliance" field is always referring to 6th cycle.
        airtable_6cycle_status = [x.upper() for x in airtable_row["fields"].get("HE Compliance Home3", "N/A")]
        hcd_6cycle_status = re.split(r",\s*", str(hcd_row[2]).upper())
        if hcd_6cycle_status != airtable_6cycle_status:
            changes.append(
                juri + " | From **" + ",".join(airtable_6cycle_status) + "** to **" + hcd_6cycle_status + "**"
            )
            if dry_run:
                print(
                    f"Dry run: Change YIMBY Law HE Airtable 6th cycle compliance for juri {juri}"
                    f" from {airtable_6cycle_status} to {hcd_6cycle_status}"
                )
            else:
                airtable_bases.yimby_law_housing_elements.tables["HCD Cities"].update(
                    airtable_row["id"],
                    {"HE Compliance Home3": hcd_6cycle_status},
                )
    return changes


def run_scrape_hcd(dry_run=False) -> str:
    # Scrape the HCD website
    # big 12-page BI dashboard
    page_url = "https://www.hcd.ca.gov/planning-and-community-development/housing-open-data-tools/housing-element-implementation-and-apr-dashboard"
    # smaller 3-page BI dashboard with similar data (but not exactly the same formatting):
    # page_url = "https://www.hcd.ca.gov/planning-and-community-development/housing-open-data-tools/housing-element-review-and-compliance-report"

    hcd_page_scraper = PowerBIScraper(page_url)

    # Useful information fetched from the server: list of sections, tables, and columns:
    sections = hcd_page_scraper.list_sections()
    tables = hcd_page_scraper.list_tables()
    review_table_cols = hcd_page_scraper.list_columns("Under Review")
    status_table_cols = hcd_page_scraper.list_columns("HE_Compliance")

    # Fetch "Under Review" table:
    select_columns = [
        "JURISDICTION",
        "CYCLE",
        "TYPE",
        "RECEIVED_DATE",
        "FINAL_DUE_DATE",
        "ADOPTED_DATE",
        "COMPLIANCE_STATUS",
    ]
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
    select_columns = ["Jurisdiction", "5th Cycle", "6th Cycle"]
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
    review_diff = diff_he_reviews(hcd_review_table, airtable_review_raw, dry_run)
    yl_he_diff = diff_yimby_law_housing_elements(hcd_status_table, hcd_review_table, dry_run)

    # Sync HCD status to Yimby Law's airtable
    sync_he_status_to_yimby_law_table(hcd_status_table, hcd_review_table, dry_run)

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

    if yl_he_diff:
        change_summary += "\n\n*Jurisdiction(s) with new YIMBY Law Housing Elements table status:*\n" + "\n".join(
            yl_he_diff
        )

    if change_summary == "":
        change_summary = "No changes detected."

    runTime = datetime.datetime.now(timezone.utc).strftime("%m/%d/%y %H:%M:%S")
    if not dry_run:
        airtable_log_table = airtable_bases.he_status_bot.tables["scrapeLog"]
        airtable_log_table.create({"runTime": runTime, "differences": change_summary})
    else:
        print("Dry run: logTable.create(" + runTime + ", " + change_summary)

    return change_summary
