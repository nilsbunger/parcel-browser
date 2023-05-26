import * as React from "react"
import { useCallback, useEffect } from "react"

import { Anchor, ScrollArea, Table } from "@mantine/core"
import { Link, useParams } from "react-router-dom"
import useSWR from "swr"
import { fetcher } from "../utils/fetcher"
import CollapsibleTree from "../components/CollapsibleTree"

export default function PropertyDetailPage() {
  const { id } = useParams<{ id: string }>()

  // get property profiles
  const { data, error, isValidating } = useSWR(`/api/properties/profiles/${id}`, fetcher)
  const addr: string = data?.address.street_addr || "Loading..."
  useEffect(() => {
    document.title = addr
    // load initial values of state from local storage
  }, [addr])

  // const data = [{ id: 1, address: "555 main st" }]

  if (error) return <div>failed to load property</div>
  if (isValidating) return <div>loading...</div>

  return (
    <div>
      <h1>Property detail page</h1>
      <p>{addr}</p>
      <p>
        {data.address.city}, {data.address.state} {data.address.zip}
      </p>

      <div className="py-10">
        <hr />
      </div>
      <CollapsibleTree data={data} />
    </div>
  )
}
