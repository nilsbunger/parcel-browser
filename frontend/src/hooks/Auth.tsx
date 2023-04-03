import * as React from "react"
import { createContext, useContext } from "react"
import { apiRequest, ApiResponse, fetcher } from "../utils/fetcher"
import useSWR from "swr"
import { LoginRequest, LoginRespDataCls, User } from "../types"
import { BACKEND_DOMAIN } from "../constants"
import { z } from "zod"

const authContext = createContext<AuthContextType | { user: null; isLoading: true }>({
  user: null,
  isLoading: true,
})

// useAuth hook:
export const useAuth = () => {
  return useContext(authContext) as AuthContextType
}

// Auth context provider:
export function AuthProvider({ children }: { children: React.ReactNode }) {
  const auth: AuthContextType = useAuthProvider()
  return <authContext.Provider value={auth}>{children}</authContext.Provider>
}

// Provider hook that creates auth object and handles state
function useAuthProvider() {
  // const [user, setUser] = useState(null);
  // const navigate = useNavigate();

  const { data, error, isValidating, mutate } = useSWR<User | null>(
    `${BACKEND_DOMAIN}/api/userflows/user`,
    fetcher,
    {
      // More SWR config options at https://swr.vercel.app/docs/api
      shouldRetryOnError: false, // disable error retry because it was hitting server over and over again.
      revalidateOnFocus: false,
    }
  )
  const user = data === undefined ? null : data
  const isLoading = isValidating
  // console.log("IsLoading=", isLoading)

  if (error) {
    const err = error.response
    if (err.status != 401) {
      // 401 is expected when user is not logged in
      console.log("useAuthProvider error on call to userflows/user:", err.status, " ", err.data)
    }
    // navigate("/login")
  }
  // console.log("Got user", user)
  const logIn = async (
    loginParameters: LoginRequest
  ): Promise<{
    errors: boolean | Record<string, string>
    data: z.infer<typeof LoginRespDataCls>
    message: string | null
  }> => {
    const { data, errors, message } = await apiRequest<typeof LoginRespDataCls>(`api/userflows/login`, {
      RespDataCls: LoginRespDataCls,
      isPost: true,
      body: loginParameters,
    })
    if (!errors) {
      await mutate(data?.user)
      // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
      return { data, errors, message }
    } else {
      // error (eg 401 (unauth'd), 422 (form validation errors), 500 (server error), xxx (network error)
      await mutate(null)
      return { data, errors, message }
    }
  }
  const signUp = async (/*email, password*/): Promise<void> => {
    console.error("Not implemented")
    return Promise.resolve()
  }
  const logOut = async () => {
    console.error("Not implemented")
    return Promise.resolve() // bogus return value to make async function ok
    // const fetchResponse = await apiRequest<typeof LogoutResponseSchema>(`api/userflows/logout`, {
    //   RespResponseCls: LogoutResponseSchema,
    //   isPost: true,
    // })
    // if (!fetchResponse.errors) {
    //   await mutate(null)
    // } else {
    //   console.log("Logout failed", fetchResponse)
    // }
  }
  const sendPasswordResetEmail = (/*email*/): Promise<void> => {
    console.error("Not implemented")
    return Promise.resolve()
  }
  const confirmPasswordReset = (/*code, password*/): Promise<void> => {
    console.error("Not implemented")
    return Promise.resolve()
  }

  // Return the user object and auth methods
  return {
    user,
    error,
    isLoading,
    logIn,
    logOut,
    signUp,
    sendPasswordResetEmail,
    confirmPasswordReset,
  }
}

export interface AuthContextType {
  user: User | null
  error: string | null
  isLoading: boolean
  logIn: (x: LoginRequest) => Promise<ApiResponse<typeof LoginRespDataCls>>
  logOut: () => Promise<void>
  signUp: (x: LoginRequest) => Promise<void>
  sendPasswordResetEmail: (x: string) => Promise<void>
  confirmPasswordReset: (x: string, y: string) => Promise<void>
}
