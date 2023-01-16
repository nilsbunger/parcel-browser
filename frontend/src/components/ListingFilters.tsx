// File that defines the different filter components for various types
// of columns on the listing table.

import * as React from "react"

import { Table, Column, ColumnFiltersState } from "@tanstack/react-table"
import { Updater } from "use-immer"

function Filter({
  column,
  table,
  setColumnFilters,
}: {
  column: Column<any, unknown>
  table: Table<any>
  setColumnFilters: Updater<ColumnFiltersState>
}) {
  const firstValue = table.getPreFilteredRowModel().flatRows[0]?.getValue(column.id)

  const columnFilterValue = column.getFilterValue()

  // Converting to sqft if necessary
  let modifier = (x) => x

  const sortedUniqueValues = React.useMemo(
    () =>
      typeof firstValue === "number" ? [] : Array.from(column.getFacetedUniqueValues().keys()).sort(),
    [column.getFacetedUniqueValues()]
  )

  return column.columnDef.filterFn === "inNumberRange" ? (
    <div>
      <div className="flex space-x-2">
        <DebouncedInput
          type="number"
          min={modifier(Number(column.getFacetedMinMaxValues()?.[0] ?? ""))}
          max={modifier(Number(column.getFacetedMinMaxValues()?.[1] ?? ""))}
          value={(columnFilterValue as [number, number])?.[0] ?? ""}
          onChange={(value) => {
            setColumnFilters((draft) => {
              const filterIndex = draft.findIndex((item) => item.id === column.id)
              if (filterIndex === -1) {
                draft.push({
                  id: column.id,
                  value: [modifier(value), undefined],
                })
              } else {
                draft[filterIndex].value[0] = modifier(value)
              }
            })
          }}
          placeholder={`Min ${
            column.getFacetedMinMaxValues()?.[0]
              ? `(${modifier(column.getFacetedMinMaxValues()?.[0])})`
              : ""
          }`}
          className="w-24 border shadow rounded"
        />
        <DebouncedInput
          type="number"
          min={modifier(Number(column.getFacetedMinMaxValues()?.[0] ?? ""))}
          max={modifier(Number(column.getFacetedMinMaxValues()?.[1] ?? ""))}
          value={(columnFilterValue as [number, number])?.[1] ?? ""}
          onChange={(value) => {
            setColumnFilters((draft) => {
              const filterIndex = draft.findIndex((item) => item.id === column.id)
              if (filterIndex === -1) {
                draft.push({
                  id: column.id,
                  value: [undefined, modifier(value)],
                })
              } else {
                draft[filterIndex].value[1] = modifier(value)
              }
            })
          }}
          placeholder={`Max ${
            column.getFacetedMinMaxValues()?.[1]
              ? `(${modifier(column.getFacetedMinMaxValues()?.[1])})`
              : ""
          }`}
          className="w-24 border shadow rounded"
        />
      </div>
      <div className="h-1" />
    </div>
  ) : (
    <>
      <datalist id={column.id + "list"}>
        {sortedUniqueValues.slice(0, 5000).map((value: any) => (
          <option value={value} key={value} />
        ))}
      </datalist>
      <DebouncedInput
        type="text"
        value={(columnFilterValue ?? "") as string}
        onChange={(value) => {
          setColumnFilters((draft) => {
            const filterIndex = draft.findIndex((item) => item.id === column.id)
            if (filterIndex === -1) {
              draft.push({
                id: column.id,
                value,
              })
            } else {
              draft[filterIndex].value = value
            }
          })
        }}
        placeholder={`Search... (${column.getFacetedUniqueValues().size})`}
        className="w-36 border shadow rounded"
        list={column.id + "list"}
      />
      <div className="h-1" />
    </>
  )
}

// A debounced input react component
// from https://tanstack.com/table/v8/docs/examples/react/filters
function DebouncedInput({
  value: initialValue,
  onChange,
  debounce = 500,
  ...props
}: {
  value: string | number
  onChange: (value: string | number) => void
  debounce?: number
} & Omit<React.InputHTMLAttributes<HTMLInputElement>, "onChange">) {
  const [value, setValue] = React.useState(initialValue)

  React.useEffect(() => {
    setValue(initialValue)
  }, [initialValue])

  React.useEffect(() => {
    const timeout = setTimeout(() => {
      onChange(value)
    }, debounce)

    return () => clearTimeout(timeout)
  }, [value])

  return (
    <input
      {...props}
      value={value}
      onChange={(e) => setValue(e.target.value)}
      className="input input-bordered w-[160px] max-w-xs"
    />
  )
}

export default Filter
