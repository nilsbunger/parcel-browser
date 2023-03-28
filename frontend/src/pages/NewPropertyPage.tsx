import { useForm, zodResolver } from "@mantine/form"
import useSWR from "swr"
import { BACKEND_DOMAIN } from "../constants"
import { apiRequest, fetcher } from "../utils/fetcher"
import * as React from "react"
import { useCallback, useState } from "react"
import { AddressAutofill, AddressMinimap } from "@mapbox/search-js-react"
import { TextInput } from "@mantine/core"
import { z } from "zod"
import { LoginResponseSchema, UserSchema } from "../types"

export const NewPropertyFormSchema = z.object({
  streetAddress: z.string(),
  city: z.string().min(4).max(24),
  zip: z.string().length(5).regex(/^\d+$/),
})
export type NewPropertyForm = z.infer<typeof NewPropertyFormSchema>

export const NewPropertyRespSchema = z.object({
  success: z.boolean(),
  message: z.string().nullable(),
  formErrors: z.object({}).nullable().optional(),
  // user: UserSchema.nullable(),
})
export type NewPropertyResp = z.infer<typeof NewPropertyRespSchema>

export default function NewPropertyPage() {
  // Mapbox address autofill component.
  // see also https://docs.mapbox.com/mapbox-search-js/api/react/autofill/
  const form = useForm({
    validate: zodResolver(NewPropertyFormSchema),
    initialValues: {
      streetAddress: "",
      city: "",
      zip: "",
    },
  })
  const { data: accessToken, error } = useSWR<string, string>(
    `${BACKEND_DOMAIN}/api/world/mapboxtoken`,
    fetcher
  )

  const [showMinimap, setShowMinimap] = useState(true)
  const [feature, setFeature] = useState()

  const handleRetrieve = useCallback(
    (res) => {
      console.log("Handle retrieve... features = ", res.features)
      const feature = res.features[0]
      setFeature(feature)
      setShowMinimap(true)
      // setShowFormExpanded(true);
    },
    []
    // [setFeature, setShowMinimap]
  )

  const tempFeature = {
    type: "Feature",
    properties: {
      accuracy: "rooftop",
      mapbox_id: "dXJuOm1ieGFkcjo0MDE3NTRlNi02NzNjLTQzMDQtYThhNS0wYTliZmI3NDc0Yzc=",
      match_code: {
        exact_match: false,
        house_number: "matched",
        street: "unmatched",
        postcode: "unmatched",
        place: "unmatched",
        region: "unmatched",
        locality: "not_applicable",
        country: "inferred",
        confidence: "low",
      },
      place_type: ["address"],
      place_name: "555 College Avenue, Palo Alto, California 94306, United States",
      address_number: "555",
      street: "College Avenue",
      context: [
        {
          id: "neighborhood.127036652",
          mapbox_id: "dXJuOm1ieHBsYzpCNUpzN0E",
          text_en: "College Terrace",
          text: "College Terrace",
        },
        {
          id: "postcode.313356012",
          mapbox_id: "dXJuOm1ieHBsYzpFcTF1N0E",
          text_en: "94306",
          text: "94306",
        },
        {
          id: "place.250554604",
          wikidata: "Q47265",
          mapbox_id: "dXJuOm1ieHBsYzpEdThvN0E",
          text_en: "Palo Alto",
          language_en: "en",
          text: "Palo Alto",
          language: "en",
        },
        {
          id: "district.20686572",
          wikidata: "Q110739",
          mapbox_id: "dXJuOm1ieHBsYzpBVHVtN0E",
          text_en: "Santa Clara County",
          language_en: "en",
          text: "Santa Clara County",
          language: "en",
        },
        {
          id: "region.419052",
          short_code: "US-CA",
          wikidata: "Q99",
          mapbox_id: "dXJuOm1ieHBsYzpCbVRz",
          text_en: "California",
          language_en: "en",
          text: "California",
          language: "en",
        },
        {
          id: "country.8940",
          short_code: "us",
          wikidata: "Q30",
          mapbox_id: "dXJuOm1ieHBsYzpJdXc",
          text_en: "United States",
          language_en: "en",
          text: "United States",
          language: "en",
        },
      ],
      id: "address.8098767896859408",
      external_ids: {
        carmen: "address.8098767896859408",
        federated: "carmen.address.8098767896859408",
      },
      feature_name: "555 College Avenue",
      matching_name: "555 College Avenue",
      description: "Palo Alto, California 94306, United States",
      metadata: {
        iso_3166_2: "US-CA",
        iso_3166_1: "us",
      },
      language: "en",
      maki: "marker",
      neighborhood: "College Terrace",
      postcode: "94306",
      place: "Palo Alto",
      district: "Santa Clara County",
      region: "California",
      region_code: "CA",
      country: "United States",
      country_code: "us",
      full_address: "555 College Avenue, Palo Alto, California 94306, United States",
      address_line1: "555 College Avenue",
      address_line2: "",
      address_line3: "",
      address_level1: "CA",
      address_level2: "Palo Alto",
      address_level3: "College Terrace",
      postcode_plus: "1433",
      is_deliverable: true,
      missing_unit: false,
    },
    text_en: "College Avenue",
    geometry: {
      type: "Point",
      coordinates: [-122.147775, 37.42552],
    },
  }
  const tempNewProperty = {
    streetAddress: "555 College Avenue",
    city: "Palo Alto",
    zip: "94306",
  }

  const onSubmit = useCallback(async (newProperty: NewPropertyForm) => {
    console.log("on submit", newProperty)
    const { data, errors, message } = await apiRequest<typeof NewPropertyRespSchema>(
      `api/properties/profiles`,
      {
        respSchema: NewPropertyRespSchema,
        isPost: true,
        body: { formFields: tempNewProperty, features: tempFeature },
      }
    )

    // const { success, message, formErrors } = await logIn(loginData)
    // if (!success) {
    //   showNotification({ title: "Login failure", message, color: "red" })
    //   if (formErrors) {
    //     form.setErrors(formErrors) // note: this can also take a previous->next mapping function
    //   }
    // } else {
    //   navigate("/listings")
    // }
  }, [])

  if (error) return <div>failed to load mapbox token</div>
  if (!accessToken) return <div>loading mapbox token...</div>

  return (
    <div>
      <section className="dark:bg-gray-900 py-10">
        <div className="flex flex-row items-stretch justify-center md:px-6 py-8 mx-auto lg:py-0">
          {/* Form */}
          <div className="w-full bg-white rounded-lg shadow border md:mt-0 sm:max-w-md xl:p-0 dark:bg-gray-800 dark:border-gray-600 border-gray-400">
            <div className="p-6 space-y-4 md:space-y-6 sm:p-8">
              <h1 className="text-xl font-bold leading-tight tracking-tight text-gray-900 md:text-2xl dark:text-white">
                Add a property
              </h1>
              <button className="btn btn-primary" onClick={() => onSubmit(null)}>
                Test submit
              </button>
              <form className="space-y-4 md:space-y-6" onSubmit={form.onSubmit(onSubmit)}>
                <div>
                  <AddressAutofill accessToken={accessToken} onRetrieve={handleRetrieve}>
                    <TextInput
                      withAsterisk
                      label="Street Address"
                      placeholder="123 Main St"
                      autoComplete="address-line1"
                      {...form.getInputProps("streetAddress")}
                    />
                  </AddressAutofill>
                </div>
                <div>
                  <TextInput
                    withAsterisk
                    label="City"
                    placeholder="Los Angeles"
                    autoComplete="address-level2"
                    {...form.getInputProps("city")}
                  />
                </div>
                <div>
                  <TextInput
                    withAsterisk
                    label="Zip Code"
                    placeholder="90001"
                    autoComplete="postal-code"
                    {...form.getInputProps("zip")}
                  />
                </div>
                <button
                  type="submit"
                  className="w-full btn btn-primary text-white bg-primary-600 hover:bg-primary-700 focus:ring-4 focus:outline-none focus:ring-primary-300 font-medium rounded-lg text-sm px-5 py-2.5 text-center dark:bg-primary-600 dark:hover:bg-primary-700 dark:focus:ring-primary-800"
                >
                  Add property
                </button>
              </form>
            </div>
          </div>

          {/* Visual confirmation map */}
          <div
            id="minimap-container"
            className="grow"
            // className="!w-96 !h-full relative"
          >
            <AddressMinimap
              canAdjustMarker={true}
              satelliteToggle={true}
              feature={feature}
              accessToken={accessToken}
              show={showMinimap}
              // onSaveMarkerLocation={handleSaveMarkerLocation}
            />
          </div>
        </div>
      </section>
    </div>
  )
}
