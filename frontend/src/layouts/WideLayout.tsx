import Home3Footer from "../components/layout/Home3Footer";
import Navbar from "../components/layout/Navbar";
import {Outlet} from "react-router-dom";
import React = require("react");

const WideLayout = () => {
  return (
    <>
      <div className="flex flex-col h-screen justify-between">
        <div className='flex-none'>
          <Navbar/>
        </div>
        <div className={'grow'}>
          <main>
            <div className="pt-2 mx-1">
              <Outlet/>
            </div>
          </main>
        </div>
        <div className='flex-none'>
          <Home3Footer/>
        </div>
      </div>
    </>
  )
}
export default WideLayout
