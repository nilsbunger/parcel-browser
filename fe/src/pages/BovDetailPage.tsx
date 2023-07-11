import * as React from "react"
import { useEffect } from "react"
import { useParams } from "react-router-dom"
import "react-data-grid/lib/styles.css"
import RentRoll from "../components/RentRoll";
import ProfitLossTable from "../components/ProfitLossTable";
import PropertyFilters from "../components/PropertyFilters";
import DataGrid, { Column } from "react-data-grid"
import { apiRequest, fetcher } from "../utils/fetcher"
import { LoginRespDataCls, RentRollRespDataCls } from "../types"
import { Dropzone, MIME_TYPES } from "@mantine/dropzone"
import { Box, Button, Flex, Group, LoadingOverlay, Modal, rem, Table, Text, useMantineTheme } from "@mantine/core"
import { IconPhoto, IconTable, IconUpload, IconX } from "@tabler/icons"
import { useDisclosure } from "@mantine/hooks"
import { DataTable } from "mantine-datatable"

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
  // setup and state
  const { id } = useParams<{ id: string }>()
  const [showRentRoll, setShowRentRoll] = React.useState(false)
  useEffect(() => {
    document.title = `BOV ${id}`
  }, [id])

  const rentRollDisplay = !id
    ? <div>Invalid BOV id</div>
    : !showRentRoll ? <button onClick={() => setShowRentRoll(true)}>Load Rent Roll</button>
      : <RentRoll id={parseInt(id)}></RentRoll>

  return (<div>
      <h2 className="py-5">Filters</h2>
      <PropertyFilters />
      <h2 className="py-5">Profit & Loss</h2>
      <div className="py-5">
        <ProfitLossTable/>
      </div>
      <h2 className="py-5">Rent Roll</h2>
      {rentRollDisplay}
      <div className="py-5"></div>
    </div>

  )
}
