import * as React from "react"
import { FeatureGroup, LayersControl, MapContainer, Marker, Popup, TileLayer } from "react-leaflet"
import { Link } from "react-router-dom"
import { Listing } from "../../types"
import { ErrorBoundary } from "react-error-boundary"

type Props = { listings: Listing[] }

const asSqFt = (m: number) => Math.round(m * 3.28 * 3.28)

function ListingsMap({ listings }: Props) {
  const center = [32.7157, -117.1611]
  return (
    <ErrorBoundary fallback={<div>Error in ListingsMap</div>}>
      <MapContainer
        center={center as any}
        zoom={13}
        scrollWheelZoom={true}
        className={"!h-[80vh] !w-5/12"}
        whenCreated={(map: any) =>
          setInterval(() => {
            map.invalidateSize()
          }, 100)
        }
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {/* See layer control example at https://react-leaflet.js.org/docs/example-layers-control/ */}
        <LayersControl position="topright">
          <LayersControl.Overlay name="Transit Priority Areas">
            <Marker position={center}>
              <Popup>
                A pretty CSS3 popup. <br /> Easily customizable.
              </Popup>
            </Marker>
            {/*<TileLayer*/}
            {/*  url="/dj/api/tpatile/{z}/{x}/{y}"*/}
            {/*/>*/}
          </LayersControl.Overlay>
          <LayersControl.Overlay checked name="Layer group with circles">
            <Marker position={[5, 5]}>
              <Popup>
                A pretty CSS3 popup. <br /> Easily customizable.
              </Popup>
            </Marker>
          </LayersControl.Overlay>
          <LayersControl.Overlay name="Feature group">
            <FeatureGroup pathOptions={{ color: "purple" }}>
              <Popup>Popup in FeatureGroup</Popup>
            </FeatureGroup>
          </LayersControl.Overlay>
        </LayersControl>
        {listings.map((listing) => (
          <Marker key={"" + listing.mlsid + listing.founddate} position={[listing.centroid_y, listing.centroid_x]}>
            <Popup>
              <p>
                <Link
                  to={{
                    pathname: `/analysis/${listing.analysis_id}`,
                  }}
                  className="underline text-darkblue"
                >
                  {listing.address}
                </Link>
                <br />
                Price: ${listing.price}
                <br />
                Zone: {listing.zone}
                <br />
                Parcel size: {asSqFt(listing.parcel_size)}
                <br />
                Avail building area: {asSqFt(listing.avail_geom_area)}sqft
                <br />
                FAR potential: {listing.potential_FAR.toPrecision(2)}
                {/* Add any other information we want */}
              </p>
            </Popup>
          </Marker>
        ))}
      </MapContainer>
    </ErrorBoundary>
  )
}

export default ListingsMap
