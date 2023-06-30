import * as React from "react";
import { useEffect } from "react";
import { apiRequest } from "../utils/fetcher";
import { RentRollRespDataCls } from "../types";
import DataGrid from "react-data-grid";

// React data grid: https://github.com/adazzle/react-data-grid/blob/main/README.md

function rowKeyGetter(row: any) {
  // need this method to support row selection
  return row.UnitNum
}

type ColumnarData = {
  [key: string]: any[]
}

type RowData = {
  [key: string]: any
}

function columnarToRowData(columnarData: ColumnarData): RowData[] {
  const keys = Object.keys(columnarData)
  const rowCount = columnarData[keys[0]].length

  return Array.from({ length: rowCount }, (_, i) =>
    keys.reduce((row: RowData, key) => {
      row[key] = columnarData[key][i]
      return row
    }, {})
  )
}

export default function RentRoll({ id }: {id: number}) {
  const [rows, setRows] = React.useState<RowData[]>([])
  const [isLoading, setIsLoading] = React.useState(true)
  const [error, setError] = React.useState<boolean | Record<string, string>>(false)

  useEffect(() => {
    apiRequest<typeof RentRollRespDataCls>(`/api/properties/bov/${id}`, {
      RespDataCls: RentRollRespDataCls,
      isPost: false,
      body: undefined,
    })
      .then(({ errors, data, message }) => {
        console.log("Column data:")
        console.log(data)
        const rowData = columnarToRowData(data)
        console.log("Row data:")
        console.log(rowData)
        setRows(rowData)
        setError(errors)
        setIsLoading(false)
      })
      .catch((err) => {
        console.log("Error getting property profiles:", err)
        setError(true)
        setIsLoading(false)
      })
  }, [id])
  if (error) return <div>failed to load Rent Roll</div>
  if (isLoading) return <div>loading...</div>
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
        rows={rows}
        rowKeyGetter={rowKeyGetter}
        // onSort={(columnKey, sortDirection) => console.log(columnKey, sortDirection)}
        className="rdg-light"
      />
    </div>
  )
}
