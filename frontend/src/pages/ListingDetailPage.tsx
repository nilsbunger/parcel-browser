import React from 'react';
import { useParams } from 'react-router-dom';
import useSWR from 'swr';
import { fetcher } from '../utils/fetcher';

export function ListingDetailPage({}) {
  const params = useParams();
  const { data, error } = useSWR(
    `/dj/api/listings/${params.listingId}`,
    fetcher
  );

  if (error) return <div>failed to load</div>;
  if (!data) return <div>loading...</div>;

  return (
    <>
      <h1>{data.address}</h1>
      <h2>{params.listingId}</h2>
      <img src={data.thumbnail} />
      <h3>New Buildings analysis</h3>
      <img src={`/temp_computed_imgs/new-buildings/${params.listingId}.jpg`} />
      {data.can_lot_split && (
        <>
          <h3>Lot Split:</h3>
          <img src={`/temp_computed_imgs/lot-splits/${params.listingId}.jpg`} />
        </>
      )}
      {Object.keys(data).map((key) => {
        return (
          <p>
            {key}: {data[key]}
          </p>
        );
      })}
    </>
  );
}
