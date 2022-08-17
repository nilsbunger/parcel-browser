import * as React from "react";

function titleCase(string){
  return string[0].toUpperCase() + string.slice(1).toLowerCase();
}

console.log(titleCase('Download Price History'));
function FinanceTable({ data, children }) {
  return <div>
    {children}
    {Object.keys(data).map((category) => (<>
        {titleCase(category)}
        <table className="table table-compact w-full table-fixed break-normal whitespace-normal">
          {data[category].map((row) => (
            <tr>
              <td className={'w-1/4 whitespace-normal'}>{titleCase(row[0])}</td>
              <td className={'w-1/4'}>${row[1].toLocaleString()}</td>
              <td className={'w-1/2 break-normal whitespace-normal'}>{row[2]}</td>
            </tr>
          ))}
        </table>
      </>
    ))
    }
  </div>

}

function DevFinances({ finances }) {
  return <div>
    <FinanceTable data={finances.capital_flow}>
      <h3>Capital Flows</h3>
    </FinanceTable>
    <b>Total Capital In: ${finances.capital_sum.toLocaleString()}</b>
    <FinanceTable data={{ 'Operations': finances.operating_flow }}>
      <h3 className={'mt-5'}>Operating Flows</h3>
    </FinanceTable>
    <b>Net Operating Income: ${finances.net_income.toLocaleString()}</b>
  </div>
}

export function DevScenarios({ scenarios }) {


  return <div><h1 className="mt-10">ADU Scenarios</h1>
    <div className="flex flex-row w-full justify-between items-top mt-5">
      <div className="divider divider-horizontal"></div>

      {scenarios.map((scenario) => {
        return (<>
            <div className="flex-auto">
              <h3>Scenario: {scenario.adu_qty} {scenario.unit_type.br}BR, {scenario.unit_type.ba}BA ADUs</h3>
              <p>Each {scenario.unit_type.sqft.toLocaleString()} sqft, {scenario.unit_type.stories} stories</p>
              <div className="stats shadow mb-3 mt-2">
                <div className="stat">
                  <div className="stat-title">Size</div>
                  <div className="stat-value">{scenario.unit_type.br}BR,{scenario.unit_type.ba}BA</div>
                  <div className="stat-desc">{scenario.unit_type.sqft} sqft each</div>
                </div>
                <div className="stat">
                  <div className="stat-title"># of ADUs</div>
                  <div className="stat-value">{scenario.adu_qty}</div>
                  <div className="stat-desc">units</div>
                </div>
                <div className="stat">
                  <div className="stat-title">Cap Rate</div>
                  <div className="stat-value">{scenario.finances.cap_rate}%</div>
                  <div className="stat-desc">cap</div>
                </div>
              </div>

              <h3>Total Capital In: ${scenario.finances.capital_sum.toLocaleString()}</h3>
              <h3>NOI: ${scenario.finances.net_income.toLocaleString()}</h3>
              <div className="divider"></div>
              <DevFinances finances={scenario.finances}/>
              {/*<p>{JSON.stringify(scenario.finances)}</p>*/}
            </div>
            <div className="divider divider-horizontal"></div>
          </>
        )
      })
      }
    </div>

  </div>

}
