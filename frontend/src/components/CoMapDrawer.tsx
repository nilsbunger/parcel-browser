import useSWR from "swr"
import { EligibilityCheck, ParcelGetResp, RoadGetResp } from "../types"
import { fetcher } from "../utils/fetcher"
import { stringify } from "../utils/utils"
import { Drawer, ScrollArea, Tooltip } from "@mantine/core"
import { ErrorBoundary } from "react-error-boundary"
import * as React from "react"
import {
  BadgeCheckIcon,
  DotsVerticalIcon,
  ExclamationIcon,
  InformationCircleIcon,
  QuestionMarkCircleIcon,
  XCircleIcon,
} from "@heroicons/react/solid"
import { MinusCircleIcon } from "@heroicons/react/outline"
import { BACKEND_DOMAIN } from "../constants"

export function CoMapDrawer({ selection, setSelection }) {
  const opened = selection !== null
  return (
    <Drawer
      opened={opened}
      onClose={() => setSelection(null)}
      title="Details"
      padding="lg"
      size="350px"
      closeOnClickOutside={false}
      trapFocus={false}
      withOverlay={false}
    >
      <ErrorBoundary fallback={<div>Failed to load details. Close the drawer and try again</div>}>
        <ScrollArea className="h-[90%]">
          <CoMapDrawerContents selection={selection} />
        </ScrollArea>
      </ErrorBoundary>
    </Drawer>
  )
}

const renderEligibilityTitleRow = (eligibility: EligibilityCheck) => {
  let passFail
  switch (eligibility.result) {
    case "passed":
      passFail = (
        <Tooltip label={"Passed"}>
          <BadgeCheckIcon className="inline-block align-middle h-6 w-6 text-success" />
        </Tooltip>
      )
      break
    case "failed":
      passFail = (
        <Tooltip label={"Failed"}>
          <XCircleIcon className="inline-block align-middle h-6 w-6 text-error" />
        </Tooltip>
      )
      break
    case "not_run":
      passFail = (
        <Tooltip label={"Not run"}>
          <MinusCircleIcon className="inline-block align-middle h-6 w-6 text-slate-200" />
        </Tooltip>
      )
      break
    case "uncertain":
      passFail = (
        <Tooltip label={"Uncertain"}>
          <QuestionMarkCircleIcon className="inline-block align-middle h-6 w-6 text-warning" />
        </Tooltip>
      )
      break
    case "error":
      passFail = (
        <Tooltip label={"Error"}>
          <ExclamationIcon className="inline-block align-middle h-6 w-6 text-error" />
        </Tooltip>
      )
      break

    default:
      passFail = <span>{eligibility.result[0].toUpperCase() + eligibility.result.substring(1)}</span>
      break
  }

  const rowname = eligibility.name == "And" ? "All of these checks must pass:" : eligibility.name
  return (
    <>
      {passFail}
      <Tooltip
        multiline
        width={220}
        withArrow
        transition="fade"
        transitionDuration={200}
        label={eligibility.description}
      >
        <span className={"leading-6"}>
          {` ${rowname} `}
          <InformationCircleIcon className="inline align-text-bottom h-4 w-4 text-info" />
        </span>
      </Tooltip>
    </>
  )
}

const EligibilityCheck = ({ eligibility, level }: { eligibility: EligibilityCheck; level: number }) => {
  return (
    <>
      {renderEligibilityTitleRow(eligibility)}

      {eligibility?.notes?.map((note, idx) => (
        <p key={idx}>
          <DotsVerticalIcon className="inline-block align-middle h-6 w-6 text-slate-200" />
          {" " + note}
        </p>
      ))}
      {eligibility?.children?.map((child, idx) => (
        <div className="ml-5" key={idx}>
          <EligibilityCheck eligibility={child} level={level + 1} />
        </div>
      ))}
    </>
  )
}

