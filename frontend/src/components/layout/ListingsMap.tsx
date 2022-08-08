import * as React from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import { Link } from 'react-router-dom';
import { Listing } from '../../types';

type Props = { listings: Listing[] };

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
            <p>
              APN:
              <Link
                to={{
                  pathname: `/analysis/${listing.analysis_id}`,
                }}
                className="underline text-darkblue"
              >
                {listing.apn}
              </Link>
            </p>
          </Popup>
        </Marker>
      ))}
    </MapContainer>
  );
}

export default ListingsMap;
