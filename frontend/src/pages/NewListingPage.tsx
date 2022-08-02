import React from 'react';
import useSWR, { useSWRConfig } from 'swr';
import { fetcher } from '../utils/fetcher';

export function NewListingPage() {
  const [addressSearch, setAddressSearch] = React.useState('');

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

  const handleAddListing = () => {
    console.log('Do something here!');
  };

  return (
    <>
      <h1>Manually add a listing</h1>
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
    </>
  );
}
