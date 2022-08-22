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
  founddate: string;
  seendate: string;
  neighborhood: string;

  [key: string]: string | number | boolean | object;
};

// Record of single unit type (eg 3BR,2BA) to RentRate (mean, percentiles, etc)
// export type UnitRentRate = Record<string, Record<"rent_mean" | "rent_75_percentile", number>>
export type UnitRentRate = Record<string, any>

export type RentLocationRate = {
  lat: number;
  long: number;
  pid: string;  // parcel ID
  rents : UnitRentRate;
}
