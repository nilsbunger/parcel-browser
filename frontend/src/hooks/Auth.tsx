import * as React from "react"
import { createContext, useContext } from "react"
import { apiRequest, fetcher } from "../utils/fetcher"
import useSWR from "swr"
import { LoginRequest, LoginResponse, LoginResponseSchema, LogoutResponseSchema, User } from "../types"
import { BACKEND_DOMAIN } from "../constants"

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
    console.log("useAuthProvider error on call to userflows/user", error)
    // navigate("/login")
  }
  // console.log("Got user", user)
  const logIn = async (loginParameters: LoginRequest): Promise<LoginResponse> => {
    const { data, errors, message } = await apiRequest<typeof LoginResponseSchema>(
      `api/userflows/login`,
      {
        respSchema: LoginResponseSchema,
        isPost: true,
        body: loginParameters,
      }
    )
    if (!errors) {
      await mutate(data?.user)
      return data
    } else {
      // error (eg 401 (unauth'd), 422 (or 500)
      await mutate(null)
      return { user: null, success: false, message: message, formErrors: errors }
    }
  }
  const signUp = async (/*email, password*/): Promise<void> => {
    console.error("Not implemented")
    // return firebase
    //   .auth()
    //   .createUserWithEmailAndPassword(email, password)
    //   .then((response) => {
    //     setUser(response.user);
    //     return response.user;
    //   });
    return Promise.resolve()
  }
  const logOut = async () => {
    const fetchResponse = await apiRequest<typeof LogoutResponseSchema>(`api/userflows/logout`, {
      respSchema: LogoutResponseSchema,
      isPost: true,
    })
    if (!fetchResponse.errors) {
      await mutate(null)
    } else {
      console.log("Logout failed", fetchResponse)
    }
  }
  const sendPasswordResetEmail = (/*email*/): Promise<void> => {
    console.error("Not implemented")
    return Promise.resolve()
  }
  const confirmPasswordReset = (/*code, password*/): Promise<void> => {
    console.error("Not implemented")
    return Promise.resolve()
  }
  // // Subscribe to user on mount
  // useEffect(() => {
  //   const unsubscribe = firebase.auth().onAuthStateChanged((user) => {
  //     if (user) {
  //       setUser(user);
  //     } else {
  //       setUser(false);
  //     }
  //   });
  //   // Cleanup subscription on unmount
  //   return () => unsubscribe();
  // }, []);

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
  logIn: (x: LoginRequest) => Promise<LoginResponse>
  logOut: () => Promise<void>
  signUp: (x: LoginRequest) => Promise<void>
  sendPasswordResetEmail: (x: string) => Promise<void>
  confirmPasswordReset: (x: string, y: string) => Promise<void>
}
