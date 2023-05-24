import * as React from "react"
import { AuthContextType, useAuth } from "../../hooks/Auth"
import { showNotification } from "@mantine/notifications"
import { useNavigate } from "react-router"
import { type LoginRequest, LoginRequestSchema } from "../../types"
import { useForm, zodResolver } from "@mantine/form"
import { Button, Checkbox, PasswordInput, TextInput } from "@mantine/core"

// Originally from Flowbite free: https://flowbite.com/blocks/marketing/login/#}

export default function LoginPage() {
  const form = useForm({
    validate: zodResolver(LoginRequestSchema),
    initialValues: {
      email: "",
      password: "",
      rememberMe: false,
    },
  })
  const navigate = useNavigate()
  // console.log("Client form errors:", errors)
  const { logIn } = useAuth() as AuthContextType
  // const onSubmit = data => console.log(data);
  const onSubmit = async (loginData: LoginRequest) => {
    // console.log("on submit", loginData)

    const { errors, message, data } = await logIn(loginData)
    if (errors) {
      if (message) showNotification({ title: "Login failure", message, color: "red" })
      if (typeof errors === "object") form.setErrors(errors)
    } else {
      // successful login
      if (message) showNotification({ title: "Login success", message, color: "green" })
      navigate("/properties")
    }
  }

  return (
    <>
      <section>
        <div className="flex flex-col items-center justify-center md:px-6 py-8 mx-auto lg:py-0">
          <div className="w-full bg-white rounded-lg shadow dark:border md:mt-0 sm:max-w-md xl:p-0 dark:bg-gray-800 dark:border-gray-700">
            <div className="p-6 space-y-4 md:space-y-6 sm:p-8">
              <h1 className="text-xl font-bold leading-tight tracking-tight md:text-2xl dark:text-white">
                Sign in to your account
              </h1>
              <form className="space-y-4 md:space-y-6" onSubmit={form.onSubmit(onSubmit)}>
                <div>
                  <TextInput
                    withAsterisk
                    label="Your email"
                    placeholder="example@mail.com"
                    {...form.getInputProps("email")}
                  />
                </div>
                <div>
                  <PasswordInput
                    withAsterisk
                    label="Your password"
                    placeholder="********"
                    {...form.getInputProps("password")}
                  />
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-start">
                    <div className="flex items-center h-5">
                      <Checkbox label={"Remember me"} {...form.getInputProps("rememberMe")} />
                    </div>
                  </div>
                  <a href="#" className="text-sm font-medium hover:underline dark:text-primary-500">
                    Forgot password?
                  </a>
                </div>
                <button
                  type="submit"
                  className="w-full btn btn-primary text-white bg-primary-600 hover:bg-primary-700 focus:ring-4 focus:outline-none focus:ring-primary-300 font-medium rounded-lg text-sm px-5 py-2.5 text-center dark:bg-primary-600 dark:hover:bg-primary-700 dark:focus:ring-primary-800"
                >
                  Sign in
                </button>
                <p className="text-sm font-light text-gray-600 dark:text-gray-400">
                  Don’t have an account yet?{" "}
                  <a href="#" className="font-medium text-primary-600 hover:underline dark:text-primary-500">
                    Sign up
                  </a>
                </p>
              </form>
            </div>
          </div>
        </div>
      </section>
    </>
  )
}
