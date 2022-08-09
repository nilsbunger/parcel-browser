import Map from 'ol/Map';
import View from 'ol/View';
import {MVT} from 'ol/format'
import OSM from 'ol/source/OSM';
import TileLayer from 'ol/layer/Tile';
import {fromLonLat} from 'ol/proj';
import VectorTileLayer from "ol/layer/VectorTile";
import VectorTileSource from "ol/source/VectorTile";
import {Fill, Stroke, Style} from "ol/style";

const form = document.getElementById('search');
const log = document.getElementById('log');

async function search(event) {
    event.preventDefault();
    let center;
    const addr = document.getElementById('addr').value;
    
    await fetch(`/map/search/${addr}`)
    .then(response => { return response.json() })
    .then(coords => {
        if (coords == '404') {
            log.textContent = `Could not find ${addr}.`;
        } else {
            center = fromLonLat([coords.x, coords.y]);
            window.location.href = `/map/?center=${center[0]},${center[1]}`;
        }
    });
}

form.addEventListener('submit', search);

let parcelVectorSource = new VectorTileSource({
    format: new MVT({
      idProperty: 'iso_a3',
    }),
    url: '/dj/api/parceltile/{z}/{x}/{y}',
    wrapX: false,
});

const parcelTileLayer = new VectorTileLayer({
    declutter: true,
    source: parcelVectorSource,
    style: new Style({
        stroke: new Stroke({
            color: 'green',
            width: 1
        }),
        fill: new Fill({
        color: 'rgba(20,20,20,0.1)',
      }),
    })
});

let topoVectorSource = new VectorTileSource({
    format: new MVT({
      idProperty: 'iso_a3',
    }),
    url: '/dj/api/topotile/{z}/{x}/{y}',
    wrapX: false,
});


const topoTileLayer = new VectorTileLayer({
    declutter: true,
    source: topoVectorSource,
    minZoom: 16,
    style: new Style({
        stroke: new Stroke({
            color: 'green',
            width: 1
        }),
        fill: new Fill({
        color: 'rgba(20,20,20,0.1)',
      }),
    })
});


const queryString = window.location.search;
const urlParams = new URLSearchParams(queryString);
const centerStr = urlParams.get('center')?.split(',');
let viewCenter = fromLonLat([-117.19905688459625, 32.78415286818754]) // 2210 Illion St, San Diego, 92110],
let zoom = 18;
console.log (viewCenter);
if (centerStr) {
    viewCenter = [parseFloat(centerStr[0]), parseFloat(centerStr[1])]
}
console.log (viewCenter);

let map = new Map({
    layers: [
        new TileLayer({source: new OSM()}),
        parcelTileLayer,
        topoTileLayer,
            // style: function (feature) {
            //   const color = feature.get('COLOR') || '#eeeeee';
            //   style.getFill().setColor(color);
            //   return style;
            //   },

    ],
    target: 'map',
    view: new View({
        center: viewCenter,
        zoom: zoom,
        minZoom: 14,
    })
});

const selectedStyle = new Style({
    fill: new Fill({
        color: '#eeeeee',
    }),
    stroke: new Stroke({
        color: 'rgba(255, 255, 255, 0.7)',
        width: 2,
    }),
});

map.on(['click'], function (event) {
    console.log("EVENT", event);
    console.log(event.pixel);
    const features = map.getFeaturesAtPixel(event.pixel);
    console.log ("Features:", features[0]);
    if (features[0]?.properties_.apn) {
        document.body.style.cursor = "wait";
        window.location.href = "/dj/parcel/" + features[0].properties_.apn;
    }
    // vtLayer.getFeatures(event.pixel).then(function (features) {
    //     console.log ("Features:", features);
    //       selectionLayer.changed();
    // });
});
