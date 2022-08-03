import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import useSWR, { useSWRConfig } from 'swr';
import { fetcher } from '../utils/fetcher';

export function NewListingPage() {
  const navigate = useNavigate();

  const [addressSearch, setAddressSearch] = useState('');
  const [addAsListing, setAddAsListing] = useState(false);
  const [err, setErr] = useState('');

  // This will make a call every time that addressSearch is mutated, which could
  // result in many network calls. May need to change later
  const { data, error } = useSWR(
    `/dj/api/address-search/${addressSearch}`,
    fetcher
  );

  const handleAddressSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    setAddressSearch(e.target.value);
  };

  const handleSearchSubmit = (e: React.SyntheticEvent) => {
    e.preventDefault();
    console.log('Submitted');
  };

  const handleAddListing = async () => {
    // Ensure that we have an APN
    if (!data?.apn) {
      console.log('No APN. Cannot add listing');
      return;
    }

    const fetchResponse = await fetch(`/dj/api/listings`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        apn: data.apn,
        add_as_listing: addAsListing,
      }),
    });
    const res = await fetchResponse.json();
    console.log(res);

    if (res.error) {
      console.log('An error has occured');
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
      <p>
        Important note: After you get redirected to the new listing, please
        restart the server for images to load properly.
      </p>
      <form onSubmit={handleSearchSubmit}>
        <input
          className="border border-gray-700"
          type="text"
          value={addressSearch}
          onChange={handleAddressSearch}
        />
        <label>
          <input
            type="checkbox"
            checked={addAsListing}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
              setAddAsListing(e.target.checked)
            }
          />
          Add as a listing
        </label>
      </form>
      {data?.apn ? (
        <>
          <p>APN FOUND! {data.apn}</p>
          <button onClick={handleAddListing}>Add listing</button>
        </>
      ) : (
        <p>{JSON.stringify(data)}</p>
      )}
      <p>{err}</p>
    </>
  );
}
