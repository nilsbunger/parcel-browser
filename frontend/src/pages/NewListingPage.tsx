import * as React from 'react';
import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import useSWR, { useSWRConfig } from 'swr';
import { fetcher, post_csrf } from '../utils/fetcher';
import { ErrorBoundary } from "react-error-boundary";

export function NewListingPage() {

  const [addressSearch, setAddressSearch] = useState('');
  const [err, setErr] = useState('');
  const [loading, setLoading] = useState(false)

  const { mutate } = useSWRConfig()
// This will make a call every time that addressSearch is mutated, which could
  // result in many network calls. May need to change later
  const { data, error } = useSWR(
    `/api/address-search/${addressSearch}`,
    fetcher
  );
  const handleAddressSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    setAddressSearch(e.target.value);
  };

  const handleSearchSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    console.log(e)
    console.log("SUBMITTING")
    setLoading(true)
    const fetchResponse = await post_csrf(`/api/analysis/`, { apn: data.apn })
    await mutate(`/api/address-search/${addressSearch}`)
    setLoading(false)
    return
  }


  return (
    <>
      <h1>Analyze an Address</h1>
      <ErrorBoundary fallback={<div>Error handling address search</div>}>
        <form onSubmit={handleSearchSubmit}>
          <input
            className="border border-gray-700"
            type="text"
            value={addressSearch}
            onChange={handleAddressSearch}
          />{'  '}
          {data?.apn ? !data.analyzed_listing &&
              <button className={'btn btn-sm btn-primary' + (loading ? ' loading':'')} type="submit">Analyze...</button> : ''}
        </form>
        {data?.apn ? (
          <>
            <p>FOUND: {data.apn} {data.address}.</p>
            {data.analyzed_listing && <p>
                Analysis={data.analyzed_listing}. {'  '}
                <Link className="link link-primary" to={`/analysis/${data.analyzed_listing}`}>Go to detail page</Link>
            </p>}
            {/*<button onClick={handleAddListing}>Add listing</button>*/}

          </>
        ) : (
          <p>{JSON.stringify(data)}</p>
        )}
      </ErrorBoundary>
      <p>{err}</p>
    </>
  );
}
