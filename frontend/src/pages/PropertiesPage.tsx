import * as React from "react"
import { useCallback, useEffect } from "react"

import { Anchor, ScrollArea, Table } from "@mantine/core"
import { Link } from "react-router-dom"
import useSWR from "swr"
import { BACKEND_DOMAIN } from "../constants"
import { fetcher } from "../utils/fetcher"

// const useStyles = createStyles((theme) => ({
//   progressBar: {
//     '&:not(:first-of-type)': {
//       borderLeft: `${rem(3)} solid ${
//         theme.colorScheme === 'dark' ? theme.colors.dark[7] : theme.white
//       }`,
//     },
//   },
// }));

interface PropertiesProps {
  data: {
    title: string
    author: string
    year: number
    reviews: { positive: number; negative: number }
  }[]
}

export default function PropertiesPage() {
  useEffect(() => {
    document.title = "Properties"
    // load initial values of state from local storage
  }, [])

  // get property profiles
  const { data, error, isValidating } = useSWR(`${BACKEND_DOMAIN}/api/properties/profiles`, fetcher)
  console.log("isValidating", isValidating)
  console.log("data", data)

  if (error) return <div>failed to load properties list</div>
  if (isValidating) return <div>loading...</div>

  // const data = [{ id: 1, address: "555 main st" }]

  // const { classes, theme } = useStyles();

  const onRowClick = useCallback((e: React.MouseEvent<HTMLTableRowElement, MouseEvent>) => {
    const id = e.currentTarget.getAttribute("data-id")
    console.log("row click:", e)
    console.log("id", id)
    // e.preventDefault()
    // if (id) {
    //   router.push(`/props/${id}`)
    // }
  }, [])

  const rows = data.map((row) => {
    return (
      <tr
        key={row.id}
        data-id={row.id}
        onClick={onRowClick}
        className="cursor-pointer border-primarylight hover:border-solid"
      >
        <td>{row.id}</td>
        <td>{row.address}</td>
      </tr>
    )
  })

  return (
    <ScrollArea>
      <div className="flex flex-row">
        <div className="flex-grow text-right">
          <Link to={{ pathname: `/properties/new` }} className="btn btn-primary btn-sm">
            ADD...
          </Link>

          {/*<Anchor component="a" type="button" href="/properties/new" className="">ADD...</Anchor>*/}
        </div>
      </div>
      <Table sx={{ minWidth: 800 }} verticalSpacing="xs">
        <thead>
          <tr>
            <th>ID</th>
            <th>Address</th>
          </tr>
        </thead>
        <tbody>{rows}</tbody>
      </Table>
    </ScrollArea>
  )
}

// const table: Table<Listing> = useReactTable<Listing>({
//   data: listings,
//   columns,
//   state: {
//     columnVisibility,
//     sorting,
//     pagination: {
//       pageIndex,
//       pageSize,
//     },
//     columnFilters,
//   },
//   // onColumnVisibilityChange: setColumnVisibility,
//   onSortingChange: setSorting,
//   getCoreRowModel: getCoreRowModel(),
//   getSortedRowModel: getSortedRowModel(),
//   manualSorting: true,
//   manualPagination: true,
//   pageCount: data ? Math.ceil(data.count / pageSize) : null,
//   getFilteredRowModel: getFilteredRowModel(),
//   getPaginationRowModel: getPaginationRowModel(),
//   getFacetedRowModel: getFacetedRowModel(),
//   getFacetedUniqueValues: getFacetedUniqueValues(),
//   getFacetedMinMaxValues: getFacetedMinMaxValues(),
// })
//
// if (error)
//   return (
//     <div className="md:container px-8 lg:px-16 pt-2">
//       <h2>Failed to load</h2>
//     </div>
//   )
//
// return (
//   <div className={"flex flex-row"}>
//     <ListingsMap listings={table.getRowModel().rows.map((row) => row.original)} />
//     <div id="tablegrouper" className={"overflow-y-auto max-h-[80vh] grow px-5 overflow-x-auto"}>
//       <p>{isValidating ? "Fetching..." : "Up to date"}</p>
//       <TablePagination
//         table={table}
//         pageIndex={pageIndex}
//         pageSize={pageSize}
//         setPageIndex={setPageIndex}
//         setPageSize={setPageSize}
//       />
//
//       <ListingTable table={table} setColumnFilters={setColumnFilters} />
//
//     </div>
//   </div>
// )
