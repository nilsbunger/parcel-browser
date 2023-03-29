import React from "react"
import TurbopropLogoIcon from "jsx:./TurbopropLogoIcon.svg"

export default function TurbopropLogo() {
  return (
    <>
      <div className="flex items-center">
        <TurbopropLogoIcon style={{ height: "32px" }} />
        <p className="font-heading text-3xl font-bold text-slate-800 ml-2">Turboprop</p>
      </div>
    </>
  )
}
