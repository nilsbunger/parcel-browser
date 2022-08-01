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
      <h1>Hello world from pages/ListingDETAILPage.tsx!</h1>
      <p>{JSON.stringify(data)}</p>
    </>
  );
}
