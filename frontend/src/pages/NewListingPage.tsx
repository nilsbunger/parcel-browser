import React from 'react';
import { useNavigate } from 'react-router-dom';
import useSWR, { useSWRConfig } from 'swr';
import { fetcher } from '../utils/fetcher';

export function NewListingPage() {
  const navigate = useNavigate();

  const [addressSearch, setAddressSearch] = React.useState('');
  const [err, setErr] = React.useState('');

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
      }),
    });
    const res = await fetchResponse.json();
    console.log(res);

    if (res.error) {
      console.log('An error has occured');
      setErr(res.error);
    }
    if (res.msg == 'success') {
      console.log('Successfully added listing');
      navigate(`/listings/${res.apn}`);
    }
  };

  return (
    <>
      <h1>Manually add a listing</h1>
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
