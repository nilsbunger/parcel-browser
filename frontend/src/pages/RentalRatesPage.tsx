import useSWR from "swr"
import * as React from "react"
import { fetcher, swrLaggy } from "../utils/fetcher"
import RentalRatesMap from "../components/layout/RentalRatesMap"

export default function RentalRatesPage() {
  const { data, error, isValidating } = useSWR(
    [
      "/api/rentalrates",
      {
        params: {},
      },
    ],
    fetcher
  )

  if (error)
    return (
      <div className="md:container px-8 lg:px-16 pt-2">
        <h2>Failed to load</h2>
        <p>
          Try <a href="/dj/accounts/login/">logging in?</a>
        </p>
      </div>
    )
  if (!data) return <div>Loading...</div>

  // Render each date as a separate table
  return <RentalRatesMap rentalRates={data} />
}
