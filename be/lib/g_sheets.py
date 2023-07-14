import logging
import re
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import date, timedelta
from enum import StrEnum
from typing import cast

import polars as pl
from django.core.exceptions import ImproperlyConfigured
from google.oauth2 import service_account
from googleapiclient import discovery
from parsnip.settings import BASE_DIR

# support this module in django and non-django env
try:
    from django.conf import settings  # check if django is setup.

    str(settings)  # check if django is setup (this will raise an exception if not)
    from django.core.cache import cache as django_cache
except ImproperlyConfigured:
    django_cache = None

log = logging.getLogger(__name__)

# API references:
# Client library: https://github.com/googleapis/google-api-python-client
# https://developers.google.com/sheets/api/reference/rest
# https://developers.google.com/sheets/api/quickstart/python
# https://googleapis.github.io/google-api-python-client/docs/dyn/sheets_v4.html
# https://developers.google.com/resources/api-libraries/documentation/sheets/v4/python/latest/index.html
# Replace with the path to your JSON key file
KEY_FILE_PATH = BASE_DIR / "parsnip-385123-dc1dfbcf5254.json"

# Replace with your Google Sheet URL
# sheet_url = "https://docs.google.com/spreadsheets/d/1gkM9FXICQ81ee_eZJSNs3iG-uow2FsCH9EUQsRxQPpM/edit"

# Verdant apt rent-roll and t12 google sheet
rent_roll_sheet_url = "https://docs.google.com/spreadsheets/d/1-ADiHnDJxAzCToVMd0aNeXRhdLniPja813ATcwNvJ_s/edit"
t12_sheet_url = "https://docs.google.com/spreadsheets/d/1KMXU0iDZPKJvcbEasme0bfMHVPsQ37NqtPohJ_DtbWo/edit"

# Verdant apt pro-forma google sheet
pro_forma_sheet_url = "https://docs.google.com/spreadsheets/d/1AotrAY7fs8dxId2tSukVINaIwYQ8hHa8bt-anqilDaQ/edit"


class SheetCell:
    def __init__(self, cell: str | tuple[str, str]):
        """SheetCell can be initialized with a string like "A1" or "Sheet1!A1" or a tuple like ("Sheet1", "A1")"""
        if isinstance(cell, tuple):
            self.sheet, self.cell = cell
        elif isinstance(cell, str):
            try:
                self.sheet, self.cell = cell.split("!")
            except ValueError:
                self.sheet = None
                self.cell = cell
        else:
            raise ValueError(f"Invalid cell reference: {cell}")

    @staticmethod
    def col_name_to_num(col_name: str) -> int:
        assert re.fullmatch(r"[A-Z]{1,2}", col_name)
        col_num = 0
        for i, c in enumerate(reversed(col_name)):
            col_num += (ord(c) - ord("A") + 1) * (26**i)
        return col_num

    @staticmethod
    def col_num_to_name(col_num: int) -> str:
        assert col_num > 0
        col_name = ""
        while col_num > 0:
            col_num, remainder = divmod(col_num - 1, 26)
            col_name = chr(ord("A") + remainder) + col_name
        return col_name

    def move_relative(self, rows: int = 0, cols: int = 0):
        match = re.fullmatch(r"[A-Z]{1,2}[0-9]{1,4}", self.cell)
        if match:
            col: str
            row: str
            col, row = match.group(0)
            colnum = self.col_name_to_num(col)
            rownum = int(row)
            colnum += cols
            rownum += rows
            col = self.col_num_to_name(colnum)
            row = str(rownum)
            return SheetCell((self.sheet, col + row))

    def to_string(self, skip_sheet: bool = False):
        if self.sheet and not skip_sheet:
            return f"'{self.sheet}'!{self.cell}"
        else:
            return f"{self.cell}"

    def __repr__(self) -> str:
        if self.sheet:
            return f"SheetCell({self.sheet}!{self.cell})"
        else:
            return f"SheetCell({self.cell})"


