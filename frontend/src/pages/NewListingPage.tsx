import * as React from 'react';
import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import useSWR from 'swr';
import { fetcher } from '../utils/fetcher';
import { ErrorBoundary } from "react-error-boundary";

export function NewListingPage() {
  const navigate = useNavigate();

  const [addressSearch, setAddressSearch] = useState('');
  const [addAsListing, setAddAsListing] = useState(false);
  const [err, setErr] = useState('');

  // This will make a call every time that addressSearch is mutated, which could
  // result in many network calls. May need to change later
  const { data, error } = useSWR(
    `/api/address-search/${addressSearch}`,
    fetcher
  );
  const handleAddressSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    setAddressSearch(e.target.value);
  };

  const handleSearchSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    console.log (e)
    console.log("SUBMITTING")
  }

    const fetchResponse = await fetch(`/dj/api/listings`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        apn: data.apn,
        add_as_listing: addAsListing,
        redo_analysis: false,
      }),
    });
    const res = await fetchResponse.json();

    if (res.error) {
      console.log('An error has occurred');
      setErr(res.error);
    }
    if (res.analysis_id) {
      console.log('Redirecting');
      navigate(`/analysis/${res.analysis_id}`);
    }
  };

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
          {data?.apn? !data.analyzed_listing && <button className='btn btn-sm btn-primary' type="submit">Analyze...</button> : ''}
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
