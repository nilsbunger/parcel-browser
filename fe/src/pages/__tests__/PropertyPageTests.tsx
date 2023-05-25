import { afterAll, afterEach, beforeAll, beforeEach, describe, expect, jest, test } from "@jest/globals"
// import * as renderer from "react-test-renderer" // ES6 default import syntax won't work w/ commonjs module
import { render, waitFor } from "@testing-library/react"
import { setupServer } from "msw/node"
import { rest } from "msw"
import React from "react"
import PropertyDetailPage from "../PropertyDetailPage"
import { BrowserRouter, Route, useParams } from "react-router-dom"
import NewPropertyPage from "../NewPropertyPage"
import userEvent from "@testing-library/user-event"
import { act } from "react-dom/test-utils"

type ReactRouterDom = typeof BrowserRouter & {
  useParams: typeof useParams
  Route: typeof Route
}

const navigate = jest.fn()
const showNotification = jest.fn()

// Mock useParams which is called by the React component being tested. Lt others go through.
jest.mock("react-router-dom", () => {
  return {
    ...jest.requireActual<ReactRouterDom>("react-router-dom"),
    useParams: jest.fn(),
    useNavigate: jest.fn(),
  }
})

jest.mock("@mantine/notifications", () => {
  return {
    __esModule: true,
    showNotification: (opts: unknown) => showNotification(opts),
  }
})

jest.mock("@mapbox/search-js-react", () => ({
  __esModule: true,
  AddressAutofill: ({ children }: { children: React.ReactNode }) => {
    return (
      <div>
        <h2>MAPBOX autofill</h2>
        {children}
      </div>
    )
  },
  AddressMinimap: ({ children }: { children: React.ReactNode }) => {
    return (
      <div>
        <h2>MAPBOX map</h2>
        {children}
      </div>
    )
  },
}))

// Mock API calls --
const server = setupServer(
  // capture "GET /greeting" requests
  rest.get("http://test:5555/api/props/profiles/", (req, res, ctx) => {
    // User profile fetch -- act as if user is not logged in, returning a 401 status code and a JSON response body
    return res(ctx.status(401), ctx.json({ detail: "Unauthorized" }))
  }),
  rest.get("http://test:5555/api/properties/profiles/1", (req, res, ctx) => {
    // get property detail, send response.
    const s = fixtureData["random_property_detail"]
    console.log("RETURNING MOCKED PROPERTY DETAIL RESPONSE")
    return res(ctx.status(s.status), ctx.json(s.response))
  }),
  rest.post("http://test:5555/api/properties/profiles", (req, res, ctx) => {
    // create a new property
    const s = fixtureData["new_property_validation_extra_field_error"]
    console.log("RETURNING MOCKED NEW PROPERTY RESPONSE, VALIDATION ERROR WITH EXTRA FIELDS")
    return res(ctx.status(s.status), ctx.json(s.response))
  }),
  rest.get("http://test:5555/api/world/mapboxtoken", (req, res, ctx) => {
    // get a mapbox token
    return res(ctx.status(200), ctx.text("testtoken"))
  })
)

// establish API mocking before all tests
beforeAll(() => server.listen())
// reset any request handlers that are declared as a part of our tests
// (i.e. for testing one-time error scenarios)
afterEach(() => {
  jest.clearAllMocks()
  server.resetHandlers()
})

// clean up once the tests are done
afterAll(() => server.close())

beforeEach(() => {
  // jest.spyOn(router, "useNavigate").mockImplementation(() => navigate)
  ;(useParams as jest.Mock).mockReturnValue({ id: "1" })
})

describe("property details", () => {
  test("get property detail successfully", async () => {
    // react testing library examples: https://testing-library.com/docs/react-testing-library/example-intro
    // const component = renderer.create(<LoginPage />)
    const { getByText, findByText } = render(<PropertyDetailPage />)
    const el: HTMLElement = getByText("loading...")
    const el2: HTMLElement = await waitFor(() => findByText(/4 Dummy Rd/i))
  })
})

describe("new property", () => {
  test("show a validation error for extra fields", async () => {
    const user = userEvent.setup()

    const { getByText, getByLabelText, findByLabelText } = render(<NewPropertyPage />)
    const addrInput = (await findByLabelText(/^Street Address/)) as HTMLInputElement
    const cityInput = getByLabelText(/^City/) as HTMLInputElement
    const zipInput = getByLabelText(/^Zip Code/) as HTMLInputElement
    const submitButton = getByText("Add property") as HTMLButtonElement
    cityInput.readOnly = false
    zipInput.readOnly = false
    await act(async () => {
      await user.type(addrInput, "555 test prop dr")
      await user.type(cityInput, "New City")
      await user.type(zipInput, "12345")
      await user.click(submitButton)
    })

    expect(showNotification).toHaveBeenCalledWith({
      color: "red",
      message: "Invalid request to server (422)",
      title: "Submission failure",
    })
    expect(showNotification).toHaveBeenCalledTimes(1)
  })
})

const fixtureData = {
  random_property_detail: {
    status: 200,
    response: {
      address: {
        address_features: {},
        city: "La Honda",
        id: 4,
        state: "CA",
        street_addr: "4 Dummy Rd",
        zip: "94020",
      },
      id: 4,
      legal_entity: null,
    },
  },
  new_property_validation_extra_field_error: {
    status: 422,
    response: {
      detail: [
        {
          loc: ["body", "data", "features", "geometry", "interpolated"],
          msg: "extra fields not permitted",
          type: "value_error.extra",
        },
      ],
    },
  },
}
