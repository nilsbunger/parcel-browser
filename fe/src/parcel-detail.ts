// import Map from "ol/Map"
// import View from "ol/View"
// import { GeoJSON, MVT } from "ol/format"
// import OSM from "ol/source/OSM"
// import TileLayer from "ol/layer/Tile"
// import VectorSource from "ol/source/Vector"
// import { fromLonLat } from "ol/proj"
// import VectorLayer from "ol/layer/Vector"
// import { SimpleGeometry } from "ol/geom"
// import VectorTileSource from "ol/source/VectorTile"
// import VectorTileLayer from "ol/layer/VectorTile"
// import { Fill, Stroke, Style } from "ol/style"
// import { BACKEND_DOMAIN } from "./constants";
//
// // Initiate map with CRS => EPSG:3857
// const url = window.location.pathname
//
// let topoVectorSource = new VectorTileSource({
//   format: new MVT({
//     idProperty: "iso_a3",
//   }),
//   url: `${BACKEND_DOMAIN}/dj/api/topotile/{z}/{x}/{y}`,
//   wrapX: false,
// })
//
// const topoTileLayer = new VectorTileLayer({
//   declutter: true,
//   source: topoVectorSource,
//   minZoom: 16,
//   style: new Style({
//     stroke: new Stroke({
//       color: "green",
//       width: 1,
//     }),
//     fill: new Fill({
//       color: "rgba(20,20,20,0.1)",
//     }),
//   }),
// })
//
// // TODO: we should use local data from the template (parcelData and buildingData) instead of fetching
// // it.
// let vectorSource = new VectorSource({
//   format: new GeoJSON(),
//   url: url + "/geodata",
// })
// console.log(vectorSource.getFeatures())
//
// // let vectorSourceNeighbor = new VectorSource({
// //   format: new GeoJSON(),
// //   url: url + "/geodata/neighbor",
// // })
// //
// let view = new View({
//   center: fromLonLat([-117.19905688459625, 32.78415286818754]),
//
//   // center: ol.proj.fromLonLat([, ]),   // 2210 Illion St, San Diego, 92110],
//   zoom: 19,
// })
//
// // let map = new Map({
// //   layers: [
// //     new TileLayer({
// //       source: new OSM(),
// //     }),
// //     new VectorLayer({
// //       source: vectorSourceNeighbor,
// //       style: new Style({
// //         stroke: new Stroke({
// //           color: "rgba(8,45,122,0.3)",
// //           width: 1,
// //         }),
// //         fill: new Fill({
// //           color: "rgba(8,45,122,0.1)",
// //         }),
// //       }),
// //     }),
// //     new VectorLayer({
// //       source: vectorSource,
// //       style: new Style({
// //         stroke: new Stroke({
// //           color: "rgba(8,45,122,0.85)",
// //           width: 1,
// //         }),
// //         fill: new Fill({
// //           color: "rgba(8,45,122,0.15)",
// //         }),
// //       }),
// //     }),
// //     topoTileLayer,
// //   ],
// //   target: "map",
// //   view: view,
// // })
//
// vectorSource.on("featuresloadend", (event) => {
//   console.log("FEATURED LOADED")
//   console.log(event.features[0].getGeometry())
//   // console.log(event.features[0].values_);
//   const parcelFeatures = pickFeatures(event.features[0].values_)
//
//   let aestheticAddress = ""
//   const addrVals = [
//     parcelFeatures["situs_addr"],
//     parcelFeatures["situs_pre_field"],
//     parcelFeatures["situs_stre"],
//     parcelFeatures["situs_suff"],
//     parcelFeatures["situs_frac"],
//     parcelFeatures["situs_buil"],
//     parcelFeatures["situs_suit"],
//   ]
//   addrVals.forEach((string) => {
//     if (string !== null) {
//       aestheticAddress += string + " "
//     }
//   })
//
//   let rightcol = document.getElementById("rightcol")
//   rightcol.innerHTML =
//     "<p>" + aestheticAddress + "</p><p>" + latlong + "</p><p>Lot size: " + lotSize + " </p>"
//   let val: keyof typeof parcelFeatures
//   for (val in parcelFeatures) {
//     console.log(val, parcelFeatures[val])
//     let p = document.createElement("p")
//     p.innerHTML = val + ": " + parcelFeatures[val]
//     rightcol.append(p)
//   }
//
//   view.fit(event.features[0].getGeometry() as SimpleGeometry, { padding: [100, 100, 100, 100] })
//   let center = view.getCenter()
//   let maplink = document.getElementById("map-header-link")
//   maplink.href = new URL("/dj/map?center=" + center, maplink.href)
// })
//
// const pickFeatures = (o) => {
//   return (({
//     apn,
//     apn_8,
//     parcelid,
//     own_name1,
//     own_name2,
//     own_name3,
//     fractint,
//     own_addr1,
//     own_addr2,
//     own_addr3,
//     own_addr4,
//     own_zip,
//     situs_juri,
//     situs_stre,
//     situs_suff,
//     situs_post,
//     situs_pre_field,
//     situs_addr,
//     situs_frac,
//     situs_buil,
//     situs_suit,
//     legldesc,
//     asr_land,
//     asr_impr,
//     asr_total,
//     doctype,
//     docnmbr,
//     docdate,
//     acreage,
//     taxstat,
//     ownerocc,
//     tranum,
//     asr_zone,
//     asr_landus,
//     unitqty,
//     submap,
//     subname,
//     nucleus_zo,
//     nucleus_us,
//     situs_comm,
//     year_effec,
//     total_lvg_field,
//     bedrooms,
//     baths,
//     addition_a,
//     garage_con,
//     garage_sta,
//     carport_st,
//     pool,
//     par_view,
//     usable_sq_field,
//     qual_class,
//     nucleus_si,
//     nucleus_1,
//     nucleus_2,
//     situs_zip,
//     overlay_ju,
//     sub_type,
//     multi,
//   }) => ({
//     apn,
//     apn_8,
//     parcelid,
//     own_name1,
//     own_name2,
//     own_name3,
//     fractint,
//     own_addr1,
//     own_addr2,
//     own_addr3,
//     own_addr4,
//     own_zip,
//     situs_juri,
//     situs_stre,
//     situs_suff,
//     situs_post,
//     situs_pre_field,
//     situs_addr,
//     situs_frac,
//     situs_buil,
//     situs_suit,
//     legldesc,
//     asr_land,
//     asr_impr,
//     asr_total,
//     doctype,
//     docnmbr,
//     docdate,
//     acreage,
//     taxstat,
//     ownerocc,
//     tranum,
//     asr_zone,
//     asr_landus,
//     unitqty,
//     submap,
//     subname,
//     nucleus_zo,
//     nucleus_us,
//     situs_comm,
//     year_effec,
//     total_lvg_field,
//     bedrooms,
//     baths,
//     addition_a,
//     garage_con,
//     garage_sta,
//     carport_st,
//     pool,
//     par_view,
//     usable_sq_field,
//     qual_class,
//     nucleus_si,
//     nucleus_1,
//     nucleus_2,
//     situs_zip,
//     overlay_ju,
//     sub_type,
//     multi,
//   }))(o)
// }
