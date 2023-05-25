import * as React from "react"
import Home3Footer from "../components/layout/Home3Footer"
import Navbar from "../components/layout/Navbar"
import { Outlet } from "react-router-dom"

const HomeLayout = () => {
  return (
    <>
      <Navbar />
      <main className="grow bg-white">
        <div className="md:container px-8 lg:px-16 pt-2">
          <Outlet />
        </div>
      </main>
    </>
  )
}
export default HomeLayout
