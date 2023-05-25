import useSWR, { Fetcher, Middleware } from "swr"
import * as React from "react"
import { ChangeEvent, ReactElement, useEffect, useState } from "react"
import { z } from "zod"
import {
  Cell,
  ColumnFiltersState,
  getCoreRowModel,
  getFacetedMinMaxValues,
  getFacetedRowModel,
  getFacetedUniqueValues,
  getFilteredRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  Row,
  SortingState,
  Table,
  useReactTable,
} from "@tanstack/react-table"
import { Link } from "react-router-dom"
import { fetcher, swrLaggy } from "../utils/fetcher"
import { asSqFt, ONEDAY, snakeCaseToTitleCase } from "../utils/utils"
import { Listing } from "../types"
import ListingsMap from "../components/layout/ListingsMap"
import { useImmer } from "use-immer"
import TablePagination from "../components/TablePagination"
import ListingTable from "../components/ListingTable"
import { BACKEND_DOMAIN } from "../constants"

const basicAccessor = (cell: Cell<Listing, unknown>) => {
  return String(cell.getValue()).slice(0, 20)
}

const apnAccessor = ({ row }: { row: Row<Listing> }): ReactElement => (
  <Link to={{ pathname: `/analysis/${row.getValue("analysis_id")}` }} className="underline text-darkblue">
    {row.getValue("apn")}
  </Link>
)

const addressAccessor = ({ row }: { row: Row<Listing> }) => (
  <div className={"relative " + ((row.getValue("apn") as string).slice(8, 10) !== "00" ? "bg-gray-300" : "")}>
    <Link to={{ pathname: `/analysis/${row.getValue("analysis_id")}` }} className="underline text-darkblue">
      {(row.getValue("address") as string).slice(0, 20)}
    </Link>
    {row.original.is_tpa && <div className="mb-1 gap-2 badge badge-primary text-med">TPA</div>}{" "}
    {row.original.is_mf && <div className="badge badge-accent text-med">MF</div>}
  </div>
)

const asSqFtAccessor = ({ cell }: { cell: Cell<Listing, unknown> }) => asSqFt(cell.getValue()).toLocaleString()

const roundingAccessor = ({ cell }: { cell: Cell<Listing, unknown> }) => {
  return (cell.getValue() as number).toPrecision(2)
}

const priceAccessor = ({ cell }: { cell: Cell<Listing, unknown> }): ReactElement | string => {
  // @ts-ignore
  const prev_price = cell.row.getValue("metadata")["prev_values"][cell.column.id] as number
  if (prev_price) {
    return (
      <span>
        $
        {
          // @ts-ignore
          cell.getValue().toLocaleString()
        }{" "}
        <s> {prev_price} </s>
      </span>
    )
  } else {
    return "$" + (cell.getValue() as number).toLocaleString()
  }
}

const statusAccessor = ({ row }: { row: Row<Listing> }) => {
  const metadata: { [key: string]: any } = row.getValue("metadata")
  return metadata["category"] == "new" ? <div className="badge badge-accent">NEW</div> : ""
}

// calculate days since found
const founddateAccessor = ({ cell }: { cell: Cell<Listing, unknown> }) => {
  const foundDate = cell.getValue() as string
  const foundtime = new Date(foundDate).getTime()
  const nowtime = Date.now()
  return Math.round((nowtime - foundtime) / ONEDAY)
}

const mfFilterFn = (row: Row<Listing>, columnId: number, filterValue: boolean): boolean => {
  return row.original.is_mf || !filterValue
}

const tpaFilterFn = (row: Row<Listing>, columnId: number, filterValue: boolean): boolean => {
  return row.original.is_tpa || !filterValue
}

