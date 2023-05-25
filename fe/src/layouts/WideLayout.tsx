import Home3Footer from "../components/layout/Home3Footer"
import Navbar from "../components/layout/Navbar"
import { Outlet } from "react-router-dom"
import React from "react"

const WideLayout = () => {
  return (
    <>
      <div className="flex flex-col">
        <Navbar />
        <main className="grow bg-white">
          <Outlet />
        </main>
      </div>
    </>
  )
}
export default WideLayout
