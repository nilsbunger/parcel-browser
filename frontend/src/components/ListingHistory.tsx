import useSWR from "swr"
import { fetcher } from "../utils/fetcher"
import * as React from "react"

export function ListingHistory({ mlsid }) {
  const { data, error } = useSWR(`/api/listinghistory?mlsid=${mlsid}`, fetcher)
  if (error) return <div>ListingHistory failed its AJAX call. {JSON.stringify(error)}</div>
  if (!data) return <div>loading...</div>
  return (
    <div className={"overflow-x-auto"}>
      <table className={"table"}>
        <thead>
          <tr>
            <th>Date</th>
            <th>Price</th>
            <th></th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {data.map((l) => (
            <tr key={l.founddate}>
              <td>{l.founddate.substring(0, 10)}</td>
              <td>
                ${l.price?.toLocaleString()} {l.status === "OFFMARKET" ? "Off-market" : ""}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
