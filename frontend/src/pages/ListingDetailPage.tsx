import * as React from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import useSWR from 'swr';
import { fetcher } from '../utils/fetcher';

async function getAnalysis(e, apn) {
  const fetchResponse = await fetch(`/dj/api/listings`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      apn: apn,
      add_as_listing: false,
      redo_analysis: true,
    }),
  });
  return fetchResponse.json();
}

const asSqFt = (m) => Math.round(m * 3.28 * 3.28);
const asFt = (m) => Math.round(m * 3.28);

export function ListingDetailPage({}) {
  const params = useParams();
  let navigate = useNavigate();
  const { data, error } = useSWR(
    `/dj/api/analysis/${params.analysisId}`,
    fetcher
  );
  if (error) return <div>ListingDetailPage failed its AJAX call. {error}</div>;
  if (!data) return <div>loading...</div>;

  async function onRedoAnalysis(e) {
    const res = await getAnalysis(e, data.apn);
    navigate('/analysis/' + res.analysis_id, { replace: true });
  }

  console.log(data);
  return (
    <>
      {data.messages &&
        data.messages.warning.map((warn) => (
          <div className="alert alert-warning shadow-lg py-1 rounded-lg">
            <div>
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="stroke-current flex-shrink-0 h-6 w-6"
                fill="none"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                />
              </svg>
              <span>{warn}</span>
            </div>
          </div>
        ))}
      {/*Show building and land plots */}
      <div className="flex flex-row w-full justify-between items-top mt-5">
        <div>
          <h1>{data.address}</h1>
          <p>{data.neighborhood}</p>
          <p>APN: {data.apn}</p>
          <p>Build Sq Ft by FAR: {asSqFt(data.avail_area_by_FAR)}</p>
          <p>Sq Ft open area: {asSqFt(data.avail_geom_area)}</p>
          <p>Zone: {data.zone}</p>
        </div>
        <div>
          <h1>${data.price}</h1>
          <p>{asSqFt(data.existing_living_area)} sq ft</p>
          <p>{data.br} BR</p>
          <p>{data.ba} BA</p>
          <p>{data.garages + data.carports} garage</p>
        </div>
        <div className={'justify-end'}>
          <img src={data.thumbnail} className="min-w-[25%] min-h-[25%]" />
          <button
            className="btn btn-secondary btn-xs mt-3"
            onClick={onRedoAnalysis}
          >
            Re-analyze
          </button>
        </div>
      </div>
      <div className="flex flex-row mt-6">
        <div className="flex-auto">
          <h2 className="font-semibold text-center">Plot analysis</h2>
          <img src={`/temp_computed_imgs/new-buildings/${data.apn}.jpg`} />
        </div>
        <div className="flex-auto">
          <h2 className="font-semibold text-center">Usable land analysis</h2>
          <img src={`/temp_computed_imgs/cant-build/${data.apn}.jpg`} />
          <div
            tabIndex={0}
            className="collapse collapse-arrow w-60 border border-base-300 bg-base-100 min-h-0 object-right float-right"
          >
            <input type="checkbox" style={{ minHeight: 0 }} />
            <div className={'collapse-title min-h-0 p-2 after:!top-3 '}>
              <p>Legend</p>
            </div>
            <div className={'collapse-content'}>
              <p>Red: Too steep</p>
              <p>Cyan: Buffered buildings</p>
              <p>Orange: Setbacks</p>
              <p>Green: Flag lot</p>
            </div>
          </div>
        </div>

        <iframe
          width="450"
          height="250"
          frameBorder={0}
          style={{ border: 0 }}
          referrerPolicy="no-referrer-when-downgrade"
          src={`https://www.google.com/maps/embed/v1/place?key=AIzaSyDeucEjPuJ4M6i7FSxKKO-MHMp_007Y7ds&q=${data.address} San Diego`}
          allowFullScreen
        ></iframe>

        {false && data.can_lot_split && (
          <div>
            <h2 className="font-semibold text-center">Lot Split:</h2>
            <img src={`/temp_computed_imgs/lot-splits/${data.apn}.jpg`} />
          </div>
        )}
      </div>

      {/* Show cards for FAR and geometry calculation */}
      <div className="flex flex-row w-full justify-left space-x-4 items-top">
        <div className="card bg-base-100 shadow-xl">
          <div className="card-body">
            <h2 className="card-title">FAR calculations</h2>
            <p>Current FAR: {data.existing_FAR.toFixed(2)}</p>
            <p>Max FAR: {data.max_FAR.toFixed(2)}</p>
            <p>Parcel size: {asSqFt(data.parcel_size)}</p>
            <p>
              Buildable sq ft based on FAR: {asSqFt(data.avail_area_by_FAR)}
            </p>
            {/*<div className="card-actions justify-end">*/}
            {/*  <button className="btn btn-primary">Buy Now</button>*/}
            {/*</div>*/}
          </div>
        </div>
        <div className="card bg-base-100 shadow-xl">
          <div className="card-body">
            <h2 className="card-title">Geometry calculations</h2>
            <p>Buildable area by geometry: {asSqFt(data.avail_geom_area)}</p>
            {/*<div className="card-actions justify-end">*/}
            {/*  <button className="btn btn-primary">Buy Now</button>*/}
            {/*</div>*/}
          </div>
        </div>
      </div>
      <h2>Details:</h2>
      {Object.keys(data).map((key) => {
        return (
          <p key={key}>
            {key}:{' '}
            {typeof data[key] == 'object'
              ? JSON.stringify(data[key])
              : data[key]}
          </p>
        );
      })}
    </>
  );
}
