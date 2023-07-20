import * as React from "react"
import { ReactNode, useCallback, useEffect } from "react"
import { useParams } from "react-router-dom"
import "react-data-grid/lib/styles.css"
import RentRoll from "../components/RentRoll";
import ProfitLossTable from "../components/ProfitLossTable";
import PropertyFilters from "../components/PropertyFilters";
import { Dropzone, MIME_TYPES } from "@mantine/dropzone"
import { Box, Flex, Group, LoadingOverlay, rem, Table, Text, useMantineTheme } from "@mantine/core"
import { IconPhoto, IconTable, IconUpload, IconX } from "@tabler/icons"
import { apiRequest } from "../utils/fetcher";
import { z, ZodType } from "zod";
import { columnarToRowData } from "../utils/utils";
import { KeyedColumns, RentRollRespDataZod, KeyedRow } from "../types";


const MyDropzone = ({ setFilename = null, children }: { setFilename?: any; children: ReactNode }): JSX.Element => {
  const theme = useMantineTheme()
  const [loading, setLoading] = React.useState(false)
  const onDrop = useCallback((files: File[]) => {
    setLoading(true)
    setTimeout(() => {
      setLoading(false)
      setFilename(files[0].name)
    }, 2500)
    console.log("accepted files", files)
  }, [])
  return (
    <Dropzone
      className="my-10"
      onDrop={onDrop}
      onReject={(files) => console.log("rejected files", files)}
      maxSize={50 * 1024 ** 2}
      accept={[MIME_TYPES.pdf, MIME_TYPES.csv, MIME_TYPES.xls, MIME_TYPES.xlsx]}
      loading={loading}
    >
      <Group position="center" spacing="xl" style={{ minHeight: rem(110), pointerEvents: "none" }}>
        <Dropzone.Accept>
          <IconUpload
            size="3.2rem"
            stroke={1.5}
            color={theme.colors[theme.primaryColor][theme.colorScheme === "dark" ? 4 : 6]}
          />
        </Dropzone.Accept>
        <Dropzone.Reject>
          <IconX size="3.2rem" stroke={1.5} color={theme.colors.red[theme.colorScheme === "dark" ? 4 : 6]}/>
        </Dropzone.Reject>
        <Dropzone.Idle>
          <IconPhoto size="3.2rem" stroke={1.5}/>
        </Dropzone.Idle>
        <div>{children}</div>
      </Group>
    </Dropzone>
  )
}

export function useApiRequest<T, U=T>(url: string | null, RespDataZod: ZodType, xformer: (a: T) => U): {data:U | null, isLoading:boolean, error:boolean | Record<string, string>} {
  const [data, setData] = React.useState<U | null>(null)
  const [isLoading, setIsLoading] = React.useState(true)
  const [error, setError] = React.useState<boolean | Record<string, string>>(false)
  useEffect(() => {
    if (!url) return;
    apiRequest<typeof RespDataZod>(url, {
      RespDataCls: RespDataZod,
      isPost: false,
      body: undefined,
    })
      .then(({ errors, data, message }) => {
        // console.log("Column data:")
        // console.log(data)
        const xdata = xformer(data) // eg convert column to row data
        setError(errors)
        setIsLoading(false)
        setData(xdata)
      })
      .catch((err) => {
        console.error(err)
        setError(true)
        setIsLoading(false)
        setData(null)
      })
  }, [url])
  return {data, isLoading, error}
}


