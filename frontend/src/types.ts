// Slowly build this up with the types that we need for the frontend
export type Listing = {
  apn: string;
  centroid_x: number;
  centroid_y: number;
  avail_geom_area: number;
  potential_FAR: number;
  metadata: object;
  mlsid: string;
  addr: string;
  ba: string;
  br: string;
  founddate: string,
  seendate: string,
  neighborhood: string,

  [key: string]: string | number | boolean | object;
};
