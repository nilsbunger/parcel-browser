// Slowly build this up with the types that we need for the frontend
import { z } from "zod";

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

// **** API schemas and types **** //
// /api/<name> schemas and types

// generic API error response
export const ApiErrorSchema = z.object({
  error: z.string()
})

export const PropertyListingSchema = z.object({
  price: z.number(),
  br: z.number(),
  ba: z.number(),
  founddate: z.date(),
  seendate: z.date(),
  neighborhood: z.string(),
  mlsid: z.string(),
  size: z.number(),
  thumbnail: z.string().url(),
  status: z.string(),
})

export const FinanceLineItemSchema = z.tuple([
  z.string(), // name of line item
  z.number(), // value of line item
  z.string(), // notes / description of line item
])
export type FinanceLineItem = z.infer<typeof FinanceLineItemSchema>

export const DevScenarioFinanceSchema = z.object({
  cap_rate: z.number(),
  net_income: z.number(),
  capital_sum: z.number(),
  capital_flow: z.object({
    acquisition: z.array(FinanceLineItemSchema),
    construction: z.array(FinanceLineItemSchema),
  }),
  operating_flow: z.array(FinanceLineItemSchema),
})
export type DevScenarioFinance = z.infer<typeof DevScenarioFinanceSchema>

export const DevScenarioSchema = z.object({
  adu_qty: z.number(),
  unit_type: z.object({
    br: z.number(),
    ba: z.number(),
    sqft: z.number(),
    stories: z.number(),
    lotspace_required: z.number(),
  }),
  finances: DevScenarioFinanceSchema
})
export type DevScenario = z.infer<typeof DevScenarioSchema>

export const AnalysisGetRespSchema = z.object({
  datetime_ran: z.date(),
  is_tpa: z.boolean(),
  is_mf: z.boolean(),
  zone: z.string(),
  salt: z.string(),
  centroid: z.array(z.number()).length(2),
  listing: PropertyListingSchema,
  apn: z.string(),
  dev_scenarios: z.array(DevScenarioSchema),
  details: z.object({
    address: z.string(),
    parcel_size: z.number(),
    garages: z.number(),
    carports: z.number(),
    existing_FAR: z.number(),
    max_FAR: z.number(),
    avail_area_by_FAR: z.number(),
    avail_geom_area: z.number(),
    existing_living_area: z.number(),
    can_lot_split: z.boolean(),
    existing_units_with_rent: z.array(z.array(z.object({
      br: z.number(),
      ba: z.number(),
      sqft: z.number(),
    }))),
    re_params: z.object({
      constr_costs: z.object({
        soft_cost_rate: z.number(),
        build_cost_two_story: z.number(),
        build_cost_single_story: z.number(),
      }),
      vacancy_rate: z.number(),
      prop_tax_rate: z.number(),
      mgmt_cost_rate: z.number(),
      repair_cost_rate: z.number(),
      insurance_cost_rate: z.number(),
      new_unit_rent_percentile: z.number(),
      existing_unit_rent_percentile: z.number(),
    }),
    messages: z.object({
      warning: z.array(z.string()),
      info: z.array(z.string()),
      note: z.array(z.string()),
      error: z.array(z.string()),
    }),
  }).passthrough(), // 'passthrough' allows extra keys through
})
export type AnalysisGetResp = z.infer<typeof AnalysisGetRespSchema>

// /api/analysis
export const AnalysisPostRespSchema = z.object({
  analysisId: z.number()
})
export const AnalysisPostReqSchema = z.object({
  // APN id
  apn: z.string().optional(),
  // analyzed listing ID
  al_id: z.number().optional(),
})
export type AnalysisPostReq = z.infer<typeof AnalysisPostReqSchema>
// type AnalysisPostResp = z.infer<typeof AnalysisPostRespSchema>

// /api/address-search
export const AddressSearchGetRespSchema = z.union([
  ApiErrorSchema,
  z.object({
    address: z.string(),
    apn: z.string(),
    analyzed_listing: z.number()
  })
])
export type AddressSearchGetResp = z.infer<typeof AddressSearchGetRespSchema>
