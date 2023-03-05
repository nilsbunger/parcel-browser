import datetime
from datetime import timezone
from pprint import pprint
import string

from pyairtable import Table
from pydantic import BaseModel

from lib.power_bi import BITable, PowerBIScraper, WhereCondition
from mygeo.settings import env

# Scrape HCD data from HCD website, and dump it into this AirTable:
# https://airtable.com/app9boMvblYpDS3Du/tblAUo4gVNmcESrUV/viwAZtEwucQQomLw6?blocks=hide

################################################
# Connect to Airtable
################################################

tableID = "app9boMvblYpDS3Du"

tableName = "dashboardSync"
AIRTABLE_API_KEY = env("AIRTABLE_API_KEY")

airtable_element_status_table = Table(AIRTABLE_API_KEY, tableID, tableName)

reviewTableName = "underReview"
airtable_review_table = Table(AIRTABLE_API_KEY, tableID, reviewTableName)

logTableName = "scrapeLog"
airtable_log_table = Table(AIRTABLE_API_KEY, tableID, logTableName)


def diff_he_statuses(hcd_status_table, airtable_status_raw, dry_run) -> list[str]:
    hcd_jurisdictions = set([string.capwords(x[0]) for x in hcd_status_table.rows])
    airtable_jurisdictions = set([string.capwords(x["fields"]["jurisdiction"]) for x in airtable_status_raw])
    # ensure no jurisdiction is listed twice (eg the set didn't remove any dupes)
    assert len(hcd_jurisdictions) == len(hcd_status_table.rows)
    assert len(airtable_jurisdictions) == len(airtable_status_raw)
    juris_in_both_sets = hcd_jurisdictions & airtable_jurisdictions
    juris_in_airtable_only = airtable_jurisdictions - hcd_jurisdictions
    juris_in_hcd_only = hcd_jurisdictions - airtable_jurisdictions

    # didn't build out adding new jurisdictions to Airtable yet... but this should be v rare!
    assert len(juris_in_airtable_only) == 0
    assert len(juris_in_hcd_only) == 0
    assert hcd_status_table.column_names == ["Jurisdiction", "5th Cycle", "6th Cycle"]

    status_diff = []
    for juri in juris_in_both_sets:
        hcd_row = next((row for row in hcd_status_table.rows if string.capwords(row[0]) == juri))
        airtable_row = next(
            (row for row in airtable_status_raw if string.capwords(row["fields"]["jurisdiction"]) == juri)
        )
        old_status = airtable_row["fields"]["6thCycle"]
        new_status = hcd_row[2]
        if old_status != new_status:
            status_diff.append(juri + " | From **" + old_status + "** to **" + new_status + "**")
            if not dry_run:
                airtable_element_status_table.update(airtable_row["id"], {"6thCycle": new_status})
            else:
                print("Dry run: elementStatus " + airtable_row["id"] + " to " + new_status)
    pprint(status_diff)
    return status_diff
    # # 6th cycle status: any record difference means a status update for that jurisdiction
    # for x in tableRows:
    #     if x not in airtableStatusRecords:
    #         # find list element with dict key/value
    #         oldItem = list(
    #             filter(lambda y: y["fields"]["jurisdiction"] == x["jurisdiction"], airtable_status_raw)
    #         )[0]
    #         oldStatus = oldItem["fields"]["6thCycle"]
    #         statusDiff.append(x["jurisdiction"] + " | From **" + oldStatus + "** to **" + x["6thCycle"] + "**")
    #         if not dry_run:
    #             airtable_element_status_table.update(oldItem["id"], {"6thCycle": x["6thCycle"]})
    #         else:
    #             print("Dry run: elementStatus" + oldItem["id"] + " to " + x["6thCycle"])

    # under review: find jurisdictions that came in OR left review


class HEReviewDiffs(BaseModel):
    new_reviews: list[str]
    exited_reviews: list[str]


