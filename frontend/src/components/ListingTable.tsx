// Provides functionality to render the listings table.
// Also renders filters under each of the column headers

import { ColumnFiltersState, flexRender, Table } from "@tanstack/react-table"
import * as React from "react"
import { ErrorBoundary } from "react-error-boundary"
import { Updater } from "use-immer"
import { Listing } from "../types"
import Filter from "./ListingFilters"
import Skeleton from "react-loading-skeleton"
import "react-loading-skeleton/dist/skeleton.css"

type Props = {
  table: Table<Listing>
  setColumnFilters: Updater<ColumnFiltersState>
}

export default function ListingTable({ table, setColumnFilters }: Props) {
  return (
    <ErrorBoundary fallback={<div>Error in ListingTable</div>}>
      {table.getRowModel().rows.length == 0 && <Skeleton count={50} />}
      <table className="table-auto pb-8 border-spacing-2 overflow-x-auto whitespace-nowrap border-separate">
        <thead>
          {table.getHeaderGroups().map((headerGroup) => (
            <tr key={headerGroup.id}>
              {headerGroup.headers.map((header) => {
                return (
                  <th key={header.id} colSpan={header.colSpan}>
                    {header.isPlaceholder ? null : (
                      <>
                        <div
                          {...{
                            className: header.column.getCanSort() ? "cursor-pointer select-none" : "",
                            onClick: header.column.getToggleSortingHandler(),
                          }}
                        >
                          {flexRender(header.column.columnDef.header, header.getContext())}
                          {{
                            asc: " 🔼",
                            desc: " 🔽",
                          }[header.column.getIsSorted() as string] ?? null}
                        </div>
                        {header.column.getCanFilter() ? (
                          <div>
                            <Filter
                              column={header.column}
                              table={table}
                              setColumnFilters={setColumnFilters}
                            />
                          </div>
                        ) : null}
                      </>
                    )}
                  </th>
                )
              })}
            </tr>
          ))}
        </thead>
        <tbody>
          {table.getRowModel().rows.map((row) => (
            <tr key={row.id}>
              {row.getVisibleCells().map((cell) => {
                const foo = flexRender(cell.column.columnDef.cell, cell.getContext())
                if (foo === null || (foo as any).props.renderValue() === null) {
                  return <td key={cell.id}>None </td>
                }
                if (typeof (foo as any).props.renderValue() === "object") {
                  console.log(
                    "WE have a problem in table cell rendering: ",
                    (foo as any).props.renderValue()
                  )
                  return <td key={cell.id}>BAD</td>
                } else {
                  return <td key={cell.id}> {foo} </td>
                }
              })}
            </tr>
          ))}
        </tbody>
      </table>
      <div className="h-2" />
    </ErrorBoundary>
  )
}