const neighborhoodFilterFn = (row: Row<Listing>, columnId: number, filterValue: string): boolean => {
  return true
}
// Schema for what Listings page stores in local storage.
const ListingsPageLocalStorage = z.object({
  pageSize: z.number().default(25),
  pageIndex: z.number().default(1),
  sorting: z.object({ id: z.string(), desc: z.boolean() }).array(),
  // columnFilters examples:
  //  { "id": "is_mf", "value": false },
  //  { "id": "neighborhood", "value": "" },
  //  { "id": "price", "value": ["", undefined] }]  <-- range filter: undefined means no filter for that side of range
  columnFilters: z.array(
    z.object({
      id: z.string(),
      value: z.union([z.string(), z.boolean(), z.number(), z.array(z.string().optional(), z.string().optional())]),
    })
  ),
})
type ListingsPageLocalStorage = z.infer<typeof ListingsPageLocalStorage>

const MyColumnDef = z
  .object({
    accessorKey: z.string(),
    cell: z.function().default(() => basicAccessor),
    header: z.string(),
    enableColumnFilter: z.boolean().default(false),
    filterFn: z.any().optional(),
    visible: z.boolean().default(false),
  })
  .strict()
type MyColumnDef = z.infer<typeof MyColumnDef>

const MyColumn = z.tuple([z.string(), MyColumnDef.partial()]).or(z.tuple([z.string()]))
type MyColumn = z.infer<typeof MyColumn>
const colState = z.array(MyColumn).parse([
  ["founddate", { visible: true, header: "DSU", cell: founddateAccessor }],
  ["apn", { cell: apnAccessor }],
  ["address", { visible: true, cell: addressAccessor }],
  ["zone", { visible: true }],
  ["is_mf", { filterFn: mfFilterFn }],
  ["is_tpa", { filterFn: tpaFilterFn }],
  ["max_cap_rate", { visible: true, header: "CapRate" }],
  ["num_existing_buildings", {}],
  ["is_flag_lot", {}],
  ["analysis_id", { visible: false }],
  ["carports"],
  ["garages"],
  ["neighborhood", { visible: true, filterFn: neighborhoodFilterFn }],
  ["parcel_size", { visible: true, header: "Lot size", cell: asSqFtAccessor }],
  ["existing_living_area", { cell: asSqFtAccessor }],
  ["existing_floor_area", { cell: asSqFtAccessor }],
  ["existing_FAR", { cell: roundingAccessor }],
  ["num_new_buildings"],
  ["new_building_areas"],
  ["existing_FAR", { cell: roundingAccessor }],
  ["num_new_buildings"],
  ["new_building_areas"],
  ["total_added_building_area"],
  ["garage_con_units"],
  ["garage_con_area"],
  ["total_new_units"],
  ["total_added_area"],
  ["limiting_factor"],
  ["new_FAR"],
  ["max_FAR", { cell: roundingAccessor }],
  ["potential_FAR", { cell: roundingAccessor }],
  ["main_building_poly_area"],
  ["accessory_buildings_polys_area:"],
  ["avail_geom_area", { cell: asSqFtAccessor }],
  ["avail_area_by_FAR", { visible: true, header: "Build sqft", cell: asSqFtAccessor }],
  ["parcel_sloped_area"],
  ["parcel_sloped_ratio"],
  ["total_score"],
  ["cap_ratio_score"],
  ["open_space_score"],
  ["project_size_score"],
  ["can_lot_split"],
  ["new_lot_area_ratio"],
  ["new_lot_area"],
  ["git_commit_hash"],
  ["datetime_ran"],
  ["front_setback"],
  ["br", { visible: true }],
  ["ba", { visible: true }],
  ["price", { visible: true, cell: priceAccessor, filterFn: "inNumberRange" }],
  ["zipcode"],
  ["seendate"],
  ["mlsid"],
  ["mls_floor_area"],
  ["thumbnail"],
  ["listing_url"],
  ["soldprice"],
  ["status", { cell: statusAccessor }],
  ["metadata"], // Need to make this one ALWAYS invisible
])

const columns = colState.map((i: MyColumn) =>
  MyColumnDef.parse({
    ...(i[1] as object),
    accessorKey: i[0],
    header: ((i[1] && i[1]["header"]) as string) || snakeCaseToTitleCase(i[0]),
    enableColumnFilter: i[1] && "filterFn" in (i[1] as object),
  })
) as MyColumnDef[]