def latest_received_review(hcd_review_table, cycle_name, min_date):
    # get the latest received review for each jurisdiction from the data pulled from HCD
    hcd_6th_cycle_table = sorted(
        [row for row in hcd_review_table.rows if row[1] == cycle_name and row[3] >= min_date],
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
    airtableReviewRecords = [x["fields"] for x in airtable_review_raw]

    jan_1_2023 = datetime.datetime(2023, 1, 1, tzinfo=datetime.timezone.utc)
    hcd_latest_6th_cycle_reviews = latest_received_review(hcd_review_table, "6th Cycle", jan_1_2023)

    hcd_jurisdictions = set([string.capwords(x[0]) for x in hcd_latest_6th_cycle_reviews])
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
    #  Marcio's original implementation:
    # for x in airtableReviewRecords:
    #     if x not in reviewTableRows:
    #         exited_reviews.append(
    #             x["jurisdiction"]
    #             + " | type: "
    #             + x["type"]
    #             + " | received date: "
    #             + x["receivedDate"]
    #             + " | final due date: "
    #             + x["finalDueDate"]
    #         )
    #         oldItem = list(filter(lambda y: y["fields"]["jurisdiction"] == x["jurisdiction"], airtable_review_raw))[0]
    #         if not dry_run:
    #             airtable_review_table.delete(oldItem["id"])
    #         else:
    #             print("Dry run: reviewTable.delete(" + oldItem["id"] + ")")

    # Add new items being added to review
    new_reviews = []
    for juri in juris_in_hcd_only:
        hcd_row = next((row for row in hcd_latest_6th_cycle_reviews if string.capwords(row[0]) == juri))
        new_reviews.append(
            f"{juri} | type: {hcd_row[2]} | received date: {hcd_row[3]} " f"| final due date: {hcd_row[4]}"
        )
        new_entry = {
            "jurisdiction": juri,
            "type": hcd_row[2],
            "receivedDate": hcd_row[3],
            "finalDueDate": hcd_row[4],
        }
        if not dry_run:
            airtable_review_table.create(new_entry)
        else:
            print("Dry run: reviewTable.create(" + str(new_entry) + ")")

    # TODO: handle case of an updated entry (eg juris_in_both_sets list)

    #  Marcio's original implementation:
    # TODO: QUESTION --> in an updated review, does this create a new entry with the same jurisdiction in airtable?
    # newReviews = []
    # for x in reviewTableRows:
    #     if x not in airtableReviewRecords:
    #         newReviews.append(
    #             x["jurisdiction"]
    #             + " | type: "
    #             + x["type"]
    #             + " | received date: "
    #             + x["receivedDate"]
    #             + " | final due date: "
    #             + x["finalDueDate"]
    #         )
    #         new_entry = {
    #             "jurisdiction": x["jurisdiction"],
    #             "type": x["type"],
    #             "receivedDate": x["receivedDate"],
    #             "finalDueDate": x["finalDueDate"],
    #         }
    #         if not dry_run:
    #             airtable_review_table.create(new_entry)
    #         else:
    #             print("Dry run: reviewTable.create(" + str(new_entry) + ")")
    return HEReviewDiffs(new_reviews=new_reviews, exited_reviews=exited_reviews)


def run_scrape_hcd(dry_run=False):
    # Scrape the HCD website
    # tableRows = scrape_element_statuses()
    # reviewTableRows = scrape_elements_under_review()

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
    select_columns = ["JURISDICTION", "CYCLE", "TYPE", "RECEIVED_DATE", "FINAL_DUE_DATE"]
    # Each condition in the list must be true (AND). Inside a condition, any one of the values will match (OR)
    conditions = [
        WhereCondition(column_name="CYCLE", values=["5th Cycle", "6th Cycle"]),
        WhereCondition(column_name="TYPE", values=["ADOPTED", "SUBSEQUENT DRAFT", "DRAFT", "INITIAL DRAFT"]),
    ]
    hcd_review_table = hcd_page_scraper.fetch_table("Under Review", columns=select_columns, conditions=conditions)

    # Fetch "HE Compliance" status table. The column naming isn't consistent between tables, likely due to
    #  inconsistency at HCD.
    select_columns = ["Jurisdiction", "5th Cycle", "6th Cycle"]
    hcd_status_table = hcd_page_scraper.fetch_table("HE_Compliance", columns=select_columns, conditions=[])

    # fetch Airtables
    airtable_status_raw = airtable_element_status_table.all()
    airtable_review_raw = airtable_review_table.all()

    ############
    # diff Airtables and scraped data
    ############

    status_diff = diff_he_statuses(hcd_status_table, airtable_status_raw, dry_run)

    review_diff = diff_he_reviews(hcd_review_table, airtable_review_raw, dry_run)

    ############
    # store changes in runLog
    ############
    change_summary = ""
    if status_diff:
        change_summary = "\n*Jurisdiction(s) with new 6th Cycle status:*\n"
        for x in status_diff:
            change_summary = change_summary + x + "\n"

    if review_diff.new_reviews:
        change_summary = change_summary + "\n*Jurisdiction(s) newly IN review:*\n"
        for x in review_diff.new_reviews:
            change_summary = change_summary + x + "\n"

    if review_diff.exited_reviews:
        change_summary = change_summary + "\n*Jurisdiction(s) OUT of review:*\n"
        for x in review_diff.exited_reviews:
            change_summary = change_summary + x + "\n"

    if change_summary == "":
        change_summary = "No changes detected."

    runTime = datetime.datetime.now(timezone.utc).strftime("%m/%d/%y %H:%M:%S")
    if not dry_run:
        airtable_log_table.create({"runTime": runTime, "differences": change_summary})
    else:
        print("Dry run: logTable.create(" + runTime + ", " + change_summary + ")")

    return change_summary
