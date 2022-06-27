import Map from 'ol/Map';
import View from 'ol/View';
import {MVT} from 'ol/format'
import OSM from 'ol/source/OSM';
import TileLayer from 'ol/layer/Tile';
import {fromLonLat} from 'ol/proj';
import VectorTileLayer from "ol/layer/VectorTile";
import VectorTileSource from "ol/source/VectorTile";
import {Fill, Stroke, Style} from "ol/style";


let vectorSource = new VectorTileSource({
    format: new MVT({
      idProperty: 'iso_a3',
    }),
    url: '/parceltile/{z}/{x}/{y}',
    wrapX: false,
});

const vtLayer = new VectorTileLayer({
    declutter: true,
    source: vectorSource,
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

let map = new Map({
    layers: [
        new TileLayer({source: new OSM()}),
        vtLayer
            // style: function (feature) {
            //   const color = feature.get('COLOR') || '#eeeeee';
            //   style.getFill().setColor(color);
            //   return style;
            //   },

    ],
    target: 'map',
    view: new View({
        center: fromLonLat([-117.19905688459625, 32.78415286818754]), // 2210 Illion St, San Diego, 92110],
        zoom: 18,
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
        window.location.href = "/parcel/" + features[0].properties_.apn;
    }
    // vtLayer.getFeatures(event.pixel).then(function (features) {
    //     console.log ("Features:", features);
    //       selectionLayer.changed();
    // });
});
