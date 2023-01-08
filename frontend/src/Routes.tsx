import { BrowserRouter, Navigate, Outlet, Route, Routes, useNavigate } from 'react-router-dom';
import HomeLayout from './layouts/HomeLayout';
import * as React from 'react';
import { useEffect } from 'react';
import { ListingsPage } from './pages/ListingsPage';
import { ListingDetailPage } from './pages/ListingDetailPage';
import { NewListingPage } from './pages/NewListingPage';
import WideLayout from "./layouts/WideLayout";
import { RentalRatesPage } from "./pages/RentalRatesPage";
import { CoMapPage } from "./pages/CoMapPage";
import { LoginPage } from "./pages/auth/LoginPage";
import { UserFlowLayout } from "./layouts/UserFlowLayout";
import { useAuth } from "./hooks/Auth";

export function MyRoutes() {
  return (
    <BrowserRouter>
      <React.StrictMode>
        <Routes>
          {/* Pages that don't require login */}
          <Route path="login" element={<UserFlowLayout/>}>
            <Route index element={<LoginPage/>}/>
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
              <Route index element={<Navigate replace to='/listings'/>}/>
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
      </React.StrictMode>
    </BrowserRouter>
  );
}

const ProtectedRoute = () => {
  const { user } = useAuth();
  if (!user) {
    return <Navigate to="/login" replace/>;
  }
  return <Outlet/>;
};

function LogoutHelper() {
  const { logOut } = useAuth();
  const navigate = useNavigate();
  useEffect(() => {
    logOut();
    navigate("/login")
  }, [])
  return <> </>
}

function PageNotFound() {
  return (
    <div>
      <h2>Page not found</h2>
      <p>Frontend router didn't find our page 😭</p>
    </div>
  );
}
