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
  is_mf: boolean;
  is_tpa: boolean;
  [key: string]: string | number | boolean | object;
};

export type UnitRentData = { rent_mean: number, rent_75_percentile: number, num_samples: number }

// Record of single unit type (eg 3BR,2BA) to UnitRentData (mean, percentiles, etc)
export type UnitRentRate = Record<string, UnitRentData>


export type RentLocationRate = {
  lat: number;
  long: number;
  pid: string;  // parcel ID
  rents: UnitRentRate;
}
