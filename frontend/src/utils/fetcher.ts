import axios, { type AxiosInstance } from "axios"
import { useCallback, useEffect, useRef } from "react"
import { z } from "zod"
import { BACKEND_DOMAIN } from "../constants";
import { Middleware, SWRHook } from "swr";

interface ApiRequestParams<RespSchema> {
  respSchema: RespSchema
  params?: any
  body?: any
  isPost: boolean
}

interface ApiResponse<RespSchema extends z.ZodTypeAny> {
  data: z.infer<RespSchema>
  errors: Record<string, string> | boolean
  unauthenticated?: boolean // request failed with 401, indicating user is not logged in
  message: string | null
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
 * @returns a struct with error (boolean), data (RespType), and message for user
 *
 */
export async function apiRequest<RespSchema extends z.ZodTypeAny>(
  url: string,
  { respSchema, isPost = false, params = {}, body = {} }: ApiRequestParams<RespSchema>
): Promise<ApiResponse<RespSchema>> {
  // Promise<{ data?:z.infer<typeof respSchema>, error: boolean, unauthenticated?: boolean, message?: string}> {
  // Note: Axios automatically sets content-type to application/json
  url = `${BACKEND_DOMAIN}/${url}`
  const req = isPost
    ? _axiosPost.post<RespSchema>(url, body, { params: params, timeout: 5000 })
    : _axiosGet.get<RespSchema>(url, { params: params, timeout: 5000 })

  const retval = req
    .then((res) => {
      // console.log ("api_post success. Response = ", res)
      const parsed: RespSchema = respSchema.parse(res.data)
      return { errors: false, data: parsed, message: null }
    })
    .catch(function (error) {
      // non-2xx response
      console.log("Error in apiRequest", error)
      // report unauthenticated (401) differently than insufficient permission
      const unauthenticated = error.response?.status == 401
      let validationErrors = {}
      if (error.response?.status == 422) {
        const validationErrorsRaw = error.response.data.detail
        // convert validation errors into a dict of fieldname -> error message
        validationErrors = Object.assign(
          {},
          // @ts-ignore
          ...validationErrorsRaw.map((x) => ({ [x.loc.at(-1)]: x.msg }))
        )
        console.log("errors = ", validationErrors)
      }
      return {
        unauthenticated,
        message: error.message,
        errors: validationErrors,
        data: null,
      }
    })
  return retval
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
    const laggyDataRef:any = useRef()

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
