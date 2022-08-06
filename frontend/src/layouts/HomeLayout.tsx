import Home3Footer from "../components/layout/Home3Footer";
import Navbar from "../components/layout/Navbar";
import {Outlet} from "react-router-dom";

const HomeLayout = () => {
    return (
        <>
            <div className="min-h-screen">
                <Navbar/>
                <main>
                    <div className="md:container px-8 lg:px-16 pt-2">
                        <Outlet/>
                    </div>
                </main>
            </div>
            <Home3Footer/>
        </>
    )
}
export default HomeLayout
