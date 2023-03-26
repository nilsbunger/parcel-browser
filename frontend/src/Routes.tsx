import { BrowserRouter, Navigate, Outlet, Route, Routes, useNavigate } from "react-router-dom"
import HomeLayout from "./layouts/HomeLayout"
import * as React from "react"
import { lazy, Suspense, useEffect } from "react"
import WideLayout from "./layouts/WideLayout"
import { UserFlowLayout } from "./layouts/UserFlowLayout"
import { useAuth } from "./hooks/Auth"
import { Loader } from "@mantine/core"
import BackyardPage from "./pages/deals/BackyardPage";
import dataProvider from "@refinedev/simple-rest";
import routerBindings from "@refinedev/react-router-v6";
import { Refine } from "@refinedev/core";

const ListingsPage = lazy(() => import("./pages/ListingsPage"))
const ListingDetailPage = lazy(() => import("./pages/ListingDetailPage"))
const NewListingPage = lazy(() => import("./pages/NewListingPage"))
const RentalRatesPage = lazy(() => import("./pages/RentalRatesPage"))
const CoMapPage = lazy(() => import("./pages/CoMapPage"))
const LoginPage = lazy(() => import("./pages/auth/LoginPage"))

export function MyRoutes() {
  return (
    <BrowserRouter>
      <React.StrictMode>
        <Refine
          dataProvider={dataProvider("http://localhost:8000/api")}
          // notificationProvider={notificationProvider} // seems to overlap with our notif provider
          routerProvider={routerBindings}
          // authProvider={authProvider}  // overlaps with our auth provider, maybe we can add this later?
          resources={[
            {
              name: "blog_posts",
              list: "/blog-posts",
              create: "/blog-posts/create",
              edit: "/blog-posts/edit/:id",
              show: "/blog-posts/show/:id",
              meta: {
                canDelete: true,
              },
            },]}>
          <Suspense fallback={<LoadingScreen/>}>
            <Routes>
              {/* Pages that don't require login */}
              <Route path="login" element={<UserFlowLayout/>}>
                <Route index element={<LoginPage/>}/>
              </Route>

              <Route path="deals" element={<HomeLayout/>}>
                <Route path="backyard" element={<BackyardPage/>}/>
              </Route>

              {/* Rest of pages require login... */}
              <Route element={<ProtectedRoute/>}>
                <Route element={<WideLayout/>}>
                  <Route path="listings">
                    <Route index element={<ListingsPage/>}/>
                  </Route>
                </Route>
                <Route path="logout" element={<LogoutHelper/>}/>

                <Route element={<HomeLayout/>}>
                  {/*<Route path="login" element={<LoginPage/>}/>*/}
                  <Route index element={<Navigate replace to="/listings"/>}/>
                  {/*<Route index element={<HomePage/>}/>*/}
                  <Route path="analysis">
                    <Route path=":analysisId" element={<ListingDetailPage/>}/>
                  </Route>
                  <Route path="search" element={<NewListingPage/>}/>
                  <Route path="rental-rates" element={<RentalRatesPage/>}/>
                  <Route path="map" element={<CoMapPage/>}/>
                </Route>
                {/* Catch-all element below */}
                <Route path="*" element={<PageNotFound/>}/>
              </Route>
            </Routes>
          </Suspense>
        </Refine>
      </React.StrictMode>
    </BrowserRouter>
  )
}

const ProtectedRoute = () => {
  const { user, isLoading } = useAuth()

  // if (isLoading) {
  //   console.log ("Protecte route check - loading, user=", user)
  //   return (
  //     <div className="min-h-screen w-full coolbg flex flex-col justify-center items-center">
  //       <Loader variant={"dots"}/>
  //       {/*<h1>Loading...</h1>*/}
  //     </div>
  //   )
  // }
  if (!user && !isLoading) {
    console.log("Protected route, didn't find user, redirecting to login")
    return <Navigate to="/login" replace/>
  }
  return <Outlet/>
}

const LoadingScreen = () => {
  return (
    <div className="min-h-screen w-full coolbg flex flex-col justify-center items-center">
      <Loader variant={"dots"}/>
      {/*<h1>Loading...</h1>*/}
    </div>
  )
}

function LogoutHelper() {
  const { logOut } = useAuth()
  const navigate = useNavigate()
  useEffect(() => {
    logOut().then(() => {
      navigate("/login")
    }).catch((err) => {
      console.log("Error logging out: ", err)
    })
  }, [])

  return <> </>
}

function PageNotFound() {
  return (
    <div>
      <h2>Page not found</h2>
      <p>Frontend router didn't find our page 😭</p>
    </div>
  )
}
