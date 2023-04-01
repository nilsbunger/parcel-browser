import { afterAll, afterEach, beforeAll, beforeEach, describe, jest, test } from "@jest/globals"
// import * as renderer from "react-test-renderer" // ES6 default import syntax won't work w/ commonjs module
import { render, screen, act, waitFor } from "@testing-library/react"
import * as router from "react-router"
import { setupServer } from "msw/node"
import { rest } from "msw"
import React from "react"
// import { act } from "react-test-renderer"
import PropertyDetailPage from "./PropertyDetailPage"
import { BrowserRouter, Route, useParams } from "react-router-dom"

type ReactRouterDom = typeof BrowserRouter & {
  useParams: typeof useParams
  Route: typeof Route
}

const navigate = jest.fn()
const apicall = jest.fn()

// Mock useParams which is called by the React component being tested. Lt others go through.
jest.mock("react-router-dom", () => {
  return {
    ...jest.requireActual<ReactRouterDom>("react-router-dom"),
    useParams: jest.fn(),
  }
})

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
    console.log("MOCKED PROPERTY DETAIL RESPONSE")
    return res(ctx.status(s.status), ctx.json(s.response))
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
  jest.spyOn(router, "useNavigate").mockImplementation(() => navigate)
  ;(useParams as jest.Mock).mockReturnValue({ id: "1" })
})

describe("property detail test", () => {
  test("get property detail successfully", async () => {
    // react testing library examples: https://testing-library.com/docs/react-testing-library/example-intro
    // const component = renderer.create(<LoginPage />)
    const { getByText, findByText } = render(<PropertyDetailPage />)
    const el: HTMLElement = getByText("loading...")
    const el2: HTMLElement = await waitFor(() => findByText(/4 Dummy Rd/i))
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
}
