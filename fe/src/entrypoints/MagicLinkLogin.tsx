import React from "react"

import { Checkbox, MantineProvider, TextInput } from "@mantine/core"
import { MagicLinkLoginRequest, MagicLinkLoginRequestSchema } from "../types"
import { AuthContextType, AuthProvider, useAuth } from "../hooks/Auth"
import { useForm, zodResolver } from "@mantine/form"
import { showNotification } from "@mantine/notifications"
import { createRoot } from "react-dom/client";

const loginElement = document.getElementById("login_react_div")
// eslint-disable-next-line @typescript-eslint/no-non-null-assertion
const root = createRoot(loginElement!); // createRoot(container!) if you use TypeScript
root.render(<MagicLinkLoginWrapper/>)

export function MagicLinkLoginWrapper() {
  return (
    <MantineProvider>
      <AuthProvider>
        <MagicLinkLogin />
      </AuthProvider>
    </MantineProvider>
  )
}
export function MagicLinkLogin() {
  const form = useForm({
    validate: zodResolver(MagicLinkLoginRequestSchema),
    initialValues: {
      email: "",
      password: "",
      rememberMe: false,
    },
  })
  const [isEmailSent, setIsEmailSent] = React.useState(false)
  // console.log("Client form errors:", errors)
  const { logIn } = useAuth() as AuthContextType
  const onSubmit = async (loginData: MagicLinkLoginRequest) => {
    // console.log("on submit", loginData)
    const { errors, message, data } = await logIn(loginData)
    if (errors) {
      if (message) showNotification({ title: "Login failure", message, color: "red" })
      if (typeof errors === "object") form.setErrors(errors)
    } else {
      // successful login
      if (message) showNotification({ title: "Success", message, color: "green" })
      setIsEmailSent(true)
      // window.location.href = "/properties"
    }
  }

  return (
    <div className="flex flex-col items-center justify-center md:px-6 py-8 mx-auto lg:py-0">
      <div className="w-full rounded-lg bg-white shadow md:mt-0 sm:max-w-md xl:p-0">
        <div className="p-6 space-y-4 md:space-y-6 sm:p-8">
          {isEmailSent && (
            <div className="text-center">
              <h2>Welcome to Turboprop! </h2>
              <p>Check your email for a link to login</p>
            </div>
          )}
          {!isEmailSent && (
            <>
              <h2>Sign in or sign up</h2>
              <form className="space-y-4 md:space-y-6" onSubmit={form.onSubmit(onSubmit)}>
                <div>
                  <TextInput
                    withAsterisk
                    label="Your email"
                    placeholder="example@mail.com"
                    {...form.getInputProps("email")}
                  />
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-start">
                    <div className="flex items-center h-5">
                      <Checkbox label={"Remember me"} {...form.getInputProps("rememberMe")} />
                    </div>
                  </div>
                </div>
                <button
                  type="submit"
                  className="w-full btn btn-primary focus:ring-4 focus:outline-none focus:ring-primary-300"
                >
                  Sign in
                </button>
              </form>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
