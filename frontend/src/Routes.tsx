import {BrowserRouter, Route, Routes} from "react-router-dom";
import {HomePage} from "./pages/HomePage";
import HomeLayout from "./layouts/HomeLayout";
import * as React from "react";
import {ListingsPage} from "./pages/ListingsPage";
import {ListingDetailPage} from "./pages/ListingDetailPage";

export function MyRoutes() {
    return (
        <BrowserRouter>
            <React.StrictMode>

                <Routes>
                    <Route element={<HomeLayout/>}>
                        <Route path="/" >
                            <Route index element={<HomePage/>} />
                            <Route path="listings">
                                <Route index element={<ListingsPage/>}/>
                                <Route path=":listingId" element={<ListingDetailPage/>} />
                            </Route>
                        </Route>
                    </Route>
                    <Route path="*" element={<PageNotFound/>}/>
                </Routes>
            </React.StrictMode>
        </BrowserRouter>
    )
}

function PageNotFound() {
  return (
    <div>
      <h2>Page not found</h2>
    </div>
  );
}
