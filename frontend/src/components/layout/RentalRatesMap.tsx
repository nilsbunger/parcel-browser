import * as React from 'react';
import { MapContainer, Marker, TileLayer, Tooltip } from 'react-leaflet';
import { RentLocationRate } from '../../types';
import { ErrorBoundary } from 'react-error-boundary'

type Props = { rentalRates: RentLocationRate[] };

const asSqFt = (m) => Math.round(m * 3.28 * 3.28);

const topCheck = (text, state, onChangeFn) => (
  <div key={text} className="form-control w-36">
    <label className="cursor-pointer label justify-start gap-3"> {/* Label is actually a flex parent */}
      <input type="radio" value={state == text ? "true" : ""} name="unitfilter" className="checkbox checkbox-accent"
             onChange={(e) => onChangeFn(e, text)}/>
      <span className="label-text text-left">{text}</span>
    </label>
  </div>
)

function RentalRatesMap({ rentalRates }: Props) {
  // const [checks, setChecks] = React.useState<Record<string, boolean>>({
  //   "3BR,2.0BA": true, "2BR,1.0BA":true, "Others":true});
  const [unitSelect, setUnitSelect] = React.useState<string>("3BR,2BA")

  const onChecked = (e, text) => {
    // Need to create new object so that React sees the change
    // let foo = {...checks, [text]:  e.target.checked}
    setUnitSelect(text)
  }
  return (
    <ErrorBoundary fallback={<div>Error in RentalRatesMap</div>}>
      <div className='flex flex-row'>
        {["3BR,2.0BA", "2BR,1.0BA", "Others"].map((text) => {
          return topCheck(text, unitSelect, onChecked)
        })}
      </div>

      <div className='flex flex-row'>
        <MapContainer
          center={[32.7157, -117.1611]}
          zoom={13}
          scrollWheelZoom={true}
          className={'!h-[80vh] !w-100'}
          whenCreated={map => setInterval(() => {
            map.invalidateSize()
          }, 100)}

        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          {rentalRates.map((rentalRate: RentLocationRate) => (
            rentalRate.rents[unitSelect] && <div key={rentalRate.pid}>
                <Marker  position={[rentalRate.lat, rentalRate.long]}>
                    <Tooltip permanent>${rentalRate.rents[unitSelect].rent_mean.toLocaleString()}</Tooltip>
                </Marker>
                <Marker key={rentalRate.pid+"asdfjkl"} position={[rentalRate.lat, rentalRate.long]}>
                    <Tooltip permanent={false}>
                        <p>Parcel: {rentalRate.pid}</p>
                      {Object.entries(rentalRate.rents).map((kv, idx) =>
                        <p key={"rentalRate.pid" + kv[0]}>
                          {kv[0]} : Mean: ${kv[1].rent_mean.toLocaleString()}.
                          75th percentile: ${kv[1].rent_75_percentile.toLocaleString()}.
                          {' '}{kv[1].num_samples} samples
                        </p>
                      )}

                    </Tooltip>
                </Marker>
            </div>
          ))

          }
          {/*{Object.entries(rentalRate.rents).map((kv, idx) =>*/}
          {/*  <p key={"rentalRate.pid" + kv[0]}>*/}
          {/*    {kv[0]} : Mean: ${kv[1].rent_mean.toLocaleString()}.*/}
          {/*    75th percentile: ${kv[1].rent_75_percentile.toLocaleString()}</p>*/}
          {/*)}*/}
          {/*</Tooltip>*/}
        </MapContainer>
      </div>
    </ErrorBoundary>
  );
}

export default RentalRatesMap;
