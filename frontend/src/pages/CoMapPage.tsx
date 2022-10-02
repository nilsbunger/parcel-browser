import * as React from 'react';
import { CSSProperties, useCallback, useState } from 'react';
import { ErrorBoundary } from "react-error-boundary";
import DeckGL from '@deck.gl/react';
import { BitmapLayer, PathLayer } from '@deck.gl/layers';

import { MapView } from '@deck.gl/core';
import { TileLayer } from '@deck.gl/geo-layers';
import { MVTLayer } from "@deck.gl/geo-layers/typed";

// Set your mapbox access token here
const MAPBOX_ACCESS_TOKEN = 'pk.eyJ1Ijoibmlsc2hvbWUzIiwiYSI6ImNsOHJtbDFtbDI2Znkzb3RvdDV0emhmamEifQ.rkpWuotqi4HacN2QUoWkgg';

const INITIAL_VIEW_STATE = {
  latitude: 32.7157,
  longitude: -117.1611,
  zoom: 10,
  maxZoom: 20,
  minZoom: 10,
  maxPitch: 89,
  bearing: 0
};

const COPYRIGHT_LICENSE_STYLE: CSSProperties = {
  position: 'absolute',
  right: 0,
  bottom: 0,
  backgroundColor: 'hsla(0,0%,100%,.5)',
  padding: '0 5px',
  font: '12px/20px Helvetica Neue,Arial,Helvetica,sans-serif'
};

const LINK_STYLE = {
  textDecoration: 'none',
  color: 'rgba(0,0,0,.75)',
  cursor: 'grab'
};

/* global window */
const devicePixelRatio = (typeof window !== 'undefined' && window.devicePixelRatio) || 1;

function getTooltip({ tile }) {
  console.log(tile);
  if (!tile) {
    return null
  }
  const { x, y, z } = tile.index;
  return tile && `tile: x: ${x}, y: ${y}, z: ${z}`;
}

function tpaTileLayer(enabled) {

  const tpaOnHover = useCallback(info => {
    console.log("tpa on hover");
  }, [])

  if (!enabled) return null

  return new MVTLayer({
    id: 'tpa-tile-layer',
    data: '/dj/api/tpatile/{z}/{x}/{y}',
    getLineColor: [255, 255, 255],
    getFillColor: [250, 0, 0, 30],
    lineWidthMinPixels: 3,
    pickable: true,
    onHover: tpaOnHover,

    // renderSubLayers: props => {
    //   const {
    //     bbox: {west, south, east, north}
    //   } = props.tile;
    //
    //   return new BitmapLayer(props, {
    //     data: null,
    //     image: props.data,
    //     bounds: [west, south, east, north]
    //   });
    // }
  });
}

function baseTileLayer(onTilesLoad, showTileBoundaries) {
  return new TileLayer({
    // https://wiki.openstreetmap.org/wiki/Slippy_map_tilenames#Tile_servers
    data: [
      'https://a.tile.openstreetmap.org/{z}/{x}/{y}.png',
      'https://b.tile.openstreetmap.org/{z}/{x}/{y}.png',
      'https://c.tile.openstreetmap.org/{z}/{x}/{y}.png'
    ],

    // Since these OSM tiles support HTTP/2, we can make many concurrent requests
    // and we aren't limited by the browser to a certain number per domain.
    maxRequests: 20,

    pickable: false,
    onViewportLoad: onTilesLoad,
    autoHighlight: showTileBoundaries,
    highlightColor: [60, 60, 60, 40],
    // https://wiki.openstreetmap.org/wiki/Zoom_levels
    minZoom: 0,
    maxZoom: 19,
    tileSize: 256,
    zoomOffset: devicePixelRatio === 1 ? -1 : 0,
    renderSubLayers: props => {
      const {
        bbox: { west, south, east, north }
      } = props.tile;

      return [
        new BitmapLayer(props, {
          data: null,
          image: props.data,
          bounds: [west, south, east, north]
        }),
        showTileBoundaries && new PathLayer({
          id: `${props.id}-border`,
          visible: props.visible,
          data: [
            [
              [west, north],
              [west, south],
              [east, south],
              [east, north],
              [west, north]
            ]
          ],
          getPath: d => d,
          getColor: [255, 0, 0],
          widthMinPixels: 4
        })
      ];
    }
  });
}

function LayerSquare({enabled, color}) {
  if (enabled)
    return (<span style={{width: "20px", backgroundColor: "rgb(255, 255, 255)", border: "2px solid", borderColor:color}}>&nbsp;</span>)
  else
    return (<span style={{width: "20px", backgroundColor: "rgb(255, 255, 255)", border: "2px solid", borderColor:color}}>&nbsp;</span>)
}

function CoMapLayerControl({ tpaEnabled, setTpaEnabled }) {

  const onClick = event => {
    setTpaEnabled(!tpaEnabled);
  }


  return (
    <div className="dropdown">
      <label tabIndex={0} className="btn btn-xs m-1">Legend</label>
      <ul tabIndex={0} className="dropdown-content menu p-2 shadow bg-base-100 rounded-box w-52" onClick={onClick}>
        <li><a><LayerSquare enabled={true} color={"rgb(44, 160, 44)"} />Transit Priority Area</a></li>
        <li><a>Item 2</a></li>
      </ul>
    </div>
    // <div className="map-control">
    //   <label>
    //     <input
    //       type="checkbox"
    //       checked={showTileBoundaries}
    //       onChange={e => setShowTileBoundaries(e.target.checked)}
    //     />
    //     Show tile boundaries
    //   </label>
    // </div>
  );
}

export function CoMapPage({ onTilesLoad = null }) {
  const showTileBoundaries = false;
  const [hoverInfo, setHoverInfo] = useState();
  const [tpaEnabled, setTpaEnabled] = useState(true)

  console.log(hoverInfo)

  const LONGITUDE_RANGE = [-117.35, -116.9];  // west, east constraint
  const LATITUDE_RANGE = [32.5, 33.25];       // south, north constraint

  const onHover = useCallback((info, event) => {
    setHoverInfo(info);
  }, [])
  const onClick = useCallback((info, event) => {
    console.log("Click", info);
  }, [])

  return (
    <ErrorBoundary fallback={<div>Error loading commercial map</div>}>
      <DeckGL
        layers={[
          baseTileLayer(onTilesLoad, showTileBoundaries),
          tpaTileLayer(tpaEnabled),
        ]}
        views={new MapView({ repeat: true })}
        initialViewState={INITIAL_VIEW_STATE}
        controller={true}
        getTooltip={getTooltip}
        onHover={onHover}
        onClick={onClick}
        onViewStateChange={({ viewState }) => {
          viewState.longitude = Math.min(LONGITUDE_RANGE[1], Math.max(LONGITUDE_RANGE[0], viewState.longitude));
          viewState.latitude = Math.min(LATITUDE_RANGE[1], Math.max(LATITUDE_RANGE[0], viewState.latitude));
          return viewState;
        }}
      >
        <CoMapLayerControl tpaEnabled = {tpaEnabled} setTpaEnabled={setTpaEnabled} />
        <div style={COPYRIGHT_LICENSE_STYLE}>
          {'© '}
          <a style={LINK_STYLE} href="http://www.openstreetmap.org/copyright" target="blank">
            OpenStreetMap contributors
          </a>
        </div>
      </DeckGL>
    </ErrorBoundary>
  );
}
