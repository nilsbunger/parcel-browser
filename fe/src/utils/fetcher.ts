import axios, { type AxiosInstance, AxiosResponse } from "axios"
import { useCallback, useEffect, useRef } from "react"
import { z } from "zod"
import { Middleware, SWRHook } from "swr"
import { showNotification } from "@mantine/notifications"

interface ApiRequestParams<RespDataType extends z.ZodTypeAny> {
  RespDataCls: z.ZodTypeAny // TODO: should be RespDataType
  params?: any
  body?: any
  isPost: boolean
}

export interface ApiResponse<RespSchema extends z.ZodTypeAny> {
  data: z.infer<RespSchema> | null
  errors: Record<string, string> | boolean // form-level errors (if Record), or true/false
  unauthenticated?: boolean // request failed with 401, indicating user is not logged in
  message: string | null // message to display in page-level toast. red if 'errors' field is truthy, green otherwise
}

// Pydantic validation errors - defined at https://docs.pydantic.dev/usage/models/#error-handling
interface PydanticValidationError {
  // the error's location as a list, from root to leaf
  loc: string[]
  /** human-readable description of the error **/
  msg: string
  /** computer-readable identifier of the error type **/
  type: string
  /** object which contains values required to render the error message **/
  ctx?: any
}

/**
 * Sends a POST request with CSRF token included, and parses the response with Zod.
 *
 * @param url - The first input number
 * @param options - The second input number
 * @returns a struct with errors (boolean or a dict mapped to form data), data (RespType), and message toast for user
 *
 */
export async function apiRequest<RespDataType extends z.ZodTypeAny>(
  url: string,
  { RespDataCls, isPost = false, params = {}, body = {} }: ApiRequestParams<RespDataType>
): Promise<{ errors: boolean | Record<string, string>; data: any; message: string | null }> {
  // Promise<{ data?:z.infer<typeof respSchema>, error: boolean, unauthenticated?: boolean, message?: string}> {
  const ResponseCls = z.object({
    errors: z.union([z.boolean(), z.record(z.string(), z.string())]),
    data: RespDataCls,
    message: z.string().nullable(),
  })
  const req = isPost
    ? _axiosPost.post(url, body, { params: params, timeout: 5000 })
    : _axiosGet.get(url, { params: params, timeout: 5000 })

  // Make actual request
  const promiseReturn = await req
    .then((res: AxiosResponse<any>) => {
      // console.log ("api request success. Response = ", res)
      try {
        const { errors, data, message } = ResponseCls.parse(res.data)
        return { errors: errors, data: data, message: message, unauthenticated: false }
      } catch (e) {
        console.error("apiRequest: Error parsing response: ", e)
        return { errors: true, data: null, message: "Error parsing response", unauthenticated: false }
      }
    })
    .catch((error) => {
      // Axios raised error while sending request or receiving response over network... typically a non-2xx response
      // eg: 401 (unauthenticated) or 422 (pydantic validation error).
      console.log("Error in apiRequest request or response: ", error)

      // report unauthenticated (401) differently than insufficient permission
      const unauthenticated = error.response?.status == 401
      let validationErrors = {}
      if (error.response?.status == 422) {
        // pydantic / ninja validation error.
        const validationErrorsRaw = error.response.data.detail

        if (validationErrorsRaw.find((x: any) => x.type === "value_error.extra")) {
          // server error: extra fields in request body. treat as a page-level error.
          validationErrors = true // errors field is a boolean when it's a page-level error
          error.message = "Invalid request to server (422)"
        } else {
          // convert pydantic server errors into a dict of fieldname -> error message. keep only the leaf fieldname.
          validationErrors = Object.assign(
            {},
            // @ts-ignore
            ...validationErrorsRaw.map((x) => ({ [x.loc.at(-1)]: x.msg }))
          )
          console.log("errors = ", validationErrors)
        }
      }
      // return out of promise chain to top level.
      return {
        unauthenticated,
        message: error.message,
        errors: validationErrors,
        data: null,
      }
    })
  if (!promiseReturn.errors) {
    // no errors, show success toast
    showNotification({ title: "Success", message: promiseReturn.message, color: "green" })
  } else if (typeof promiseReturn.errors === "boolean") {
    // page level errors, show error toast. (field-level errors are handled by the caller)
    showNotification({ title: "Failure", message: promiseReturn.message, color: "red" })
  }
  return promiseReturn
}

type Fetcher = (url: string, config: Record<string, unknown>) => Promise<any>
export const fetcher: Fetcher = (url, config) => {
  // console.log ("FETCH " + url)
  return axios.get(url, config).then((res) => res.data)
}

// This is a SWR middleware for keeping the data even if key changes.
// From https://swr.vercel.app/docs/middleware#keep-previous-result
export const swrLaggy: Middleware = (useSWRNext: SWRHook) => {
  return (key, fetcher, config) => {
    // Use a ref to store previous returned data.
    const laggyDataRef: any = useRef()

    // Actual SWR hook.
    const swr = useSWRNext(key, fetcher, config)

    useEffect(() => {
      // Update ref if data is not undefined.
      if (swr.data !== undefined) {
        laggyDataRef.current = swr.data
      }
    }, [swr.data])

    // Expose a method to clear the laggy data, if any.
    const resetLaggy = useCallback(() => {
      laggyDataRef.current = undefined
    }, [])

    // Fallback to previous data if the current data is undefined.
    const dataOrLaggyData = swr.data === undefined ? laggyDataRef.current : swr.data

    // Is it showing previous data?
    const isLagging = swr.data === undefined && laggyDataRef.current !== undefined

    // Also add a `isLagging` field to SWR.
    return Object.assign({}, swr, {
      data: dataOrLaggyData,
      isLagging,
      resetLaggy,
    })
  }
}

const _axiosPost = axios.create({
  // baseURL: 'https://some-domain.com/api/',
  timeout: 5000,
  method: "post",
  headers: {
    Accept: "application/json",
  },
  xsrfHeaderName: "X-CSRFTOKEN", // django csrf header and cookie
  xsrfCookieName: "csrftoken",
})

const _axiosGet: AxiosInstance = axios.create({
  // baseURL: 'https://some-domain.com/api/',
  timeout: 5000,
  method: "get",
  headers: {
    Accept: "application/json",
  },
})