@dataclass(kw_only=True)  # kw_only=True keeps things clean for inheritance
class GoogleSheet:
    sheet_url: str

    class ValueRenderOption(StrEnum):
        FORMATTED = "FORMATTED_VALUE"
        UNFORMATTED = "UNFORMATTED_VALUE"
        FORMULA = "FORMULA"

    def __post_init__(self) -> None:
        self._sheet_id = self.sheet_url.split("spreadsheets/d/")[1].split("/")[0]
        self.credentials = service_account.Credentials.from_service_account_file(
            KEY_FILE_PATH, scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )
        self.service = discovery.build("sheets", "v4", credentials=self.credentials)

    def read_data(
        self,
        start_range: SheetCell,
        end_range: SheetCell = None,
        value_render_option: ValueRenderOption = ValueRenderOption.FORMATTED,
    ) -> list[list[str]] | None:
        range_str = self.range_string(start_range=start_range, end_range=end_range)
        result = self.service.spreadsheets().values()
        result = result.get(
            spreadsheetId=self._sheet_id, range=range_str, valueRenderOption=value_render_option
        ).execute()
        return result.get("values", [])

    def write_column(self, data: Sequence[str | int | float | date], start_range: SheetCell, end_range=None):
        """write a list of data as a single column. If end_range isn't provided, we'll allow it to write down
        the entire column"""
        assert isinstance(data, Sequence)
        if isinstance(data[0], date):
            # convert date back to number of days since Dec 30, 1890 (the epoch for Google Sheets)
            typed_data = [(d - date(1899, 12, 30)).days for d in data]
        else:
            assert isinstance(data[0], str | int | float)
            typed_data = data
        data_columns = [[x] for x in typed_data]
        if not end_range:
            end_range = start_range.move_relative(rows=len(data_columns))
        range_str = self.range_string(start_range, end_range)
        body = {"values": data_columns}
        result = (
            self.service.spreadsheets()
            .values()
            .update(spreadsheetId=self._sheet_id, range=range_str, valueInputOption="RAW", body=body)
            .execute()
        )
        return result.get("updatedCells")

    def write_data(self, data: list[str] | list[list[str]], start_range: SheetCell, end_range: SheetCell = None):
        """write any dimension of data to a range"""
        range_str = self.range_string(start_range, end_range)
        body = {"values": data}
        result = (
            self.service.spreadsheets()
            .values()
            .update(spreadsheetId=self._sheet_id, range=range_str, valueInputOption="RAW", body=body)
            .execute()
        )
        return result.get("updatedCells")

    # list all worksheet names
    def worksheets(self) -> list[str]:
        result = self.service.spreadsheets().get(spreadsheetId=self._sheet_id).execute()
        sheets = result.get("sheets", [])
        sheet_names = [sheet["properties"]["title"] for sheet in sheets]
        return sheet_names

    # Function to list named ranges
    def list_named_ranges(self) -> list[str]:
        result = self.service.spreadsheets().get(spreadsheetId=self._sheet_id, fields="namedRanges").execute()
        named_ranges = result.get("namedRanges", [])
        return [n["name"] for n in named_ranges]

    def data_from_named_range(self, named_range: str, data_type: type):
        try:
            result = (
                self.service.spreadsheets()
                .values()
                .get(
                    spreadsheetId=self._sheet_id,
                    range=named_range,
                    valueRenderOption=str(
                        GoogleSheet.ValueRenderOption.UNFORMATTED
                    ),  # other options are UNFORMATTED_VALUE, FORMULA
                )
                .execute()
            )
            res = result.get("values", [])
            if data_type is date:
                typed_res = [[date(1899, 12, 30) + timedelta(days=int(x)) for x in row] for row in res]
            else:
                typed_res = [[data_type(x) for x in row] for row in res]
            return typed_res
        except Exception as e:
            print(e)
            raise

    @staticmethod
    def range_string(start_range: SheetCell, end_range: SheetCell or None):
        if not end_range:
            return start_range.to_string()
        elif start_range.sheet != end_range.sheet and end_range.sheet is not None:
            raise ValueError(
                f"Range {start_range},{end_range} spans multiple sheets: {start_range.sheet} and {end_range.sheet}"
            )
        return f"{start_range.to_string()}:{end_range.to_string(skip_sheet=True)}"

    def find_column_starts(
        self, start_range: SheetCell, end_range: SheetCell, strings_to_find
    ) -> dict[str, SheetCell]:
        """Given a range of cells to search in, find columns with a heading in strings_to_find and report the
        first cell where data starts in each column."""
        data = self.read_data(
            start_range=start_range, end_range=end_range, value_render_option=self.ValueRenderOption.FORMATTED
        )
        print(data)
        # Find the column starts
        column_starts = {}
        lc_strings_to_find = {s.lower() for s in strings_to_find}
        for row_idx, row in enumerate(data):
            for col_idx, cell in enumerate(row):
                if cell.lower().strip() in lc_strings_to_find and cell not in column_starts:
                    lc_strings_to_find -= {cell.lower().strip()}
                    # Have heading of column. First data cell is the next cell down (row_idx+1)
                    moved_cell = start_range.move_relative(rows=row_idx + 1, cols=col_idx)
                    column_starts[cell] = moved_cell
        print(column_starts)
        return column_starts

    def named_ranges_to_polars_df(self, named_ranges: Iterable[str, type]) -> pl.DataFrame:
        dfs = []

        for range_name, range_type in named_ranges:
            # Get data from the named range - returns one or more columns
            data: list[list[float | date]] = self.data_from_named_range(range_name, range_type)

            # Create polars column name(s) for the named range
            col_names = [range_name] if len(data[0]) == 1 else [f"{range_name}_{i}" for i in range(len(data[0]))]

            # Create a Polars DataFrame for the named range
            df = pl.DataFrame(dict(zip(col_names, zip(*data, strict=True), strict=True)))
            dfs.append(df)

        # Concatenate the DataFrames horizontally
        result_df = pl.concat(dfs, how="horizontal")
        return result_df