const ParcelDetails = ({ apn }) => {
  const { data, error } = useSWR<ParcelGetResp, string>(
    `${BACKEND_DOMAIN}/api/world/parcel/${apn}`,
    fetcher
  )
  if (error) return <div>failed to load parcel APN={apn}</div>
  if (!data) return <div>loading parcel APN={apn}</div>
  console.log("PARCEL DETAILS", data)
  return (
    <div>
      <h3>Parcel {apn}</h3>
      <div>
        <p className="mt-5 font-bold">Address</p>
        {data.situs_addr || 0}
        {data.situs_pre_field || ""} {data.situs_stre || ""} {data?.situs_post || ""}{" "}
        {data?.situs_suff || ""}
        <br />
        {data.situs_juri} {data.situs_zip}
      </div>
      <div>
        <p className="mt-5 font-bold">Owner</p>
        {data.own_name1} {data.own_name2} {data.own_name3}
        <br />
        {data.own_addr1}
        <br />
        {data.own_addr2} {data.own_addr3} {data.own_addr4}
        <br />
        {data.own_zip}
      </div>
      <div>
        <p className="mt-5 font-bold">Stats</p>
        Lot size: {data.usable_sq_field} sqft
        <br />
        Interior size: {data.total_lvg_field} sqft
        <br /># of units: {data.unitqty}
        <br />
        Bedrooms: {data.bedrooms}
        <br />
        Baths: {data.baths}
      </div>
      <div>
        <p className="mt-5 font-bold">AB 2011 Eligibility</p>
      </div>
      <div>
        <EligibilityCheck eligibility={data.ab2011_result} level={0} />
      </div>
    </div>
  )
}

const RoadDetails = ({ properties }) => {
  const { data, error } = useSWR<RoadGetResp, string>(
    `${BACKEND_DOMAIN}/api/world/road/${properties.roadsegid}`,
    fetcher
  )
  if (error) return <div>failed to load road segid={properties.roadsegid}</div>
  if (!data) return <div>loading road segid={properties.roadsegid}</div>
  console.log("ROAD:", properties)
  return (
    <div>
      <p>Road</p>
      <p>
        {" "}
        {properties.abloaddr && (
          <span>
            {properties.abloaddr} - {properties.abhiaddr}
          </span>
        )}
        {properties.rd30full}
      </p>
      <p>Width: {properties.rightway} ft</p>
      {properties.roadsegid && <p>Segment ID: {properties.roadsegid}</p>}
      <p>Functional class: {data.funclass_decoded}</p>
      <p>Segment class: {data.segclass_decoded}</p>
      <span className={"text-xs"}>
        <pre>{stringify(data, 5, null, 2)}</pre>
      </span>
    </div>
  )
}

const CoMapDrawerContents = ({ selection }) => {
  if (!selection) return <></>

  if (selection.selType == "tpa-tile-layer") return <p>Transit Priority Area Overlay</p>
  if (selection.selType == "ab2011-tile-layer") return <p>AB 2011 Eligibility Overlay</p>
  if (selection.selType == "zoning-tile-layer") {
    return (
      <div>
        <p>Zone</p>
        <p>{selection.info.object.properties.zone_name}</p>
        <p>{selection.info.object.properties.zone_desc}</p>
      </div>
    )
  }
  if (selection.selType == "r2-parcel-road-tile-layer")
    return selection.info.object.properties.apn ? (
      <ParcelDetails apn={selection.info.object.properties.apn} />
    ) : (
      <RoadDetails properties={selection.info.object.properties} />
    )
  if (selection.selType == "parcel-tile-layer")
    // this branch is unused now, since we combined parcel and zoning and serve them staticly
    return <ParcelDetails apn={selection.info.object.properties.apn} />
  if (selection.selType == "road-tile-layer")
    // this branch is unused now, since we combined parcel and zoning and serve them staticly
    return <RoadDetails properties={selection.info.object.properties} />
  if (selection.selType == "compcomm-tile-layer") {
    const p = selection.info.object.properties
    return (
      <div>
        <p>Complete Community Overlay</p>
        <p>{p.tier}</p>
        <p>{p.allowance}</p>
      </div>
    )
  }
  return (
    <>
      <p>{selection.selType}</p>
      <span className={"text-xs"}>
        <pre>{stringify(selection, 5, null, 2)}</pre>
      </span>
    </>
  )
}
