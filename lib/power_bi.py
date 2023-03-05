import base64
from datetime import datetime, timezone
import json
import re

from bs4 import BeautifulSoup
from django.core.cache import cache
from pydantic import BaseModel
import requests


class BITable(BaseModel):
    table_name: str
    column_names: list[str]
    rows: list[list[object]]


class WhereCondition(BaseModel):
    column_name: str  # column name
    values: list[object]  # list of values to accept (OR clause)


# Scrape a MS PowerBI web URL which contains a BI iframe.
# Originally inspired by https://stackoverflow.com/questions/62480695/python-scraping-of-a-site-that-contains-powerbi-graphs
class PowerBIScraper:
    page_headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36"
    }

    def __init__(self, page_url: str):
        # Initialize class, fetch page containing iframe and the contents of the iframe itself.
        self.url = page_url
        soup = BeautifulSoup(
            requests.get(page_url, verify=False, headers=self.page_headers).content, "html.parser"
        )

        # now fetch the iframe contents
        html_data = requests.get(soup.iframe["src"]).text
        d = json.loads(base64.b64decode(soup.iframe["src"].split("=")[-1]).decode("utf-8"))
        self.tenantId = d["t"]
        self.resourceKey = d["k"]
        self.resolvedClusterUri = re.search(r"var resolvedClusterUri = '(.*?)'", html_data)[1].replace(
            "-redirect", "-api"
        )
        self.requestId = re.search(r"var requestId = '(.*?)'", html_data)[1]
        self.activityId = re.search(r"var telemetrySessionId =  '(.*?)'", html_data)[1]

        # now that we've initialized request_id, etc, we can make API calls. This first one lists all the
        # tables, which we'll use for future calls.
        self.data_models = requests.get(self.models_url, headers=self.api_headers).json()
        assert len(self.data_models["models"]) == 1, "Only one model supported"

        # Clean up data_models by converting JSON strings to actual JSON objects.
        self.data_models["exploration"]["config"] = json.loads(self.data_models["exploration"]["config"])
        self.dataset_id = self.data_models["models"][0]["dbName"]
        for section in self.data_models["exploration"]["sections"]:
            section["config"] = json.loads(section["config"])
            for container in section["visualContainers"]:
                container["config"] = json.loads(container["config"])
                if "filters" in container:
                    container["filters"] = json.loads(container["filters"])

        self.report_id = self.data_models["exploration"]["report"]["objectId"]
        self.model_id = self.data_models["models"][0]["id"]

        # now that we've initialized data_models, we can call the schema API to get the column names.
        self.schema = requests.get(self.schema_url, headers=self.api_headers).json()
        if "error" in self.schema:
            # We failed to get schema. The schema query is throttled aggressively. In this case, we use a cached
            # version of the schema.
            self.schema = cache.get("powerbi_schema:" + page_url)
            if self.schema is None:
                raise Exception("Failed to get schema for PowerBI page: " + page_url)
            print("Using cached schema for PowerBI page: " + page_url)
        else:
            # We got the schema from our web request.
            # Save it using the default django cache since we can fail to get it next time.
            cache.set("powerbi_schema:" + page_url, self.schema, 60 * 60 * 24 * 7)

    def list_sections(self):
        # List all the sections and their display names. Each section is typically a slide.
        return [section["displayName"] for section in self.data_models["exploration"]["sections"]]

    def list_tables(self):
        # List all the tables that are part of this model. Note we only support a single model.
        assert len(self.schema["schemas"]) == 1, "Only one schema supported (meaning only one model)"
        return [x["Name"] for x in self.schema["schemas"][0]["schema"]["Entities"]]

    def list_columns(self, table_name) -> list[str]:
        table = self._table_from_table_name(table_name)
        return self._columns_from_table(table)

    def fetch_table(self, table_name, columns, conditions: list[WhereCondition]) -> BITable:
        # fetch table from HCD with optional conditions (WHERE clauses) for filtering
        query_limit = 5000
        table = self._table_from_table_name(table_name)
        query = self._query_from_table(table, columns, conditions, query_limit)
        payload = {
            "version": "1.0.0",
            "queries": [
                {
                    "Query": query,
                    "CacheKey": "",
                    "QueryId": "",
                    "ApplicationContext": {
                        "DatasetId": self.dataset_id,
                        "Sources": [{"ReportId": self.report_id}],
                    },
                }
            ],
            "cancelQueries": [],
            "modelId": self.model_id,
        }
        raw_table_data = requests.post(self.query_url, json=payload, headers=self.api_headers).json()
        assert (
            len(raw_table_data["results"][0]["result"]["data"]["dsr"]["DS"][0]["PH"][0]["DM0"]) < query_limit
        ), f"This query needs pagination or a higher query limit, which isn't implemented"

        table_data = self._decompress_table(raw_table_data, table_name)
        return table_data

    def _table_from_table_name(self, table_name):
        assert len(self.schema["schemas"]) == 1, "Only one schema supported (meaning only one model)"
        table = [x for x in self.schema["schemas"][0]["schema"]["Entities"] if x["Name"] == table_name]
        assert len(table) == 1
        return table[0]

    def _columns_from_table(self, table) -> list[str]:
        return [x["Name"] for x in table["Properties"]]

    def _decompress_col_mapper(self, col_def, value_dict):
        # value_dict: keys are 'D0', 'D1', ... representing column names, and each value is a list which is indexed into
        # col_def: a dict containing keys:
        #   'T': column type -- 1 means indexed integer (index into value_dict); 7 means timestamp.
        #   'DN': column name -- exists if T=1, and is the key into value_dict
        # return a function that takes an encoded value for this column and returns the decoded value
        if col_def["T"] == 1:
            return lambda x: (value_dict[col_def["DN"]][x] if isinstance(x, int) else x)
        elif col_def["T"] == 7:
            return lambda x: datetime.fromtimestamp(x / 1000, tz=timezone.utc) if x else None
        else:
            raise Exception("Unknown column type: " + str(col_def["T"]))

    def _decompress_table(self, table_data, table_name) -> BITable:
        # Convert a table from a GET response, decoding the compression
        # and the mappings from indices to actual values.
        section_root = table_data["results"][0]["result"]["data"]
        col_names = [
            key["Source"]["Property"]
            for key in section_root["descriptor"]["Expressions"]["Primary"]["Groupings"][0]["Keys"]
        ]
        table = BITable(table_name=table_name, column_names=col_names, rows=[])

        # decompress results, putting them into 'XC' field
        decompressible_array = section_root["dsr"]["DS"][0]["PH"][0]["DM0"]
        value_dict = section_root["dsr"]["DS"][0]["ValueDicts"]
        num_fields = len(decompressible_array[0]["C"])
        col_mapper_fn = [self._decompress_col_mapper(x, value_dict) for x in decompressible_array[0]["S"]]
        prev_c = None
        for entry in decompressible_array:
            if "R" not in entry and "Ø" not in entry:
                entry["XC"] = entry["C"]
            else:
                entry["XC"] = [None] * num_fields
                decompress_bitfield = entry["R"] if "R" in entry else 0
                zero_bitfield = entry["Ø"] if "Ø" in entry else 0
                c_idx = 0
                for i in range(0, num_fields):
                    if decompress_bitfield & (1 << i):
                        entry["XC"][i] = prev_c[i]
                    elif zero_bitfield & (1 << i):
                        entry["XC"][i] = None
                    else:
                        entry["XC"][i] = entry["C"][c_idx]
                        c_idx += 1
            prev_c = entry["XC"]
            if len(entry["XC"]) != num_fields:
                raise Exception("Decompression failed: num_fields mismatch")
            entry["MXC"] = [col_mapper_fn[i](x) for i, x in enumerate(entry["XC"])]
            table.rows.append(entry["MXC"])
        return table

    @property
    def schema_url(self):
        return self.resolvedClusterUri + "/public/reports/" + self.resourceKey + "/conceptualschema"

    @property
    def models_url(self):
        return (
            self.resolvedClusterUri
            + "/public/reports/"
            + self.resourceKey
            + "/modelsAndExploration?preferReadOnlySession=true"
        )

    @property
    def query_url(self):
        return self.resolvedClusterUri + "/public/reports/querydata?synchronous=true"

    @property
    def api_headers(self):
        return {
            "ActivityId": self.activityId,
            "RequestId": self.requestId,
            "X-PowerBI-ResourceKey": self.resourceKey,
        }

    def _query_from_table(self, table, columns, conditions=[], query_limit=1000):
        # generate a query object for one table, selecting columns and filtering by conditions, and return it.
        cols_avail = self._columns_from_table(table)
        table_name = table["Name"]
        sel_clauses = [
            {"Column": {"Expression": {"SourceRef": {"Source": "t"}}, "Property": col}, "Name": "t." + col}
            for col in cols_avail
            if col in columns
        ]
        if len(sel_clauses) != len(columns):
            raise Exception("Some columns not found in table: " + str(columns))
        from_clauses = [{"Name": "t", "Entity": table_name, "Type": 0}]
        where_clauses = []
        for cond in conditions:
            where_clauses.append(
                {
                    "Condition": {
                        "In": {
                            "Expressions": [
                                {
                                    "Column": {
                                        "Expression": {"SourceRef": {"Source": "t"}},
                                        "Property": cond.column_name,
                                    }
                                }
                            ],
                            "Values": [[{"Literal": {"Value": "'" + val + "'"}}] for val in cond.values],
                        }
                    }
                }
            )
        # The "Projections" field seems to just be a list of indices into the selected columns.
        projections = list(range(len(sel_clauses)))

        return {
            "Commands": [
                {
                    "SemanticQueryDataShapeCommand": {
                        "Query": {
                            "Version": 2,
                            "From": from_clauses,
                            "Select": sel_clauses,
                            "Where": where_clauses,
                        },
                        "Binding": {
                            "Primary": {"Groupings": [{"Projections": projections}]},
                            "DataReduction": {"DataVolume": 3, "Primary": {"Window": {"Count": query_limit}}},
                            "Version": 1,
                        },
                    }
                }
            ]
        }
