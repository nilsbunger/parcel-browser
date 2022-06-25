
import Map from 'ol/Map';
import View from 'ol/View';
import {GeoJSON} from 'ol/format'
import OSM from 'ol/source/OSM';
import TileLayer from 'ol/layer/Tile';
import VectorSource from 'ol/source/Vector';
import {fromLonLat} from 'ol/proj';
import VectorLayer from "ol/layer/Vector";


// Initiate map with CRS => EPSG:3857
const url = window.location.pathname;
let vectorSource = new VectorSource({
    format: new GeoJSON(),
    url: url+'/geodata'
});

let map = new Map({
  layers: [
    new TileLayer({
      source: new OSM()
    }),
    new VectorLayer({
        source: vectorSource
    })
  ],
  target: 'map',
  view: new View({
      center: fromLonLat([-117.19905688459625, 32.78415286818754]),

      // center: ol.proj.fromLonLat([, ]),   // 2210 Illion St, San Diego, 92110],
    zoom: 19
  })
});
//
// let map = new Map({
//   layers: [
//     new TileLayer({source: new OSM()})
//   ],
//   view: new View({
//     center: [0, 0],
//     zoom: 2
//   }),
//   target: 'map'
// });
