import React from 'react';
import {useNavigate, useParams} from 'react-router-dom';
import useSWR from 'swr';
import {fetcher} from '../utils/fetcher';


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

export function ListingDetailPage({}) {
  const params = useParams();
  let navigate = useNavigate();
  const {data, error} = useSWR(
    `/dj/api/analysis/${params.analysisId}`,
    fetcher
  );
  if (error) return <div>ListingDetailPage failed its AJAX call. {error}</div>;
  if (!data) return <div>loading...</div>;

  async function onRedoAnalysis(e) {
    const res = await getAnalysis (e, data.apn);
    navigate("/analysis/"+res.analysis_id, { replace: true });
  }

  return (
    <>
      <div className="flex flex-row w-full justify-between items-center">

        <div>
          <h1>{data.address}</h1>
          <h2>APN: {data.apn}</h2>
        </div>
        <div className="justify-end">
          <button className='btn btn-secondary btn-xs'
                  onClick={onRedoAnalysis}>Re-analyze</button>
        </div>
      </div>
      <img src={data.thumbnail} className="min-w-[25%] min-h-[25%]"/>
      <div className="flex flex-row mt-6">
        <div className='flex-auto'>
          <h2 className="font-semibold text-center">Plot analysis</h2>
          <img src={`/temp_computed_imgs/new-buildings/${data.apn}.jpg`}/>
        </div>
        <div className='flex-auto'>
          <h2 className="font-semibold text-center">Usable land analysis</h2>
          <img src={`/temp_computed_imgs/cant-build/${data.apn}.jpg`}/>
          <div tabIndex={0} className="collapse collapse-arrow w-60 border border-base-300 bg-base-100 min-h-0 object-right float-right">
            <input type="checkbox" style={{minHeight:0}}/>
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
        {data.can_lot_split && (
          <div>
            <h2 className="font-semibold">Lot Split:</h2>
            <img src={`/temp_computed_imgs/lot-splits/${data.apn}.jpg`}/>
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