@dataclass(kw_only=True)
class RentRollSheet(GoogleSheet):
    use_cache: bool = True

    rent_roll_named_range_dict = {
        "UnitNum": str,
        "Occupied": str,
        "CurrentRent": int,
        "SqFt": int,
        "MoveInDate": date,
        "LeaseEndDate": date,
    }

    def __post_init__(self) -> None:
        super().__post_init__()
        self.rent_roll_named_range_set = set(self.rent_roll_named_range_dict.keys())
        self.rent_roll_df: pl.DataFrame = self._fetch()
        if self.use_cache and not django_cache:
            raise ModuleNotFoundError("use_cache is True but django cache is not imported")

    def _fetch(self) -> pl.DataFrame:
        """Get rent roll data from a rent roll datasheet that's been labelled, and return a Polars DataFrame"""
        if self.use_cache:
            rent_roll_dframe = django_cache.get("rent_roll_dframe_" + self._sheet_id)
            if rent_roll_dframe is not None:
                log.debug("Rent roll data found in cache")
                return rent_roll_dframe
        found_named_ranges = set(self.list_named_ranges())
        assert self.rent_roll_named_range_set.issubset(found_named_ranges)
        # cast due to pycharm issue? dict_items are iterable...
        self.rent_roll_df = self.named_ranges_to_polars_df(
            cast(Iterable[str, type], self.rent_roll_named_range_dict.items())
        )
        log.info(f"Rent Roll (cache missed): for {self._sheet_id}")
        if django_cache:
            django_cache.set("rent_roll_dframe_" + self._sheet_id, self.rent_roll_df)
        return self.rent_roll_df


@dataclass(kw_only=True)
class T12Sheet(GoogleSheet):
    pass


@dataclass(kw_only=True)
class ProformaSheet(GoogleSheet):
    def populate_rent_roll(self, rent_roll: RentRollSheet):
        # Get rent roll data
        rent_roll_df = rent_roll.rent_roll_df

        col_dict: dict[str, SheetCell] = self.find_column_starts(
            start_range=SheetCell("Rent Roll-Input!A1"),
            end_range=SheetCell("Z5"),
            strings_to_find=rent_roll.rent_roll_named_range_set,
        )
        print(f"Writing updates to pro forma Google Sheet. cols = {list(col_dict.keys())}")
        # update fields in the pro format sheet
        for col_str, start_cell in col_dict.items():
            print(f"... Column {col_str} to cell {start_cell.to_string(skip_sheet=True)}")
            result = self.write_column(start_range=start_cell, data=rent_roll_df[col_str].to_list())  # noqa:F841
        # data = rent_roll_gsheet.read_data(f"{rent_roll_sheets[0]}!A1:D10")
        # print("Read data:", data)

    def populate_t12(self, t12_sheet: T12Sheet):
        """Get T12 income and expense data and populate it into the pro forma sheet."""
        found_named_ranges = set(t12_sheet.list_named_ranges())  # noqa:F841

        # start_dict = self.find_column_starts(
        #     start_range=SheetCell("Rent Roll-Input!A1"),  # TODO: update to T12 location
        #     end_range=SheetCell("Z5"),
        #     strings_to_find=rent_roll_named_ranges,
        # )
        #


def main():
    # sources: rent roll and t12 sheets
    rent_roll_gsheet = RentRollSheet(sheet_url=rent_roll_sheet_url, use_cache=False)
    t12_gsheet = T12Sheet(sheet_url=t12_sheet_url)

    # destination: pro_forma sheet.
    pro_forma_gsheet = ProformaSheet(sheet_url=pro_forma_sheet_url)
    pro_forma_gsheet.populate_rent_roll(rent_roll_gsheet)
    pro_forma_gsheet.populate_t12(t12_gsheet)
    print("Data written successfully")

    # Example of writing
    rent_roll_sheets = rent_roll_gsheet.worksheets()
    assert len(rent_roll_sheets) == 1
    rent_roll_gsheet.write_data([["Hello, world!"]], SheetCell((rent_roll_sheets[0], "A1")))
    print("Done")


if __name__ == "__main__":
    main()
