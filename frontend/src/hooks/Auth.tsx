import * as React from 'react';
import { createContext, useContext } from 'react';
import { api_post, fetcher } from "../utils/fetcher";
import useSWR from "swr";
import { LoginResponse, LoginResponseSchema, LogoutResponse, LogoutResponseSchema } from "../types";

// useAuth hook:
export const useAuth = () => {
  return useContext(authContext);
}

// Auth context provider:
export function AuthProvider({ children }) {
  const auth = useAuthProvider();
  return <authContext.Provider value={auth}>{children}</authContext.Provider>;
}

const authContext = createContext(undefined);

// Provider hook that creates auth object and handles state
function useAuthProvider() {
  // const [user, setUser] = useState(null);
  // const navigate = useNavigate();

  const { data: user, error, isValidating, mutate } = useSWR(
    '/api/userflows/user', fetcher, { shouldRetryOnError: false }
  )
  const isLoading = isValidating
  console.log ("IsLoading=", isLoading)

  if (error) {
    console.log("useAuthProvider error on call to userflows/user", error)
    // navigate("/login")
  }
  // console.log("Got user", user)
  const logIn = async (loginParameters) => {
    const {data, error, message} = await api_post<LoginResponse>(`/api/userflows/login`, {
      RespSchema: LoginResponseSchema,
      body: loginParameters
    })
    if (!error) {
      await mutate(data.user);
    } else {
      await mutate(null);
    }
    return {data, error, message}
  };
  const signUp = (email, password) => {
    console.error("Not implemented");
    // return firebase
    //   .auth()
    //   .createUserWithEmailAndPassword(email, password)
    //   .then((response) => {
    //     setUser(response.user);
    //     return response.user;
    //   });
  };
  const logOut = async () => {

    const fetchResponse = await api_post<LogoutResponse>(`/api/userflows/logout`, {
      RespSchema: LogoutResponseSchema,
    },)
    if (!fetchResponse.error) {
      await mutate(null);
    } else {
      console.log("Logout failed", fetchResponse)
    }
  };
  const sendPasswordResetEmail = (email) => {
    console.error("Not implemented");
  };
  const confirmPasswordReset = (code, password) => {
    console.error("Not implemented");
  };
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
    logIn,
    logOut,
    signUp,
    isLoading,
    sendPasswordResetEmail,
    confirmPasswordReset,
  };
}