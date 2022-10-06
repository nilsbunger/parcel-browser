import * as React from 'react';
import { CSSProperties, useCallback, useEffect, useMemo, useState } from 'react';
import { ErrorBoundary } from "react-error-boundary";
import DeckGL from '@deck.gl/react';
import { BitmapLayer, GeoJsonLayer, PathLayer } from '@deck.gl/layers';

import { MapView } from '@deck.gl/core';
import { TileLayer } from '@deck.gl/geo-layers';
import { MVTLayer } from "@deck.gl/geo-layers/typed";
import { Button, Menu } from "@mantine/core";
import { useImmer } from "use-immer";
import { CoMapDrawer } from "../components/CoMapDrawer";

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

const LAYER_COLORS: Record<string, [number, number, number, number]> = {
  'tpa-vis-layer': [250, 0, 0, 30],
  'compcomm-vis-layer': [1, 1, 1, 0],  // TODO : need to add
  'sf-vis-layer': [250, 250, 0, 200],
  'mf-vis-layer': [250, 180, 0, 200],
  'c-vis-layer': [250, 0, 0, 200],
}

const TILE_DEFS2 = (zoneColorFn, visibleLayers) => {
  return {
    'road-tile-layer': {
      data: '/dj/api/roadtile/{z}/{x}/{y}',
      getLineColor: [128, 128, 128],
      getFillColor: [0, 0, 0, 255],
      minZoom: 16,
      lineWidthMinPixels: 2,
      pickable: true,
      onHover: null,
      visible: true,
    },

    'parcel-tile-layer': {
      data: '/dj/api/parceltile/{z}/{x}/{y}',
      getLineColor: [128, 128, 128],
      getFillColor: [0, 0, 0, 0],
      minZoom: 16,
      lineWidthMinPixels: 2,
      pickable: true,
      onHover: null,
      visible: true,
    },
    'tpa-tile-layer': {
      data: '/dj/api/tpatile/{z}/{x}/{y}',
      getLineColor: [255, 255, 255],
      getFillColor: [250, 0, 0, 30],
      lineWidthMinPixels: 3,
      pickable: true,
      onHover: null,
      visible: true,
    },
    'zoning-tile-label-layer': {
      data: '/dj/api/zoninglabeltile/{z}/{x}/{y}',
      getLineColor: [128, 128, 128],
      minZoom: 13,
      lineWidthMinPixels: 2,
      getTextSize: 12,
      getTextColor: [50, 50, 50],
      pickable: false,
      pointType: 'text',  // ensures Point elements are rendered as a TextLayer
      visible: true,
      // renderSubLayers: props => new GeoJsonLayer(props)
    },
    'zoning-tile-layer': {
      data: '/dj/api/zoningtile/{z}/{x}/{y}',
      getLineColor: [128, 128, 128],
      getFillColor: zoneColorFn,
      minZoom: 0,
      lineWidthMinPixels: 2,
      pickable: true,
      onHover: null,
      visible: true,
      updateTriggers: {
        getFillColor: visibleLayers
      }
    }
  }
}

function mvtLayerWrapper(id, layers, visible=true) {
  const layeropts = layers[id];
  const onHover = useCallback(layeropts.onHover, [])

  if (!visible) return null
  const merged = { ...layeropts, id: id, onHover: onHover }
  // console.log("MERGED", merged)
  return new MVTLayer(merged);
}


/* global window */
const devicePixelRatio = (typeof window !== 'undefined' && window.devicePixelRatio) || 1;

