import * as React from "react"
import { useCallback, useEffect, useMemo } from "react"
import { Link, useParams } from "react-router-dom"
import useSWR from "swr"
import "react-data-grid/lib/styles.css"
import DataGrid, { Column } from "react-data-grid"
import { apiRequest, fetcher } from "../utils/fetcher"
import { LoginRespDataCls, RentRollRespDataCls } from "../types"

// React data grid: https://github.com/adazzle/react-data-grid/blob/main/README.md
// interface Row {
//   id: number
//   title: string
// }
// const columns = [
//   { key: "id", name: "ID" },
//   { key: "title", name: "Title", sortable: true },
// ]

// const rows = [
//   { id: 0, title: "Example" },
//   { id: 1, title: "Demo" },
// ]

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

export default function BovDetailPage() {
  const [rows, setRows] = React.useState<RowData[]>([])
  const [isLoading, setIsLoading] = React.useState(true)
  const [error, setError] = React.useState<boolean | Record<string, string>>(false)
  const { id } = useParams<{ id: string }>()

  // get property profiles
  useEffect(() => {
    document.title = `BOV ${id}`
    // load initial values of state from local storage
  }, [id])
  useEffect(() => {
    apiRequest<typeof RentRollRespDataCls>(`api/properties/bov/${id}`, {
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
  // const { data, error, isValidating } = useSWR(`/api/properties/bov/${id}`, fetcher)
  // const addr: string = data?.address.street_addr || "Loading..."

  // useMemo(() => {
  //   console.log("useMemo")
  //   if (data) {
  //     const rowData = columnarToRowData(data)
  //     console.log("Row data:")
  //     console.log(rowData)
  //     setRows(rowData)
  //   }
  // }, [data])
  // const data = [{ id: 1, address: "555 main st" }]

  if (error) return <div>failed to load BOV</div>
  if (isLoading) return <div>loading...</div>
  return (
    <div>
      <h1>BOV detail page</h1>
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
