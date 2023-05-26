import { useForm, zodResolver } from "@mantine/form"
import useSWR from "swr"
import { apiRequest, fetcher } from "../utils/fetcher"
import * as React from "react"
import { useCallback, useState } from "react"
import { AddressAutofill, AddressMinimap } from "@mapbox/search-js-react"
import { TextInput } from "@mantine/core"
import { z } from "zod"
import { useNavigate } from "react-router-dom"
import { showNotification } from "@mantine/notifications"
import { ApiResponseSchema, NewPropertyRespDataCls } from "../types"

export const NewPropertyFormSchema = z.object({
  streetAddress: z.string(),
  city: z.string().min(4).max(40),
  zip: z.string().length(5).regex(/^\d+$/),
})
export type NewPropertyForm = z.infer<typeof NewPropertyFormSchema>

export const NewPropertyRespSchema = ApiResponseSchema.extend({
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
  const { data: accessToken, error } = useSWR<string, string>(`/api/world/mapboxtoken`, fetcher)

  const [showMinimap, setShowMinimap] = useState(true)
  const [feature, setFeature] = useState()
  const navigate = useNavigate()

  const handleRetrieve = useCallback(
    (res:any) => {
      console.log("Handle retrieve... features = ", res.features)
      const feature = res.features[0]
      setFeature(feature)
      setShowMinimap(true)
      // setShowFormExpanded(true);
    },
    [setFeature, setShowMinimap]
  )

  const handleChange = useCallback(
    (e: React.FormEvent<HTMLFormElement>) => {
      // remove autofill results when we see a change in the form.
      if (e.nativeEvent instanceof InputEvent) {
        setFeature(undefined)
      }
    },
    [setFeature]
  )

  const onSubmit = useCallback(
    async (newProperty: NewPropertyForm) => {
      // console.log("onSubmit: newProperty = ", newProperty)
      const { data, errors, message } = await apiRequest<typeof NewPropertyRespDataCls>(
        `/api/properties/profiles`,
        {
          RespDataCls: NewPropertyRespDataCls,
          isPost: true,
          body: { formFields: newProperty, features: feature },
        }
      )
      if (errors && typeof errors !== "boolean") {
        // field-level validation errors.
        if (errors.features) {
          // error in the maxpbox 'feature' field, not part of form -- unexpected
          showNotification({
            title: "Submission failure",
            message: "Couldn't process address",
            color: "red",
          })
        } else {
          console.log("Setting field errors = ", errors)
          form.setErrors(errors)
        }
      }
      if (!errors) {
        navigate("/properties")
      }
    },
    [feature]
  )
  if (error) return <div>failed to load mapbox token</div>
  if (!accessToken) return <div>loading mapbox token...</div>
  const disabledBtnClass = feature ? "" : " cursor-not-allowed opacity-30"

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
              <form className="space-y-4 md:space-y-6" onSubmit={form.onSubmit(onSubmit)} onChange={handleChange}>
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
                    readOnly
                    label="City"
                    placeholder="Los Angeles"
                    autoComplete="address-level2"
                    {...form.getInputProps("city")}
                  />
                </div>
                <div>
                  <TextInput
                    withAsterisk
                    readOnly
                    label="Zip Code"
                    placeholder="90001"
                    autoComplete="postal-code"
                    {...form.getInputProps("zip")}
                  />
                </div>
                {/*TODO : adopt Mantine button. Need to figure out styling. Give button tooltip like https://mantine.dev/core/button/ when disabled*/}
                <button
                  type="submit"
                  className={
                    "w-full btn btn-primary text-white bg-primary-600 hover:bg-primary-700 focus:ring-4 " +
                    "focus:outline-none focus:ring-primary-300 font-medium rounded-lg text-sm px-5 py-2.5 " +
                    "text-center dark:bg-primary-600 dark:hover:bg-primary-700 dark:focus:ring-primary-800" +
                    disabledBtnClass
                  }
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