function getTooltip({ tile }) {
  // console.log(tile);
  if (!tile) {
    return null
  }
  const { x, y, z } = tile.index;
  return tile && `tile: x: ${x}, y: ${y}, z: ${z}`;
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
          bounds: [west, south, east, north],
          desaturate: 0.8,
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

function LayerSquare({ enabled, color }: { enabled: boolean, color: [number, number, number, number] }) {
  const rgbacolor = `rgba(${color[0]},${color[1]},${color[2]},${color[3] / 255.0})`
  const styles = {
    display: "inline-block",
    width: "20px",
    marginRight: "5px",
    backgroundColor: enabled ? rgbacolor : "rgb(255, 255, 255)",
    border: "2px solid",
    borderColor: rgbacolor
  }
  return <div style={styles}>&nbsp;</div>
}

function CoMapLayerControl({ visibleLayers, setVisibleLayers }) {

  const toggleLayer = (e, name) => {
    // setTpaEnabled(!tpaEnabled);
    e.stopPropagation()
    setVisibleLayers((draft) => {
      draft[name] = !draft[name]
    })
  }

  // console.log("Visible layers:", visibleLayers)
  return (
    <div style={{ backgroundColor: "#777" }}>
      <Menu
        shadow="md"
        width={200}
        closeOnItemClick={false}
        closeOnClickOutside={false}
        withArrow={true}
        zIndex={1000}
      >
        <Menu.Target>
          <Button>Layers</Button>
        </Menu.Target>

        <Menu.Dropdown>
          <Menu.Label>Residential zones</Menu.Label>
          <Menu.Item onClick={(e) => toggleLayer(e, 'sf-vis-layer')}>
            <LayerSquare enabled={visibleLayers['sf-vis-layer']} color={LAYER_COLORS['sf-vis-layer']}/>Single-family
          </Menu.Item>
          <Menu.Item onClick={(e) => toggleLayer(e, 'mf-vis-layer')}>
            <LayerSquare enabled={visibleLayers['mf-vis-layer']} color={LAYER_COLORS['mf-vis-layer']}/>Multi-family
          </Menu.Item>
          <Menu.Item onClick={(e) => toggleLayer(e, 'tpa-vis-layer')}>
            <LayerSquare enabled={visibleLayers['tpa-vis-layer']} color={LAYER_COLORS['tpa-vis-layer']}/>TPA
          </Menu.Item>
          {/*<Menu.Item onClick={(e) => toggleLayer(e, 'compcomm-vis-layer')}>*/}
          {/*  <LayerSquare enabled={visibleLayers['compcomm-vis-layer']} color={LAYER_COLORS['compcomm-vis-layer']}/>Complete Communities*/}
          {/*</Menu.Item>*/}
          {/*<Menu.Item rightSection={<Text size="xs" color="dimmed">⌘K</Text>}>Search</Menu.Item>*/}

          <Menu.Divider/>

          <Menu.Label>Commercial zones</Menu.Label>
          <Menu.Item onClick={(e) => toggleLayer(e, 'c-vis-layer')}>
            <LayerSquare enabled={visibleLayers['c-vis-layer']} color={LAYER_COLORS['c-vis-layer']}/>Commercial zones
          </Menu.Item>
          <Menu.Item></Menu.Item>
        </Menu.Dropdown>
      </Menu>
    </div>
  );
  // <div className="dropdown">
  //   <label tabIndex={0} className="btn btn-xs m-1">Layers</label>
  //   <ul tabIndex={0} className="dropdown-content menu p-2 shadow bg-base-100 rounded-box w-52" onClick={onClick}>
  //     <li><a><LayerSquare enabled={tpaEnabled} color={"rgb(44, 160, 44)"}/>Transit Priority Area</a></li>
  //     <li><a>Item 2</a></li>
  //   </ul>
  // </div>
  //

}


export function CoMapPage({ onTilesLoad = null }) {
  const showTileBoundaries = false;
  const [hoverInfo, setHoverInfo] = useState();
  const [selection, setSelection] = useState<{ selType: string, objId: number, info: object }>(null);
  const [visibleLayers, setVisibleLayers] = useImmer<Record<string, boolean>>({
    'tpa-vis-layer': true, 'mf-vis-layer': true, 'sf-vis-layer': false, 'compcomm-vis-layer': true, 'c-vis-layer': false
  });

  const LONGITUDE_RANGE = [-117.35, -116.9];  // west, east constraint
  const LATITUDE_RANGE = [32.5, 33.25];       // south, north constraint

  const zoneColorFn = (zone, extra) => {
    console.log("ZONE COLOR on", zone)
    if (zone.properties.zone_name.startsWith("C"))
      return visibleLayers['c-vis-layer'] ? LAYER_COLORS['c-vis-layer'] : [0, 0, 0, 0]
    if (zone.properties.zone_name.startsWith("RS"))
      return visibleLayers['sf-vis-layer'] ? LAYER_COLORS['sf-vis-layer'] : [0, 0, 0, 0]
    if (zone.properties.zone_name.startsWith("RM"))
      return visibleLayers['mf-vis-layer'] ? LAYER_COLORS['mf-vis-layer'] : [0, 0, 0, 0]
    return [0, 0, 0, 0]
  }
  const TILE_DEFS = TILE_DEFS2(zoneColorFn, visibleLayers)
  const onHover = useCallback((info, event) => {
    setHoverInfo(info);
  }, [])
  const onClick = useCallback((info, event) => {
    if (event.target.id !== "view-MapView") {
      // console.log("Map page click handler ignoring click on", event.target.id)
      event.stopPropagation() // this doesn't seem to actually do anything ??
      return
    }
    if (info.layer) {
      const selType = info.layer.id // is the name of the layer - 'zoning-tile-layer', etc
      const objId = info.object.properties.id
      console.log("Set Selection: ", { selType, objId, info })
      setSelection({ selType, objId, info })
    } else
      setSelection(null)
  }, [])

  // event handler for escape key
  useEffect(() => {
    const handleEsc = (event) => {
      if (event.keyCode === 27) {
        setSelection(null)
      }
    };
    window.addEventListener('keydown', handleEsc);
    return () => {
      window.removeEventListener('keydown', handleEsc);
    };
  }, []);


  return (
    <ErrorBoundary fallback={<div>Error loading commercial map</div>}>
      <DeckGL
        layers={[
          baseTileLayer(onTilesLoad, showTileBoundaries),
          mvtLayerWrapper('zoning-tile-layer', TILE_DEFS),
          mvtLayerWrapper('zoning-tile-label-layer', TILE_DEFS),
          mvtLayerWrapper('tpa-tile-layer', TILE_DEFS, visibleLayers['tpa-vis-layer']),
          mvtLayerWrapper('parcel-tile-layer', TILE_DEFS),
          mvtLayerWrapper('road-tile-layer', TILE_DEFS),
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
        <CoMapLayerControl visibleLayers={visibleLayers} setVisibleLayers={setVisibleLayers}/>
        <CoMapDrawer selection={selection} setSelection={setSelection}/>

      </DeckGL>
    </ErrorBoundary>
  );
}
