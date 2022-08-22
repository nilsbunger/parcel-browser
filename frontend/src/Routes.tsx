import { BrowserRouter, Route, Routes } from 'react-router-dom';
import { HomePage } from './pages/HomePage';
import HomeLayout from './layouts/HomeLayout';
import * as React from 'react';
import { ListingsPage } from './pages/ListingsPage';
import { ListingDetailPage } from './pages/ListingDetailPage';
import { NewListingPage } from './pages/NewListingPage';
import WideLayout from "./layouts/WideLayout";
import { RentalRatesPage } from "./pages/RentalRatesPage";

export function MyRoutes() {
  return (
    <BrowserRouter>
      <React.StrictMode>
        <Routes>
          <Route element={<WideLayout/>}>
            <Route path="listings">
              <Route index element={<ListingsPage/>}/>
            </Route>
          </Route>
          <Route path="/" element={<HomeLayout/>}>
            <Route index element={<HomePage/>}/>
            <Route path="analysis">
              <Route path=":analysisId" element={<ListingDetailPage/>}/>
            </Route>
            <Route path="new-listing" element={<NewListingPage/>}/>
            <Route path="rental-rates" element={<RentalRatesPage/>}/>
          </Route>
          {/* Catch-all element below */}
          <Route path="*" element={<PageNotFound/>}/>
        </Routes>
      </React.StrictMode>
    </BrowserRouter>
  );
}

function PageNotFound() {
  return (
    <div>
      <h2>Page not found</h2>
      <p>Frontend router didn't find our page 😭</p>
    </div>
  );
}
