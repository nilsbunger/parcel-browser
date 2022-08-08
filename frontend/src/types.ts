// Slowly build this up with the types that we need for the frontend
export type Listing = {
  apn: string;
  centroid_x: number;
  centroid_y: number;
  [key: string]: string | number | boolean;
};
