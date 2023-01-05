import * as React from 'react';
import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import useSWR, { useSWRConfig } from 'swr';
import { fetcher, post_csrf } from '../utils/fetcher';
import { ListingHistory } from "../components/ListingHistory";
import { DevScenarios } from "../components/DevScenarios";
import { AnalysisGetResp, AnalysisPostRespSchema } from "../types";

async function redoAnalysis(e, analysisId: number) {
  const fetchResponse = AnalysisPostRespSchema.parse(
    await post_csrf(`/api/analysis/`, {params: { al_id: analysisId }})
  )
  return fetchResponse
}

const asSqFt = (m) => Math.round(m * 3.28 * 3.28).toLocaleString();
const asFt = (m) => Math.round(m * 3.28).toLocaleString();
const oneDay = 1000 * 60 * 60 * 24; // in ms (time units)

function daysAtPrice(date: string | Date) {
  const foundtime = (new Date(date)).getTime()
  const nowtime = Date.now()
  return Math.round((nowtime - foundtime) / oneDay);
}

function showAssumptions(assumptions: object) {
  console.log(assumptions)
  return (<ul className="pl-5">{Object.keys(assumptions).map((assumption, idx) => {
    const as: unknown = assumptions[assumption]
    if (typeof as === 'object') {
      return <li key={idx}>{assumption}: {showAssumptions(as)}</li>
    } else {
      return <li key={idx}>{assumption}:{assumptions[assumption]}</li>
    }
  })
  }</ul>)
}


