import React from 'react';
import { useParams } from 'react-router-dom';
import useSWR from 'swr';
import { fetcher } from '../utils/fetcher';

export function ListingDetailPage({}) {
  const params = useParams();
  const { data, error } = useSWR(
    `/dj/api/analysis/${params.analysisId}`,
    fetcher
  );

  if (error) return <div>failed to load</div>;
  if (!data) return <div>loading...</div>;

  return (
    <>
      <h1 className="text-4xl">{data.address}</h1>
      <h2>APN: {data.apn}</h2>
      <img src={data.thumbnail} className="min-w-[25%] min-h-[25%]" />
      <div className="flex flex-row flex-wrap mt-6">
        <div>
          <h2 className="font-semibold">New Buildings analysis</h2>
          <img src={`/temp_computed_imgs/new-buildings/${data.apn}.jpg`} />
        </div>
        <div>
          <h2 className="font-semibold">Unbuildable land analysis</h2>
          <h3>Legend info:</h3>
          <p>Red: Too steep</p>
          <p>Cyan: Buffered buildings</p>
          <p>Orange: Setbacks</p>
          <p>Green: Flagpole part of the lot</p>
          <img src={`/temp_computed_imgs/cant-build/${data.apn}.jpg`} />
        </div>
        {data.can_lot_split && (
          <div>
            <h2 className="font-semibold">Lot Split:</h2>
            <img src={`/temp_computed_imgs/lot-splits/${data.apn}.jpg`} />
          </div>
        )}
      </div>
      <h2>Details:</h2>
      {Object.keys(data).map((key) => {
        return (
          <p key={key}>
            {key}: {data[key]}
          </p>
        );
      })}
    </>
  );
}