export default function BovDetailPage() {
  // setup and state
  const [showRentRoll, setShowRentRoll] = React.useState(false)
  const [financialsLoading, setFinancialsLoading] = React.useState(false)
  const { id } = useParams<{ id: string }>()
  // const [showFinancials, setShowFinancials] = React.useState(false)
  const [rrFilename, setRrFilename] = React.useState<string | null>(null)
  const [t12Filename, setT12Filename] = React.useState<string | null>(null)
  const [showFinancials, setShowFinancials] = React.useState(false)
  // get property profiles

  type RespDataType = z.infer<typeof RentRollRespDataZod>
  const foo = columnarToRowData<string | number>
  console.log(foo)
  const { data, isLoading, error } = useApiRequest<RespDataType, Array<Record<string,string | number>>>(
    showRentRoll ? `/api/properties/bov/${id}`: null, RentRollRespDataZod, columnarToRowData<string | number>)

  useEffect(() => {
    if (rrFilename && t12Filename) {
      setFinancialsLoading(true)
      setTimeout(() => {
        setShowFinancials(true)
        setFinancialsLoading(false)
      }, 2500)
    }
  }, [rrFilename, t12Filename])
  useEffect(() => {
    document.title = `BOV ${id}`
  }, [id])

  const rentRollDisplay = !id
    ? <div>Invalid BOV id</div>
    : !showRentRoll ? <button onClick={() => setShowRentRoll(true)}>Load Rent Roll</button>
      : error ? <div>Error loading rent roll!</div>
      : isLoading ? <div>Loading rent roll...</div>
      : <RentRoll rows={data}></RentRoll>

  return (<div>
      <h2 className="py-5">Filters</h2>
      <PropertyFilters/>
      <h2 className="py-5">Profit & Loss</h2>
      <div className="py-5">
        <ProfitLossTable/>
      </div>
      <h2 className="py-5">Rent Roll</h2>
      {rentRollDisplay}
      <div className="py-5">
        <h1>BOV </h1>
        <h2 className="mt-10 mb-5">Financials</h2>
        {/* Table of uploaded files */}
        <Table maw={700}>
          <thead>
          <tr>
            <th>Filename</th>
            <th>Kind</th>
            <th>Current thru</th>
            <th>Upload date</th>
          </tr>
          </thead>
          <tbody>
          {rrFilename && (
            <tr onClick={() => console.log("Click on rent roll entry")}>
              <td>
                <IconTable color="#1D6F42" className="inline mr-2"/> {rrFilename}
              </td>
              <td>Rent roll</td>
              <td>3/31/2023</td>
              <td>5/9/2023</td>
            </tr>
          )}
          {t12Filename && (
            <tr>
              <td>
                <IconTable color="#1D6F42" className="inline mr-2"/> {t12Filename}
              </td>
              <td>T12 Financials</td>
              <td>3/31/2023</td>
              <td>5/9/2023</td>
            </tr>
          )}
          </tbody>
        </Table>
        <Flex
          // bg="rgba(0, 0, 0, .3)"
          gap="md"
          justify="center"
          align="flex-start"
          direction="row"
          wrap="wrap"
        >
          {!rrFilename && (
            <MyDropzone setFilename={setRrFilename}>
              <Text size="xl" inline>
                Upload your Rent Roll
              </Text>
              <Text size="sm" color="dimmed" mt={7} inline>
                Drag or click to upload a Excel, CSV, or PDF file
              </Text>
            </MyDropzone>
          )}
          {!t12Filename && (
            <MyDropzone setFilename={setT12Filename}>
              <Text size="xl">Upload your T12 Financials</Text>
              <Text size="sm" color="dimmed" mt={7}>
                Drag or click to upload an Excel, CSV, or PDF file
              </Text>
            </MyDropzone>
          )}
        </Flex>

        <h2 className="my-10">2. Review extracted data</h2>

        {(!showFinancials || financialsLoading) && (
          <Box pos="relative">
            <LoadingOverlay visible={financialsLoading}/>
            <div className="w-full h-50 my-10 bg-gray-200 ">
              <div className="flex flex-col items-center justify-center h-full text-gray-400 border-4 border-dashed">
                {/*<button onClick={() => setShowFinancials(true)}>Show Financials</button>*/}
                <p className="my-5">Waiting for rent roll and T-12...</p>
              </div>
            </div>
          </Box>
        )}
        {showFinancials && !financialsLoading && <h3>Todo... show financials here </h3>}
        <h2 className="my-10">3. Review your BOV</h2>
        <h2 className="my-10">4. Send to client</h2>
      </div>
    </div>
  )
}
