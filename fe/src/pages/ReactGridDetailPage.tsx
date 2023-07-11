import * as React from "react"
import { ReactNode, useCallback, useEffect } from "react"
import { render } from "react-dom";
import { ReactGrid, Column, Row } from "@silevis/reactgrid/dist/core";

// import "../../../../reactgrid/src/styles.css";
import "@silevis/reactgrid/dist/styles.scss";

interface Person {
  name: string;
  surname: string;
}

const getPeople = (): Person[] => [
  { name: "Thomas", surname: "Goldman" },
  { name: "Susie", surname: "Quattro" },
  { name: "", surname: "" }
];

const getColumns = (): Column[] => [
  { columnId: "name", width: 150 },
  { columnId: "surname", width: 150 }
];

const headerRow: Row = {
  rowId: "header",
  cells: [
    { type: "header", text: "Name" },
    { type: "header", text: "Surname" }
  ]
};

const getRows = (people: Person[]): Row[] => [
  headerRow,
  ...people.map<Row>((person, idx) => ({
    rowId: idx,
    cells: [
      { type: "text", text: person.name },
      { type: "text", text: person.surname }
    ]
  }))
];

export default function ReactGridDetailPage() {
    const [people] = React.useState<Person[]>(getPeople());

  const rows = getRows(people);
  const columns = getColumns();

  return (
    <div>
      <h1>ReactGridDetailPage</h1>
      <ReactGrid rows={rows} columns={columns} />
    </div>
    )

}