export function ListingDetailPage() {
  const params = useParams<{ analysisId: string }>();
  // const navigate = useNavigate();
  const [loading, setLoading] = useState<boolean>(false)
  const { data, error } = useSWR<AnalysisGetResp, string>(
    `/api/analysis/${params.analysisId}`,
    fetcher
  );
  const { mutate } = useSWRConfig()
  useEffect(() => {
    if (data) {
      document.title = data.details.address
    }
  }, [data]);
  if (error) return <div>ListingDetailPage failed its AJAX call. {error}</div>;
  if (!data) return <div>loading...</div>;

  async function onRedoAnalysis(e) {
    setLoading(true)
    const res = await redoAnalysis(e, Number(params.analysisId));
    setLoading(false)
    return mutate(`/api/analysis/${res.analysisId}`)

    // navigate('/analysis/' + res.analysisId, { replace: true });
  }

  console.log(data);
  return (
    <>
      {data.details.messages &&
        data.details.messages.warning.map((warn, idx) => (
          <div key={idx} className="alert alert-warning shadow-lg py-1 rounded-lg">
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
          <h1 className={'hidden print:block'}><a className='link text-darkblue'
                                                  href={window.location.href}>
            {data.details.address}</a></h1>
          <h1 className={'print:hidden'}>
            {loading && <progress className="progress w-36"/>}
            {!loading && data.details.address}
          </h1>
          {data.is_tpa && <div className="badge badge-primary">TPA</div>}
          {data.is_mf && <div className="badge badge-accent ml-2">Multifam</div>}
          <p>{data.listing.neighborhood}</p>
          <p>APN: {data.apn}</p>
          {/*<p>Build Sq Ft by FAR: {asSqFt(data.avail_area_by_FAR)}</p>*/}
          {/*<p>Sq Ft open area: {asSqFt(data.avail_geom_area)}</p>*/}
          <p>Zone: {data.zone}</p>
          <p>Walk score: XX</p>
          <div className='divider'></div>
          <h2>Units and Rents</h2>
          <p>Existing unit count: {data.details.existing_units_with_rent?.length}</p>
          <p>Assumed units and rents:</p>
          <ul>
            {data.details.existing_units_with_rent?.map((unit, idx) => (
                <li key={idx}>{unit[0].br} BR, {unit[0].ba} BA: ${unit[1].toLocaleString()}</li>
              )
            )}
            <li></li>
          </ul>
          <p>({data.details.re_params?.existing_unit_rent_percentile}th percentile rents)</p>

        </div>
        <div>
          <h1>${data.listing.price ? data.listing.price.toLocaleString() : "-- off-market"}</h1>
          <h2>{daysAtPrice(data.listing.founddate)} days at this price</h2>
          <p>{asSqFt(data.details.existing_living_area.toLocaleString())} sq ft</p>
          <p>{data.listing.br} BR</p>
          <p>{data.listing.ba} BA</p>
          <p>{data.details.garages + data.details.carports} garage</p>
        </div>
        <div className={'justify-end'}>
          <img src={data.listing.thumbnail} className="w-72"/>
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
          <img src={`https://r2-image-worker.upzone.workers.dev/buildings-${data.apn}-${data.salt}`}/>
        </div>
        <div className="flex-auto">
          <h2 className="font-semibold text-center">Usable land analysis</h2>
          <img src={`https://r2-image-worker.upzone.workers.dev/cant_build-${data.apn}-${data.salt}`}/>
          <div
            tabIndex={0}
            className="collapse collapse-arrow w-60 border border-base-300 bg-base-100 min-h-0 object-right float-right"
          >
            <input type="checkbox" style={{ minHeight: 0 }}/>
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

        {/* Google maps embed*/}
        <iframe
          width="500"
          height="400"
          frameBorder={0}
          style={{ border: 0 }}
          referrerPolicy="no-referrer-when-downgrade"
          src={`https://www.google.com/maps/embed/v1/place?key=AIzaSyDeucEjPuJ4M6i7FSxKKO-MHMp_007Y7ds&q=${data.details.address} San Diego`}
          allowFullScreen
        ></iframe>

        {/* Lot split overview */}
        {false && data.details.can_lot_split && (
          <div>
            <h2 className="font-semibold text-center">Lot Split:</h2>
            <img src={`/temp_computed_imgs/lot-splits/${data.apn}.jpg`}/>
          </div>
        )}
      </div>

      {/* Show cards for FAR and geometry calculation */}
      <div className="flex flex-row w-full justify-left space-x-4 items-top">
        <div className="card bg-base-100 shadow-md">
          <div className="card-body">
            <h2 className="card-title">FAR calculations</h2>
            <p>Current FAR: {data.details.existing_FAR.toFixed(2)}</p>
            <p>Max FAR: {data.details.max_FAR.toFixed(2)}</p>
            <p>Parcel size: {asSqFt(data.details.parcel_size)}</p>
            <p>
              Buildable sq ft based on FAR: {asSqFt(data.details.avail_area_by_FAR)}
            </p>
            {/*<div className="card-actions justify-end">*/}
            {/*  <button className="btn btn-primary">Buy Now</button>*/}
            {/*</div>*/}
          </div>
        </div>
        <div className="card bg-base-100 shadow-md">
          <div className="card-body">
            <h2 className="card-title">Geometry calculations</h2>
            <p>Buildable area by geometry: {asSqFt(data.details.avail_geom_area)}</p>
          </div>
        </div>
        <div className="card bg-base-100 shadow-md">
          <div className="card-body">
            <h2 className="card-title">Listing history</h2>
            <ListingHistory mlsid={data.listing.mlsid}/>
          </div>
        </div>
      </div>
      {/* Show development scenarios*/}
      <DevScenarios scenarios={data.dev_scenarios}></DevScenarios>
      <div className="divider"></div>


      <h1>Assumptions</h1>
      {data.details.re_params && showAssumptions(data.details.re_params)}

      <h1 className='mt-5'>Details</h1>
      <p> These are present primarily for debugging. Anything useful should be sent up above this section.</p>
      <pre>
      {Object.keys(data).map((key) => {
        return (
          <p key={key}>
            {key}:{' '}
            {JSON.stringify(data[key], null, 2).replace(/^"|"$/g, '')}
          </p>
        );
      })}
      </pre>
    </>
  );
}
