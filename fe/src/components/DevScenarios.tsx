import * as React from "react"
import { DevScenario, DevScenarioFinance, FinanceLineItem } from "../types"

function titleCase(string: string) {
  return string[0].toUpperCase() + string.slice(1).toLowerCase()
}

function FinanceTable({
  data,
  children,
}: {
  data: { [key: string]: FinanceLineItem[] }
  children: React.ReactNode
}) {
  return (
    <div>
      {children}
      {Object.keys(data).map((category) => (
        <>
          {titleCase(category)}
          <table className="table table-compact w-full table-fixed break-normal whitespace-normal">
            {data[category].map((row) => (
              <tr>
                <td className={"w-1/4 whitespace-normal"}>{titleCase(row[0])}</td>
                <td className={"w-1/4"}>${row[1].toLocaleString()}</td>
                <td className={"w-1/2 break-normal whitespace-normal"}>{row[2]}</td>
              </tr>
            ))}
          </table>
        </>
      ))}
    </div>
  )
}

function DevFinances({ finances }: { finances: DevScenarioFinance }) {
  return (
    <div>
      <FinanceTable data={finances.capital_flow}>
        <h3>Capital Flows</h3>
      </FinanceTable>
      <b>Total Capital In: ${finances.capital_sum.toLocaleString()}</b>
      <FinanceTable data={{ Operations: finances.operating_flow }}>
        <h3 className={"mt-5"}>Operating Flows</h3>
      </FinanceTable>
      <b>Net Operating Income: ${finances.net_income.toLocaleString()}</b>
    </div>
  )
}

export function DevScenarios({ scenarios }: { scenarios: DevScenario[] }) {
  return (
    <div>
      <h1 className="mt-10">ADU Scenarios</h1>
      {!scenarios && (
        <div className="alert alert-info shadow-lg mt-3">
          <div>
            <svg
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              className="stroke-current flex-shrink-0 w-6 h-6"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              ></path>
            </svg>
            <span className={"text-slate-50"}>We haven't run development scenarios on this listing.</span>
          </div>
        </div>
      )}
      <div className="flex flex-row w-full justify-between items-top mt-5">
        <div className="divider divider-horizontal"></div>
        {scenarios &&
          scenarios.map((scenario, idx) => {
            return (
              <React.Fragment key={idx}>
                <div className="flex-auto">
                  <h3>
                    Scenario: {scenario.adu_qty} {scenario.unit_type.br}BR, {scenario.unit_type.ba}BA ADUs
                  </h3>
                  <p>
                    Each {scenario.unit_type.sqft.toLocaleString()} sqft, {scenario.unit_type.stories} stories
                  </p>
                  <div className="stats shadow mb-3 mt-2">
                    <div className="stat">
                      <div className="stat-title">Size</div>
                      <div className="stat-value">
                        {scenario.unit_type.br}BR,{scenario.unit_type.ba}BA
                      </div>
                      <div className="stat-desc">{scenario.unit_type.sqft} sqft each</div>
                    </div>
                    <div className="stat">
                      <div className="stat-title"># of ADUs</div>
                      <div className="stat-value">{scenario.adu_qty}</div>
                      <div className="stat-desc">units</div>
                    </div>
                    <div className="stat">
                      <div className="stat-title">Cap Rate</div>
                      <div className="stat-value">{scenario.finances?.cap_rate || "?"}%</div>
                      <div className="stat-desc">cap</div>
                    </div>
                  </div>

                  <h3>Total Capital In: ${scenario.finances?.capital_sum.toLocaleString() || "?"}</h3>
                  <h3>NOI: ${scenario.finances?.net_income.toLocaleString() || "?"}</h3>
                  <div className="divider"></div>
                  {scenario.finances && <DevFinances finances={scenario.finances} />}
                  {/*<p>{JSON.stringify(scenario.finances)}</p>*/}
                </div>
                <div key={idx + 9999} className="divider divider-horizontal"></div>
              </React.Fragment>
            )
          })}
      </div>
    </div>
  )
}
