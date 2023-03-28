import Home3Footer from "../components/layout/Home3Footer"
import Navbar from "../components/layout/Navbar"
import { Outlet } from "react-router-dom"
import React from "react"

const WideLayout = () => {
  return (
    <>
      <div className="flex flex-col h-screen">
        <Navbar />
        <main className="grow">
          <Outlet />
        </main>
        <Home3Footer />
      </div>
    </>
  )
}
export default WideLayout
