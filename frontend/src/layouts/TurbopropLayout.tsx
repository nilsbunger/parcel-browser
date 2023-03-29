import TurbopropFooter from "../components/layout/TurbopropFooter"
import { Outlet } from "react-router-dom"
import TurbopropLogo from "../components/layout/TurbopropLogo"
import * as React from "react"

export const TurbopropLayout = () => {
  return (
    <>
      <div className="min-h-screen w-full coolbg">
        <div className="flex min-h-screen flex-col justify-between">
          <div>
            <div className="h-1 w-full bg-pinkpop"></div>
            <div className="md:container px-8 lg:px-16 pt-2">
              <TurbopropLogo />
            </div>
          </div>

          <div className="md:container px-8 lg:px-16 pt-2">
            <main>
              <Outlet />
            </main>
          </div>

          <TurbopropFooter />
        </div>
      </div>
    </>
  )
}