// Create query parameters for filtering, depending on type of filter
function columnFiltersToQuery(filters: ColumnFiltersState) {
  const query: { [key: string]: string | number | undefined | boolean } = {}
  filters.forEach((item) => {
    if (Array.isArray(item.value) && item.value.length == 2) {
      // Then it's a min max filter
      query[`${item.id}__gte`] = parseInt(item.value[0] as string) || undefined
      query[`${item.id}__lte`] = parseInt(item.value[1] as string) || undefined
    } else if (typeof item.value === "string" && item.value.length > 0) {
      query[`${item.id}__contains`] = item.value
    } else if (typeof item.value == "boolean") {
      query[`${item.id}`] = item.value
    }
  })
  return query
}

export default function ListingsPage() {
  const [pageSize, setPageSize] = useState<number>(-1)
  const [pageIndex, setPageIndex] = useState<number>(0)
  const [sorting, setSorting] = React.useState<SortingState>([])
  // column filters
  const [columnFilters, setColumnFilters] = useImmer<ColumnFiltersState>([
    { id: "is_mf", value: false },
    { id: "is_tpa", value: false },
    { id: "neighborhood", value: "" },
  ])

  const isMfChecked = columnFilters.find((columnFilter) => columnFilter.id === "is_mf")?.value as boolean
  const isTpaChecked = columnFilters.find((columnFilter) => columnFilter.id === "is_tpa")?.value as boolean
  const isNeighborhoodChecked =
    columnFilters.find((columnFilter) => columnFilter.id === "neighborhood")?.value !== ""

  const onTpaFilterCheck = (e: React.ChangeEvent<HTMLInputElement>) => {
    setColumnFilters((draft) => {
      const index = draft.findIndex((columnFilter) => columnFilter.id === "is_tpa")
      draft[index].value = e.target.checked
    })
  }
  const onMfFilterCheck = (e: ChangeEvent<HTMLInputElement>) => {
    // update is_mf column filter which holds the master state of whether the mf-filter is active
    setColumnFilters((draft) => {
      const isMfFilter = draft.find((columnFilter) => columnFilter.id === "is_mf")
      if (isMfFilter) isMfFilter.value = !isMfFilter.value
    })
  }

  const onNeighborhoodFilterCheck = (e: ChangeEvent<HTMLInputElement>) => {
    setColumnFilters((draft) => {
      const index = draft.findIndex((columnFilter) => columnFilter.id === "neighborhood")
      if (e.target.checked) draft[index].value = "North Park,Normal Heights,Clairemont/Bay Park,City Heights"
      else draft[index].value = ""
    })
  }
  // column visibility
  const initialVisibility = Object.fromEntries(columns.map((x) => [x.accessorKey, x.visible]))
  const [columnVisibility, setColumnVisibility] = useImmer<Record<string, boolean>>(initialVisibility)
  const toggleVisibility = (event: ChangeEvent<HTMLInputElement>) => {
    setColumnVisibility((draft) => {
      draft[event.target.id] = !draft[event.target.id]
    })
  }

  useEffect(() => {
    document.title = "Listings"
    // load initial values of state from local storage
    const jsonSettings = JSON.parse(window.localStorage.getItem("listings_page_settings") as string)
    if (jsonSettings) {
      const settings = ListingsPageLocalStorage.parse(jsonSettings)
      // console.log("Setting local state to", settings)
      setPageSize(settings.pageSize)
      setPageIndex(settings.pageIndex)
      setSorting(settings.sorting as SortingState)
      setColumnFilters(settings.columnFilters as ColumnFiltersState)
    }
  }, [])

  const { data, error, isValidating } = useSWR(
    [
      pageSize > -1 && `${BACKEND_DOMAIN}/api/world/listings`, // if pageSize is undefined, we haven't initialized yet, so wait to fetch
      {
        params: {
          limit: pageSize,
          // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
          offset: pageIndex * pageSize,
          order_by: sorting.length > 0 ? sorting[0].id : undefined,
          asc: sorting.length > 0 ? !sorting[0].desc : undefined,
          ...columnFiltersToQuery(columnFilters),
        },
      },
    ],
    fetcher,
    { use: [swrLaggy] }
  )

  useEffect(() => {
    // update local storage when something changes
    const foo = { pageSize, pageIndex, sorting, columnFilters }
    const settings = ListingsPageLocalStorage.parse(foo)
    // const settings = {
    //   pageSize: pageSize, sorting: sorting, columnFilters: columnFilters,
    // }
    window.localStorage.setItem("listings_page_settings", JSON.stringify(settings))
  }, [pageSize, pageIndex, sorting, columnFilters])

  // flatten data model, removing 'analysis' subsection. Should really refactor this,
  // eg squash on server, or squash in fetcher?
  const listings = data
    ? (data.items.map((item: any) => {
        const listing = {
          ...item,
          // This weird type casting helps squash errors. Only temporary
          ...(item.analysis as object),
        }
        delete listing.analysis
        return listing
      }) as Listing[])
    : []

  const table: Table<Listing> = useReactTable<Listing>({
    data: listings,
    columns,
    state: {
      columnVisibility,
      sorting,
      pagination: {
        pageIndex,
        pageSize,
      },
      columnFilters,
    },
    // onColumnVisibilityChange: setColumnVisibility,
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    manualSorting: true,
    manualPagination: true,
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    pageCount: data ? Math.ceil(data.count / pageSize) : undefined,
    getFilteredRowModel: getFilteredRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    getFacetedRowModel: getFacetedRowModel(),
    getFacetedUniqueValues: getFacetedUniqueValues(),
    getFacetedMinMaxValues: getFacetedMinMaxValues(),
  })

  if (error) {
    console.log("Error", pageSize, error)
    return (
      <div className="md:container px-8 lg:px-16 pt-2">
        <h2>Failed to load</h2>
        <p>
          Try <a href="/user/login">logging in?</a>
        </p>
      </div>
    )
  }

  return (
    <div className={"flex flex-row"}>
      <ListingsMap listings={table.getRowModel().rows.map((row) => row.original)} />
      <div id="tablegrouper" className={"overflow-y-auto max-h-[80vh] grow px-5 overflow-x-auto"}>
        <p>{isValidating ? "Fetching..." : "Up to date"}</p>
        <TablePagination
          table={table}
          pageIndex={pageIndex}
          pageSize={pageSize}
          setPageIndex={setPageIndex}
          setPageSize={setPageSize}
        />
        <div className="flex flex-row justify-left">
          <div className="form-control w-36">
            <label className="cursor-pointer label">
              <input
                type="checkbox"
                checked={isMfChecked}
                className="checkbox checkbox-accent"
                onChange={onMfFilterCheck}
              />
              <span className="label-text">Multifamily-only</span>
            </label>
          </div>
          <div className="form-control w-24">
            <label className="cursor-pointer label">
              <input
                type="checkbox"
                checked={isTpaChecked}
                className="checkbox checkbox-accent"
                onChange={onTpaFilterCheck}
              />
              <span className="label-text">TPA only</span>
            </label>
          </div>
          <div className="form-control w-128">
            <label className="cursor-pointer label">
              <input
                type="checkbox"
                checked={isNeighborhoodChecked}
                className="checkbox checkbox-accent"
                onChange={onNeighborhoodFilterCheck}
              />
              <span className="label-text">Clairemont/Bay Park/North Park/Normal Heights/City Heights only</span>
            </label>
          </div>
        </div>

        <ListingTable table={table} setColumnFilters={setColumnFilters} />

        {/*Render column visibility checkboxes*/}
        <label>
          <input
            {...{
              type: "checkbox",
              readOnly: true,
              // checked: table.getIsAllColumnsVisible(),
              // onChange: table.getToggleAllColumnsVisibilityHandler(),
            }}
          />{" "}
          Toggle All
        </label>
        {Object.keys(initialVisibility).map((columnKey) => {
          return (
            <div key={(columnKey += "viz_chkbx")} className="px-1">
              <label>
                <input
                  id={columnKey}
                  type="checkbox"
                  checked={columnVisibility[columnKey]}
                  onChange={toggleVisibility}
                />{" "}
                {columnKey}
              </label>
            </div>
          )
        })}
      </div>
    </div>
  )
}
