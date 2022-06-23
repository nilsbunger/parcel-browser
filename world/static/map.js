const copy = "© <a href='https://www.openstreetmap.org/copyright'>OpenStreetMap</a> contributors";
const url = "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png";
const osm = L.tileLayer(url, { attribution: copy });
const map = L.map("map", { layers: [osm], minZoom: 5 });
// map.
//     locate()
//     .on("locationfound", (e) => map.setView(e.latlng, 8))
//     .on("locationerror", () => map.setView([0, 0], 5));
// map.setView([33.22214126963008, -117.22432683708347], 14) // San Diego
map.setView([32.78415286818754, -117.19905688459625], 18)   // 2210 Illion St, San Diego, 92110
// We ask our endpoint to return only the markers of the specific displayed area, passed as a boundbox string.
//
// To build the marker layer, we ask our endpoint for data asynchronously and extract the properties we want to show in the pop-ups.
//
// We invoke this flow, every time the user stops moving on the map.
async function load_markers() {
    const markers_url = `/api/markers/?in_bbox=${map.getBounds().toBBoxString()}`
    const response = await fetch(markers_url)
    const geojson = await response.json()
    return geojson
}

let pending = 0;
async function load_parcels() {
    const parcels_url = `/api/parcels/?in_bbox=${map.getBounds().toBBoxString()}`
    const response = await fetch(parcels_url)
    const geojson = await response.json()
    return geojson
}

async function render_layers() {
    const markers = await load_markers();
    L.geoJSON(markers)
    .bindPopup((layer) => layer.feature.properties.name)
    .addTo(map);
    if (pending === 1) {
        pending = 2;
        return;
    }
    pending = 1;
    while (pending > 0) {
        const parcels = await load_parcels();
        L.geoJSON(parcels)
            // .bindPopup((layer) => layer.feature.properties.name)
            .addTo(map);
        pending = pending - 1;
    }
    // console.log('markers=', markers);
    // console.log('parcels=', parcels);
}

map.on("moveend", render_layers);
render_layers();