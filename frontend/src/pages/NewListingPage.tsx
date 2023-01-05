import * as React from 'react';
import { useState } from 'react';
import { Link } from 'react-router-dom';
import useSWR, { useSWRConfig } from 'swr';
import { fetcher, post_csrf } from '../utils/fetcher';
import { ErrorBoundary } from "react-error-boundary";
import { AddressSearchGetResp, AnalysisPostRespSchema } from "../types";


export function NewListingPage() {

  const [addressSearch, setAddressSearch] = useState('');
  const [err, setErr] = useState('');
  const [loading, setLoading] = useState(false)

  const { mutate } = useSWRConfig()
// This will make a call every time that addressSearch is mutated, which could
  // result in many network calls. May need to change later
  const { data, error } = useSWR<AddressSearchGetResp, string>(
    `/api/address-search/${addressSearch}`,
    fetcher
  );
  const handleAddressSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    setAddressSearch(e.target.value);
  };

  const handleAnalyzeSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    if ("apn" in data) {
      setLoading(true)
      const fetchResponse = AnalysisPostRespSchema.parse(
        await post_csrf(`/api/analysis/`, {params:{ apn: data.apn }})
      )
      await mutate(`/api/address-search/${addressSearch}`)
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
            value={addressSearch}
            onChange={handleAddressSearch}
          />{'  '}
          {data && ("apn" in data) && !data.analyzed_listing &&
              <button className={'btn btn-sm btn-primary' + (loading ? ' loading' : '')}
                      type="submit">Analyze...</button> }
        </form>
        {data && ("apn" in data) && (
          <>
            <p>FOUND: {data.apn} {data.address}.</p>
            {data.analyzed_listing && <p>
                Analysis={data.analyzed_listing}. {'  '}
                <Link className="link link-primary" to={`/analysis/${data.analyzed_listing}`}>Go to detail page</Link>
            </p>}
          </>
        )}
        {data && ("error" in data) && <p>{data.error}</p>}
      </ErrorBoundary>
      <p>{err}</p>
    </>
  );
}
