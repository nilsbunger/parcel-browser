import * as React from "react"
import { useCallback, useEffect } from "react"

import { Anchor, ScrollArea, Table } from "@mantine/core"
import { Link, useNavigate } from "react-router-dom"
import useSWR from "swr"
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
  const navigate = useNavigate()
  useEffect(() => {
    document.title = "Properties"
    // load initial values of state from local storage
  }, [])

  // get property profiles
  const { data, error, isValidating } = useSWR(`/api/properties/profiles`, fetcher)
  console.log("isValidating", isValidating)
  console.log("data", data)

  // const data = [{ id: 1, address: "555 main st" }]

  // const { classes, theme } = useStyles();

  const onRowClick = useCallback((e: React.MouseEvent<HTMLTableRowElement, MouseEvent>) => {
    const id = e.currentTarget.getAttribute("data-id")
    console.log("row click:", e)
    console.log("id", id)
    navigate(`${id}`)
    // e.preventDefault()
    // if (id) {
    //   router.push(`/props/${id}`)
    // }
  }, [])

  if (error) return <div>failed to load properties list</div>
  if (isValidating) return <div>loading...</div>

  const rows = data.map((row: any) => {
    return (
      <tr
        key={row.id}
        data-id={row.id}
        onClick={onRowClick}
        className="cursor-pointer border-primarylight hover:border-solid"
      >
        <td>{row.id}</td>
        <td>
          {row.address.street_addr}, {row.address.city}, {row.address.state} {row.address.zip}
        </td>
        <td>{row.legal_entity?.name}</td>
      </tr>
    )
  })

  return (
    <ScrollArea>
      <div className="flex flex-row">
        <div className="flex-grow text-right">
          <Link to={{ pathname: `/bov/1` }} className="btn btn-primary btn-sm mr-4">
            BOV example
          </Link>
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
            <th>Entity</th>
          </tr>
        </thead>
        <tbody>{rows}</tbody>
      </Table>
    </ScrollArea>
  )
}
