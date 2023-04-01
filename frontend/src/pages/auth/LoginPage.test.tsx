import { afterAll, afterEach, beforeAll, beforeEach, describe, expect, jest, test } from "@jest/globals"
// import * as renderer from "react-test-renderer" // ES6 default import syntax won't work w/ commonjs module
import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import * as router from "react-router"
import LoginPage from "./LoginPage"
import { setupServer } from "msw/node"
import { rest } from "msw"
import React from "react"
import { AuthProvider } from "../../hooks/Auth"
// import { act } from "react-test-renderer"
import { act } from "react-dom/test-utils"

const navigate = jest.fn()
const apicall = jest.fn()

const loginScenarios = {
  server_side_password_val_fail: {
    // failure by pydantic on server. 422 status code, JSON response body which should be sent to the form fields.
    status: 422,
    response: {
      detail: [
        {
          loc: ["body", "payload", "password"],
          msg: "more than 8 chars plz",
          type: "value_error.any_str.min_length",
          ctx: { limit_value: 8 },
        },
      ],
    },
  },
  client_side_password_val_fail: {},
  success: {
    // success. 200 status code.
    status: 200,
    response: {
      errors: false,
      message: "Login successful",
      data: { user: { first_name: "Nils", last_name: "Bunger", email: "nils@home3.co" } },
    },
  },
}

// declare which API requests to mock
const server = setupServer(
  // capture "GET /greeting" requests
  rest.get("http://test:5555/api/userflows/user", (req, res, ctx) => {
    // User profile fetch -- act as if user is not logged in, returning a 401 status code and a JSON response body
    return res(ctx.status(401), ctx.json({ detail: "Unauthorized" }))
  }),
  rest.post("http://test:5555/api/userflows/login", (req, res, ctx) => {
    // Respond with a successful login by default
    const s = loginScenarios["success"]
    console.log("MOCKING LOGIN API WITH SUCCESS")
    return res(ctx.status(s.status), ctx.json(s.response))
  })
)

// establish API mocking before all tests
beforeAll(() => server.listen())
// reset any request handlers that are declared as a part of our tests
// (i.e. for testing one-time error scenarios)
afterEach(() => server.resetHandlers())
// clean up once the tests are done
afterAll(() => server.close())

beforeEach(() => {
  jest.spyOn(router, "useNavigate").mockImplementation(() => navigate)
})

describe("login test module", () => {
  test("first test", () => {
    // react testing library examples: https://testing-library.com/docs/react-testing-library/example-intro
    // const component = renderer.create(<LoginPage />)
    render(<LoginPage />)
    expect(1 + 2).toBe(3)
    screen.getByText("Sign in")
    // expect(navigate).toHaveBeenCalledWith('/path')
  })

  test("test handling of success response from backend", async () => {
    const user = userEvent.setup()
    render(
      <AuthProvider>
        <LoginPage />
      </AuthProvider>
    )
    const emailInput = screen.getByLabelText(/^Your email/)
    const passwordInput = screen.getByLabelText(/^Your password/)
    const submitButton = screen.getByText("Sign in")
    await act(async () => {
      await user.type(emailInput, "foo@bar.com")
      await user.type(passwordInput, "password")
      await user.click(submitButton)
    })
    // generate a mock response to the login call from the server
    expect(navigate).toHaveBeenCalledWith("/properties")
  })

  test("test handling of validation failure from backend", async () => {
    server.use(
      rest.post("/login", (req, res, ctx) => {
        const s = loginScenarios["server_side_password_val_fail"]
        console.log("MOCKING LOGIN API WITH SERVER-SIDE VALIDATION FAILURE")
        return res(ctx.status(s.status), ctx.json(s.response))
      })
    )
    const user = userEvent.setup()
    render(
      <AuthProvider>
        <LoginPage />
      </AuthProvider>
    )
    const emailInput = screen.getByLabelText(/^Your email/)
    const passwordInput = screen.getByLabelText(/^Your password/)
    const submitButton = screen.getByText("Sign in")
    await act(async () => {
      await user.type(emailInput, "foo@bar.com")
      await user.type(passwordInput, "password")
      await user.click(submitButton)
    })
    // generate a mock response to the login call from the server
    expect(navigate).toHaveBeenCalledWith("/properties")
  })
})
