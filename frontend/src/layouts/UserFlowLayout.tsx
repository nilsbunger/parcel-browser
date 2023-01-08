import Home3Footer from "../components/layout/Home3Footer";
import { Outlet } from "react-router-dom";
import Home3Logo from "../components/layout/Home3Logo";
import * as React from "react";

export const UserFlowLayout = () => {
  return (
    <>
      <div className="min-h-screen w-full coolbg">
        <div className="flex min-h-screen flex-col justify-between">
          <div>
            <div className="h-1 w-full bg-pinkpop"></div>
            <div className="md:container px-8 lg:px-16 pt-2">
              <Home3Logo/>
            </div>
          </div>

          <div className="md:container px-8 lg:px-16 pt-2">
            <main>
              <Outlet/>
            </main>
          </div>

          <Home3Footer/>

        </div>
      </div>
    </>
  )
}
