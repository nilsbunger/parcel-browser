import * as React from "react"
import { useEffect } from "react"
import { useParams } from "react-router-dom"
import "react-data-grid/lib/styles.css"
import RentRoll from "../components/RentRoll";

export default function BovDetailPage() {
  // setup and state
  const { id } = useParams<{ id: string }>()
  const [showRentRoll, setShowRentRoll] = React.useState(false)
  useEffect(() => { document.title = `BOV ${id}` }, [id])

  const rentRollDisplay = !id
    ? <div>Invalid BOV id</div>
    : !showRentRoll ? <button onClick={() => setShowRentRoll(true)}>Load Rent Roll</button>
    : <RentRoll id={parseInt(id)}></RentRoll>

  return (<div>
      <h2>Rent Roll</h2>
      {rentRollDisplay}
    </div>

  )
}
