import * as React from "react"
import { FaLinkedin, FaTwitter } from "react-icons/fa"
import TurbopropLogo from "./TurbopropLogo"

export default function TurbopropFooter() {
  return (
    <footer className="py-3 md:py-6 bg-gray-200 w-full flex-none">
      <div className="md:container py-2 px-8 lg:px-16">
        <div className="flex flex-col gap-4">
          {/*center logo and LI/etc icons vertically and spread horizontally*/}
          <div className="flex flex-row flex-grow items-center justify-between">
            <TurbopropLogo />
            <div className="flex flex-row">
              <a href="frontend/src/components/layout/TurbopropFooter#" aria-label="LinkedIn">
                {" "}
                <FaLinkedin fontSize="1.25rem" />{" "}
              </a>
              {"_"}
              {/*<a href="#" aria-label="Github"> <FaGibHub fontSize="1.25rem" /> </a>*/}
              <a href="#" aria-label="Twitter">
                {" "}
                <FaTwitter fontSize="1.25rem" />{" "}
              </a>
            </div>
          </div>
          <p className="text-sm text-gray-600">
            &copy; {new Date().getFullYear()} Home3, Inc. All rights reserved.
          </p>
        </div>
      </div>
    </footer>
  )
}
