import Map from 'ol/Map';
import View from 'ol/View';
import {GeoJSON} from 'ol/format'
import OSM from 'ol/source/OSM';
import TileLayer from 'ol/layer/Tile';
import VectorSource from 'ol/source/Vector';
import {fromLonLat} from 'ol/proj';
import VectorLayer from "ol/layer/Vector";
import {SimpleGeometry} from "ol/geom";


// Initiate map with CRS => EPSG:3857
const url = window.location.pathname;

// TODO: we should use local data from the template (parcelData and buildingData) instead of fetching
// it.
let vectorSource = new VectorSource({
    format: new GeoJSON(),
    url: url + '/geodata'
});
console.log (vectorSource.getFeatures());

let view = new View({
    center: fromLonLat([-117.19905688459625, 32.78415286818754]),

    // center: ol.proj.fromLonLat([, ]),   // 2210 Illion St, San Diego, 92110],
    zoom: 19
})

let map = new Map({
    layers: [
        new TileLayer({
            source: new OSM()
        }),
        new VectorLayer({
            source: vectorSource,
        })
    ],
    target: 'map',
    view: view,
});

vectorSource.on('featuresloadend', (event) => {
    console.log("FEATURED LOADED");
    console.log(event.features[0].getGeometry());
    view.fit( event.features[0].getGeometry() as SimpleGeometry,{padding: [100, 100, 100, 100]})

})