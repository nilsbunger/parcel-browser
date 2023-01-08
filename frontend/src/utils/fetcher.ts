import axios from 'axios';
import { useRef, useEffect, useCallback } from 'react';
import { z } from "zod";

/**
 * Sends a POST request with CSRF token included, and parses the response with Zod.
 *
 * @param url - The first input number
 * @param options - The second input number
 * @returns a struct with success (boolean), data (RespType), and message for user (error message if success is false)
 *
 */
export async function api_post<RespType> (url, {RespSchema, params = {}, body = {}}):
  Promise<{ data?:RespType, error: boolean, unauthenticated?: boolean, message?: string}> {
  // Note: Axios automatically sets content-type to application/json
  const retval = axiosPost
    .post<RespType>(url, body, { params: params, timeout:25000})
    .then((res) => {
      // console.log ("api_post success. Response = ", res)
      const parsed:RespType = RespSchema.parse(res.data)
      return {error: false, data: parsed, message: null}
    })
    .catch(function (error) {
      // non-2xx response
      console.log ("Error in api_post", error);
      // report unauthenticated (401) differently than insufficient permission
      const unauthenticated = error.response?.status == 401
      return {error: true, unauthenticated, message: error.message, data: null}
    } )
  return retval;
}

export async function api_get<RespType> (url, {RespSchema, params = {}}):
  Promise<{ data?:RespType, error: boolean, unauthenticated?: boolean, message?: string}> {
  const retval = axiosGet
    .get<RespType>(url, { params: params, timeout:5000})
    .then((res) => {
      console.log ("api_get success. Response = ", res)
      const parsed:RespType = RespSchema.parse(res.data)
      return {error: false, data: parsed, message: null}
    })
    .catch(function (error) {
      // non-2xx response
      console.log ("Error in api_get", error);
      // report unauthenticated (401) differently than insufficient permission
      const unauthenticated = error.response?.status == 401
      return {error: true, unauthenticated, message: error.message, data: null}
    } )
  return retval;

  }

export const fetcher = (url, config) =>
  axios.get(url, config).then((res) => res.data);

// This is a SWR middleware for keeping the data even if key changes.
// From https://swr.vercel.app/docs/middleware#keep-previous-result
export function swrLaggy(useSWRNext) {
  return (key, fetcher, config) => {
    // Use a ref to store previous returned data.
    const laggyDataRef = useRef();

    // Actual SWR hook.
    const swr = useSWRNext(key, fetcher, config);

    useEffect(() => {
      // Update ref if data is not undefined.
      if (swr.data !== undefined) {
        laggyDataRef.current = swr.data;
      }
    }, [swr.data]);

    // Expose a method to clear the laggy data, if any.
    const resetLaggy = useCallback(() => {
      laggyDataRef.current = undefined;
    }, []);

    // Fallback to previous data if the current data is undefined.
    const dataOrLaggyData = swr.data === undefined ? laggyDataRef.current : swr.data;

    // Is it showing previous data?
    const isLagging = swr.data === undefined && laggyDataRef.current !== undefined;

    // Also add a `isLagging` field to SWR.
    return Object.assign({}, swr, {
      data: dataOrLaggyData,
      isLagging,
      resetLaggy,
    });
  };
}

const axiosPost = axios.create({
  // baseURL: 'https://some-domain.com/api/',
  timeout: 5000,
  method: 'post',
  headers: {
    'Accept': 'application/json',
  },
  xsrfHeaderName: 'X-CSRFTOKEN',   // django csrf header and cookie
  xsrfCookieName: 'csrftoken'
});

const axiosGet = axios.create({
  // baseURL: 'https://some-domain.com/api/',
  timeout: 5000,
  method: 'get',
  headers: {
    'Accept': 'application/json',
  },
});
