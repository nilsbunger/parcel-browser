# HCD-scraper-python

## To run

- add airtable API key to `AIRTABLE_API_KEY` env variable
- `./manage.py scrape_hcd`

## How it works

- simulates a power BI service call for the Housing Element Compliance table
  on https://www.hcd.ca.gov/planning-and-community-development/housing-open-data-tools/housing-element-implementation-and-apr-dashboard
- `request_body` JSONs are the request bodies copied from a browser session
- records are stored and changes are logged on Home3's Airtable