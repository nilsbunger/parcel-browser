import useSWR from "swr";
import { ParcelGetResp } from "../types";
import { fetcher } from "../utils/fetcher";
import { stringify } from "../utils/utils";
import { Drawer, ScrollArea } from "@mantine/core";
import { ErrorBoundary } from "react-error-boundary";
import * as React from "react";


export function CoMapDrawer ({ selection, setSelection }) {
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
        <ScrollArea grow="true" className="h-[90%]">
          <CoMapDrawerContents selection={selection}/>
        </ScrollArea>
      </ErrorBoundary>
    </Drawer>

  )
}


const ParcelDetails = ({ apn }) => {
  const { data, error } = useSWR<ParcelGetResp, string>(
    `/api/parcel/${apn}`,
    fetcher
  );
  if (error) return <div>failed to load parcel APN={apn}</div>
  if (!data) return <div>loading parcel APN={apn}</div>
  console.log("PARCEL DETAILS", data)
  return (
    <div>
      <h3>Parcel {apn}</h3>
      <div><p className="font-bold">Address</p>
        {data.situs_addr || 0}{data.situs_pre_field || ""} {data.situs_stre || ""} {data?.situs_post || ""} {data?.situs_suff || ""}
        <br/>{data.situs_juri} {data.situs_zip}
      </div>
      <div><p className="font-bold">Owner</p>
        {data.own_name1} {data.own_name2} {data.own_name3}
        <br/>{data.own_addr1}
        <br/>{data.own_addr2} {data.own_addr3} {data.own_addr4}
        <br/>{data.own_zip}
      </div>
      <div><p className="font-bold">Stats</p>
        Lot size: {data.usable_sq_field} sqft
        <br/>Interior size: {data.total_lvg_field} sqft
        <br/># of units: {data.unitqty}
        <br/>Bedrooms: {data.bedrooms}
        <br/>Baths: {data.baths}
      </div>
    </div>
  )

}

const CoMapDrawerContents = ({ selection }) => {
  if (!selection) return <></>

  if (selection.selType == "tpa-tile-layer") {
    return (
      <p>TPA</p>
    )
  }
  if (selection.selType == 'zoning-tile-layer') {
    return (
      <div>
        <p>Zone</p>
        <p>{selection.info.object.properties.zone_name}</p>
        <p>{selection.info.object.properties.zone_desc}
        </p>
      </div>
    )
  }
  if (selection.selType == 'parcel-tile-layer') {
    return (
      <div>
        <ParcelDetails apn={selection.info.object.properties.apn}/>
        {/*<p>{selection.info.object.properties.apn}</p>*/}
      </div>
    )
  }
  if (selection.selType == 'road-tile-layer') {
    const p = selection.info.object.properties;
    return (
      <div>
        <p>Road</p>
        <p>{p.abloaddr} - {p.abhiaddr} {p.rd30full}</p>
        <p>Width: {p.rightway} ft</p>
      </div>
    )
  }
  return <>
    <p>{selection.selType}</p>
    <span className={"text-xs"}>
    <pre>{stringify(selection, 5, null, 2)}</pre>
    </span>
  </>

}
