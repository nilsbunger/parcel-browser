import * as React from "react"
import { useCallback, useEffect } from "react"

import { Anchor, ScrollArea, Table } from "@mantine/core"
import { Link, useParams } from "react-router-dom"
import useSWR from "swr"
import { BACKEND_DOMAIN } from "../constants"
import { fetcher } from "../utils/fetcher"
import CollapsibleTree from "../components/CollapsibleTree"

export default function BovDetailPage() {
  const { id } = useParams<{ id: string }>()
  console.log("React version:", React.version)
  // get property profiles
  // const { data, error, isValidating } = useSWR(`${BACKEND_DOMAIN}/api/properties/profiles/${id}`, fetcher)
  // const addr: string = data?.address.street_addr || "Loading..."
  useEffect(() => {
    document.title = `BOV ${id}`
    // load initial values of state from local storage
  }, [id])

  // const data = [{ id: 1, address: "555 main st" }]

  // if (error) return <div>failed to load BOV</div>
  // if (isValidating) return <div>loading...</div>

  return (
    <div>
      <h1>BOV detail page</h1>
    </div>
  )
}
