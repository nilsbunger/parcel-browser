import * as React from "react";
import { KeyedRow } from "../types";
import DataGrid from "react-data-grid";
import 'react-data-grid/lib/styles.css';

// React data grid: https://github.com/adazzle/react-data-grid/blob/main/README.md

function rowKeyGetter(row: KeyedRow) {
  // need this method to support row selection
  return row.UnitNum
}



export default function RentRoll({ rows }: {rows: KeyedRow[] | null}) {
  return (
    <div>
      <DataGrid
        columns={[
          { key: "CurrentRent", name: "Current Rent" },
          { key: "UnitNum", name: "Unit Number" },
          { key: "Occupied", name: "Occupied" },
          { key: "MoveInDate", name: "Move In Date" },
          { key: "LeaseEndDate", name: "Lease End Date" },
          { key: "SqFt", name: "SqFt" },
        ]}
        rows={rows || []}
        rowKeyGetter={rowKeyGetter}
        // onSort={(columnKey, sortDirection) => console.log(columnKey, sortDirection)}
        className="rdg-light"
      />
    </div>
  )
}
