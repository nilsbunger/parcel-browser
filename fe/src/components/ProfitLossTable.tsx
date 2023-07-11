function PLHeader({ title, cols }: { title: string, cols: string[] }) {
  // table header row
  return (
    <thead>
    <tr>
      <td>&#160;</td>
      {cols.map((col, index) => <th key={index}>{col}</th>)}
    </tr>
    </thead>)
}

function PLLeafRow({ title, cols, isSubtotal = false }: { title?: string, cols?: string[], isSubtotal?: boolean }) {
  // table content row
  const headerCol = isSubtotal ? <td>&nbsp; &nbsp; {title}</td> : <td>{title}</td>
  return (<tr className={isSubtotal ? "font-bold" : "font-normal"}>
    {!cols && <td colSpan={10}>&#160;</td>}
    {cols && headerCol}
    {cols?.map((col, index) =>
      (isSubtotal ? <td className="border-t border-gray-800" key={index}>{col}</td>
          : <td style={{ borderTop: "3px" }} key={index}>{col}</td>
      ))}
  </tr>)
}


function PLSection({ title, children }: { title: string, children?: React.ReactNode }) {
  // table section
  return (
    <tbody role="rowgroup">
    <tr>
      <th colSpan={10} scope="rowgroup" className="text-left bg-gray-200">{title}</th>
    </tr>
    {children}
    </tbody>)
}


export default function ProfitLossTable() {

  return (<table className="table-auto text-right border-separate border-spacing-x-5">
    <PLHeader title="Income" cols={["T12 Annualized", "Pro Forma Yr 1"]}/>
    <PLSection title="OPERATING REVENUE">
      <PLLeafRow title="Potential Market Rent" cols={["$724,863", "$733,307"]}/>
      <PLLeafRow title="(Loss to Lease) / Gain to Lease" cols={["0", "0"]}/>
      <PLLeafRow title="Gross Potential Revenue" cols={["0", "0"]} isSubtotal/>
      <PLLeafRow/>
      <PLLeafRow title="Vacancy" cols={["$0", "$0"]}/>
      <PLLeafRow title="Concessions" cols={["($23,782)", "($19,800)"]}/>
      <PLLeafRow title="Base Rental Revenue" cols={["0", "0"]} isSubtotal/>
      <PLLeafRow/>
      <PLLeafRow title="Expense Reimbursements" cols={["$0", "$0"]}/>
      <PLLeafRow title="Other Residential Income" cols={["($23,782)", "($19,800)"]}/>
      <PLLeafRow title="Commercial Net Income" cols={["($23,782)", "($19,800)"]}/>
      <PLLeafRow title="Other Income" cols={["0", "0"]} isSubtotal/>
      <PLLeafRow/>
      <PLLeafRow title="EFFECTIVE GROSS REVENUE" cols={["0", "0"]} isSubtotal/>
      <PLLeafRow/>
    </PLSection>
    <PLSection title="OPERATING EXPENSES">
      <PLLeafRow title="Repair & Maintenance" cols={["$724,863", "$733,307"]}/>
      <PLLeafRow title="Contract Services" cols={["0", "0"]}/>
      <PLLeafRow title="Personnel" cols={["0", "0"]}/>
      <PLLeafRow/>
      <PLLeafRow title="TOTAL OPERATING EXPENSES" cols={["$0", "$0"]} isSubtotal/>
    </PLSection>
  </table>)
  //     <tr>
  //       <th>dffddf</th>
  //       <td>✓</td>
  //       <td>✓</td>
  //     </tr>
  //     <tr>
  //       <th>fdfdfdf</th>
  //       <td>✓</td>
  //       <td>✓</td>
  //     </tr>
  //     <tr>
  //       <th>dffddf</th>
  //       <td>&#160;</td>
  //       <td>&#160;</td>
  //     </tr>
  //   </PLSection>
  //   <tbody role="rowgroup">
  //   <tr>
  //     <th colSpan={10} scope="rowgroup" style={{ backgroundColor: "#e0e0e0", textAlign: "left" }}>Header2</th>
  //   </tr>
  //   <tr>
  //     <th>5455445</th>
  //     <td>✓</td>
  //     <td>✓</td>
  //   </tr>
  //   <tr>
  //     <th>fdfggfgf</th>
  //     <td>✓</td>
  //     <td>✓</td>
  //   </tr>
  //   </tbody>
  //   <tbody role="rowgroup">
  //   <tr>
  //     <th colSpan={10} scope="rowgroup" style={{ backgroundColor: "#e0e0e0", textAlign: "left" }}>Header3</th>
  //   </tr>
  //   <tr>
  //     <th>fgggf</th>
  //     <td>✓</td>
  //     <td>✓</td>
  //   </tr>
  //   <tr>
  //     <th>fgggfgf</th>
  //     <td>✓</td>
  //     <td>✓</td>
  //   </tr>
  //   </tbody>
  // </table>)
}
