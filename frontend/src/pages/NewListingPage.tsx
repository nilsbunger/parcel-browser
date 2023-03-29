import * as React from "react"
import { useState } from "react"
import { Link } from "react-router-dom"
import useSWR, { useSWRConfig } from "swr"
import { apiRequest, fetcher } from "../utils/fetcher"
import { ErrorBoundary } from "react-error-boundary"
import { AddressSearchGetResp, AnalysisPostRespSchema } from "../types"

export default function NewListingPage() {
  const [address, setAddress] = useState("")
  const [err, setErr] = useState("")
  const [loading, setLoading] = useState(false)

  const { mutate } = useSWRConfig()
  // This will make a call every time that addressSearch is mutated, which could
  // result in many network calls. May need to change later
  const { data: addrSearchData, error } = useSWR<AddressSearchGetResp, string>(
    address.length >= 3 ? `api/world/address-search/${address}` : null,
    fetcher
  )
  const handleAddressSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    setAddress(e.target.value)
  }

  const handleAnalyzeSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    // @ts-ignore  -- fix this later
    if ("apn" in addrSearchData) {
      setLoading(true)
      const { data, errors, message } = await apiRequest<typeof AnalysisPostRespSchema>(`api/world/analysis/`, {
        ResponseCls: AnalysisPostRespSchema,
        isPost: false,
        params: { apn: addrSearchData.apn },
      })
      if (!errors) {
        await mutate(`api/world/address-search/${address}`)
      }
      setLoading(false)
    }
    return
  }
  return (
    <>
      <h1>Analyze an Address</h1>
      <ErrorBoundary fallback={<div>Error handling address search</div>}>
        <form onSubmit={handleAnalyzeSubmit}>
          <input
            className="border border-gray-700"
            type="text"
            value={address}
            onChange={handleAddressSearch}
          />
          {"  "}
          {addrSearchData && "apn" in addrSearchData && !addrSearchData.analyzed_listing && (
            <button className={"btn btn-sm btn-primary" + (loading ? " loading" : "")} type="submit">
              Analyze...
            </button>
          )}
        </form>
        {addrSearchData && "apn" in addrSearchData && (
          <>
            <p>
              FOUND: {addrSearchData.apn} {addrSearchData.address}.
            </p>
            {addrSearchData.analyzed_listing && (
              <p>
                Analysis={addrSearchData.analyzed_listing}. {"  "}
                <Link className="link link-primary" to={`/analysis/${addrSearchData.analyzed_listing}`}>
                  Go to detail page
                </Link>
              </p>
            )}
          </>
        )}
        {addrSearchData && "error" in addrSearchData && <p>{addrSearchData.error}</p>}
      </ErrorBoundary>
      <p>{err}</p>
    </>
  )
}
