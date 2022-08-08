import * as React from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import { Link } from 'react-router-dom';
import { Listing } from '../../types';

type Props = { listings: Listing[] };

const asSqFt = (m) => Math.round(m * 3.28 * 3.28);

function ListingsMap({ listings }: Props) {
  return (
    <MapContainer
      center={[32.7157, -117.1611]}
      zoom={13}
      scrollWheelZoom={true}
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      {listings.map((listing) => (
        <Marker position={[listing.centroid_y, listing.centroid_x]}>
          <Popup>
            <Link
              to={{
                pathname: `/analysis/${listing.analysis_id}`,
              }}
              className="underline text-darkblue"
            >
              {listing.address}
            </Link>
            <p>APN: {listing.apn}</p>
            <p>Avail building area: {asSqFt(listing.avail_geom_area)}sqft</p>
            <p>FAR potential: {listing.potential_FAR.toPrecision(2)}</p>
            {/* Add any other information we want */}
          </Popup>
        </Marker>
      ))}
    </MapContainer>
  );
}

export default ListingsMap;
