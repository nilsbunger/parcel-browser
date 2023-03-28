import * as React from "react"
import Home3Footer from "../components/layout/Home3Footer"
import Navbar from "../components/layout/Navbar"
import { Outlet } from "react-router-dom"

const HomeLayout = () => {
  return (
    <>
      <div className="flex flex-col min-h-screen">
        <Navbar />
        <main className="grow">
          <div className="md:container px-8 lg:px-16 pt-2">
            <Outlet />
          </div>
        </main>
        <Home3Footer />
      </div>
    </>
  )
}
export default HomeLayout
