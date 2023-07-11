import * as React from "react"
import { useEffect } from "react"
import { useParams } from "react-router-dom"
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
        <h1>{addr}</h1>
        <h3>
          {data.address.city}, {data.address.state} {data.address.zip}
        </h3>

      <div className="py-10">
        <hr/>
      </div>
      <CollapsibleTree data={data}/>
    </div>
  )
}
