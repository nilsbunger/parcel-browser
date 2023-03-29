// Slowly build this up with the types that we need for the frontend
import { z } from "zod"

export type Listing = {
  apn: string
  centroid_x: number
  centroid_y: number
  avail_geom_area: number
  potential_FAR: number
  metadata: { [key: string]: any }
  mlsid: string
  addr: string
  ba: string
  br: string
  founddate: string
  seendate: string
  neighborhood: string
  is_mf: boolean
  is_tpa: boolean
  [key: string]: string | number | boolean | object
}

export type UnitRentData = { rent_mean: number; rent_75_percentile: number; num_samples: number }

// Record of single unit type (eg 3BR,2BA) to UnitRentData (mean, percentiles, etc)
export type UnitRentRate = Record<string, UnitRentData>

export type RentLocationRate = {
  lat: number
  long: number
  pid: string // parcel ID
  rents: UnitRentRate
}

// **** API schemas and types **** //
// /api/<name> schemas and types

// generic API error response
export const ApiErrorSchema = z.object({
  error: z.string(),
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
  finances: DevScenarioFinanceSchema,
})
export type DevScenario = z.infer<typeof DevScenarioSchema>

export type RoadGetResp = z.infer<typeof RoadGetRespSchema>
export const RoadGetRespSchema = z.object({
  roadsegid: z.number(),
  segclass: z.string(),
  funclass: z.string(),
  segclass_decoded: z.string(),
  funclass_decoded: z.string(),
})

interface EligibilityCheckSchema {
  name?: string
  description?: string
  result?: string
  notes?: string[]
  children?: EligibilityCheckSchema[]
}

// Eligibility test result
export type EligibilityCheck = z.infer<typeof EligibilityCheckSchema>
export const EligibilityCheckSchema: z.ZodType<EligibilityCheckSchema> = z.lazy(() =>
  z.object({
    name: z.string(),
    description: z.string(),
    result: z.any(),
    notes: z.array(z.string()),
    children: z.array(EligibilityCheckSchema),
  })
)

export type ParcelGetResp = z.infer<typeof ParcelGetRespSchema>
export const ParcelGetRespSchema = z.object({
  apn: z.string(),
  apn_8: z.string(),
  own_name1: z.string(),
  own_name2: z.string(),
  own_name3: z.string(),
  fractint: z.number(),
  own_addr1: z.string(),
  own_addr2: z.string(),
  own_addr3: z.string(),
  own_addr4: z.string(),
  own_zip: z.string(),
  situs_juri: z.string(),
  situs_stre: z.string(),
  situs_suff: z.string(),
  situs_post: z.string(),
  situs_pre_field: z.string(),
  situs_addr: z.number(),
  situs_frac: z.string(),
  situs_buil: z.string(),
  situs_suit: z.string(),
  legldesc: z.string(),
  asr_land: z.number(),
  asr_impr: z.number(),
  asr_total: z.number(),
  acreage: z.number(),
  taxstat: z.string(),
  ownerocc: z.string(),
  tranum: z.string(),
  asr_zone: z.number(),
  asr_landus: z.number(),
  unitqty: z.number(),
  submap: z.string(),
  subname: z.string(),
  nucleus_zo: z.string(),
  nucleus_us: z.string(),
  situs_comm: z.string(),
  year_effec: z.string(),
  total_lvg_field: z.number(),
  bedrooms: z.string(),
  baths: z.string(),
  addition_a: z.number(),
  garage_con: z.string(),
  garage_sta: z.string(),
  carport_st: z.string(),
  pool: z.string(),
  par_view: z.string(),
  usable_sq_field: z.string(),
  qual_class: z.string(),
  nucleus_si: z.number(),
  nucleus_1: z.number(),
  nucleus_2: z.string(),
  situs_zip: z.string(),
  x_coord: z.number(),
  y_coord: z.number(),
  overlay_ju: z.string(),
  sub_type: z.number(),
  multi: z.string(),
  shape_star: z.number(),
  shape_stle: z.number(),
  ab2011_result: EligibilityCheckSchema,
  // geom: z.object() // not sure how to rep this yet.
})

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
  details: z
    .object({
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
      existing_units_with_rent: z.array(
        z.array(
          z.object({
            br: z.number(),
            ba: z.number(),
            sqft: z.number(),
          })
        )
      ),
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
    })
    .passthrough(), // 'passthrough' allows extra keys through
})
export type _analysis_get_resp = z.infer<typeof AnalysisGetRespSchema>
export type AnalysisGetResp = _analysis_get_resp & Record<string, any>

// /api/analysis
export const AnalysisPostRespSchema = z.object({
  analysisId: z.number(),
})
export type AnalysisPostResp = z.infer<typeof AnalysisPostRespSchema>

export const AnalysisPostReqSchema = z.object({
  // APN id
  apn: z.string().optional(),
  // analyzed listing ID
  al_id: z.number().optional(),
})
export type AnalysisPostReq = z.infer<typeof AnalysisPostReqSchema>
// type AnalysisPostResp = z.infer<typeof AnalysisPostRespSchema>

// /api/world/address-search
export const AddressSearchGetRespSchema = z.union([
  ApiErrorSchema,
  z.object({
    address: z.string(),
    apn: z.string(),
    analyzed_listing: z.number(),
  }),
])
export type AddressSearchGetResp = z.infer<typeof AddressSearchGetRespSchema>

export const UserSchema = z.object({
  first_name: z.string(),
  last_name: z.string(),
  email: z.string(),
})
export type User = z.infer<typeof UserSchema>

export const ApiResponseSchema = z.object({
  // TODO: I think we can remove this... follow pattern in LoginPage.
  errors: z.union([z.boolean(), z.object({})]),
  message: z.string().nullable(),
})
export const LoginRespDataCls = z.object({ user: UserSchema.nullable() })
export type LoginResponse = z.infer<typeof LoginRespDataCls>

export const NewPropertyRespDataCls = z.object({
  id: z.number(),
})
export type NewPropertyResponse = z.infer<typeof NewPropertyRespDataCls>

export const LoginRequestSchema = z.object({
  email: z.string().email(),
  password: z.string().min(4).max(24),
  rememberMe: z.boolean(),
})
export type LoginRequest = z.infer<typeof LoginRequestSchema>

export const LogoutResponseSchema = ApiResponseSchema.extend({})
export type LogoutResponse = z.infer<typeof LogoutResponseSchema>
