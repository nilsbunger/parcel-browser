import * as React from "react"
import { useCallback, useEffect, useState } from "react"

import { ScrollArea, Table } from "@mantine/core"
import { Link, useNavigate } from "react-router-dom"
import useSWR from "swr"
import { fetcher } from "../utils/fetcher"
import Slider from 'rc-slider';
import 'rc-slider/assets/index.css';

interface PropertiesProps {
  data: {
    title: string
    author: string
    year: number
    reviews: { positive: number; negative: number }
  }[]
}


const FilterRow = ({ columns, onFilterChange }) => {
  const [activeFilters, setActiveFilters] = useState([]);
  const [availableColumns, setAvailableColumns] = useState(columns);

  const handleAddFilter = (column) => {
    setActiveFilters([...activeFilters, { column, value: "" }]);
    setAvailableColumns(availableColumns.filter((col) => col !== column));
  };

  const handleRemoveFilter = (index) => {
    const removedFilter = activeFilters[index];
    setActiveFilters(activeFilters.filter((_, i) => i !== index));
    setAvailableColumns([...availableColumns, removedFilter.column]);
  };

  const handleFilterChange = (index, value) => {
    const newFilters = [...activeFilters];
    newFilters[index].value = value;
    setActiveFilters(newFilters);
    onFilterChange(newFilters);
  };

  return (
    <div style={{ display: "flex", alignItems: "center" }}>
      {activeFilters.map((filter, index) => (
        <div key={index} style={{ margin: "0 10px" }}>
          <select
            value={filter.value}
            onChange={(e) => handleFilterChange(index, e.target.value)}
          >
            <option value="">Select {filter.column}</option>
            {/* Add options specific to the column here */}
          </select>
          <span
            style={{ color: "red", cursor: "pointer", marginLeft: "5px" }}
            onClick={() => handleRemoveFilter(index)}
          >
            x
          </span>
        </div>
      ))}

      {availableColumns.length > 0 && (
        <div style={{ margin: "0 10px" }}>
          <button
            onClick={() => {
              // Dummy function to handle showing a dropdown of available columns
              // Replace this with your own implementation
            }}
          >
            +
          </button>
          {/* Dropdown with available columns */}
          <div style={{ display: "none" }}>
            {availableColumns.map((column, index) => (
              <div key={index} onClick={() => handleAddFilter(column)}>
                {column}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

const DropdownButtonShell = ({ label, children }) => {
  const [isDropdownVisible, setIsDropdownVisible] = useState(false);

  const toggleDropdown = () => {
    setIsDropdownVisible(!isDropdownVisible);
  };

  return (
    <div className="relative inline-block">
      <button
        className="bg-prim-600 text-white px-4 py-2 rounded shadow hover:bg-prim-800"
        onClick={toggleDropdown}
      >
        {label}
      </button>
      {isDropdownVisible && (
        <div className="absolute mt-2 bg-white shadow rounded w-64 z-10 border-gray-800 border-solid border">
          {children}
        </div>
      )}
    </div>
  );
};

const DropdownRangeButton = ({ options, onSelectionChange }) => {
  const [minValue, setMinValue] = useState<number>(0);
  const [maxValue, setMaxValue] = useState<number>(100);

  const handleSliderChange = (value) => {
    setMinValue(value[0]);
    setMaxValue(value[1]);
  };
  return (<DropdownButtonShell label="Lot size">
    <div className="absolute mt-2 bg-white shadow rounded w-64 z-10 p-4">
      <div className="flex items-center">
        <input
          type="number"
          value={minValue}
          className="border p-1 rounded w-16 text-center"
          onChange={(e) => setMinValue(Number(e.target.value))}
        />
        <div className="flex-grow mx-2">
          <Slider range
                  min={0}
                  max={100}
                  value={[minValue, maxValue]}
                  onChange={handleSliderChange}
          />
        </div>
        <input
          type="number"
          value={maxValue}
          className="border p-1 rounded w-16 text-center"
          onChange={(e) => setMaxValue(Number(e.target.value))}
        />
      </div>
    </div>
  </DropdownButtonShell>)
}
const DropdownMultiselectButton = ({ options, onSelectionChange }) => {
  const [selectedOptions, setSelectedOptions] = useState<string[]>([]);

  const handleOptionChange = (option) => {
    if (selectedOptions.includes(option)) {
      setSelectedOptions(selectedOptions.filter((item) => item !== option));
    } else {
      setSelectedOptions([...selectedOptions, option]);
    }
  };

  // Callback to parent component
  React.useEffect(() => {
    onSelectionChange(selectedOptions);
  }, [selectedOptions, onSelectionChange]);

  return (<DropdownButtonShell label="Zoning">
    {options.map((option: string, index: React.Key) => (
      <label
        key={index}
        className="flex items-center px-4 py-2 hover:bg-gray-200 cursor-pointer"
      >
        <input
          className="mr-2"
          type="checkbox"
          checked={selectedOptions.includes(option)}
          onChange={() => handleOptionChange(option)}
        />
        <span>{option}</span>
      </label>
    ))}

  </DropdownButtonShell>)
}

const Testbed = () => {
  const handleSelectionChange = (selectedOptions) => {
    console.log('Selected options:', selectedOptions);
  };

  return (
    <div className="flex gap-4">
      <DropdownMultiselectButton
        options={['Option 1', 'Option 2', 'Option 3']}
        onSelectionChange={handleSelectionChange}
      />
      <DropdownRangeButton
        options={['Option 1', 'Option 2', 'Option 3']}
        onSelectionChange={handleSelectionChange}
      />
    </div>
  );

}

export default function PropertiesPage() {
  const navigate = useNavigate()
  useEffect(() => {
    document.title = "Properties"
    // load initial values of state from local storage
  }, [])

  // get property profiles
  const { data, error, isValidating } = useSWR(`/api/properties/profiles`, fetcher)
  console.log("isValidating", isValidating)
  console.log("data", data)

  // const data = [{ id: 1, address: "555 main st" }]

  // const { classes, theme } = useStyles();

  const onRowClick = useCallback((e: React.MouseEvent<HTMLTableRowElement, MouseEvent>) => {
    const id = e.currentTarget.getAttribute("data-id")
    console.log("row click:", e)
    console.log("id", id)
    navigate(`${id}`)
    // e.preventDefault()
    // if (id) {
    //   router.push(`/props/${id}`)
    // }
  }, [])

  if (error) return <div>failed to load properties list</div>
  if (isValidating) return <div>loading...</div>

  const rows = data.map((row: any) => {
    return (
      <tr
        key={row.id}
        data-id={row.id}
        onClick={onRowClick}
        className="cursor-pointer border-primarylight hover:border-solid"
      >
        <td>{row.id}</td>
        <td>
          {row.address.street_addr}, {row.address.city}, {row.address.state} {row.address.zip}
        </td>
        <td>{row.legal_entity?.name}</td>
      </tr>
    )
  })

  return (<>
      <div className="flex flex-row">
        <div className="flex-grow text-right">
          <Link to={{ pathname: `/bov/1` }} className="btn btn-primary btn-sm mr-4">
            BOV example
          </Link>
          <Link to={{ pathname: '/reactgrid/1' }} className="btn btn-primary btn-sm mr-4">
            ReactGrid example
          </Link>
          <Link to={{ pathname: `/properties/new` }} className="btn btn-primary btn-sm">
            ADD...
          </Link>

          {/*<Anchor component="a" type="button" href="/properties/new" className="">ADD...</Anchor>*/}
        </div>
      </div>
      {/*<FilterRow columns={["address", "entity"]} onFilterChange={(filters: any) => console.log(filters)}/>*/}
      <Testbed/>
      <ScrollArea type="auto">
        <Table verticalSpacing="xs">
          <thead>
          <tr>
            <th>ID</th>
            <th>Address</th>
            <th>Entity</th>
          </tr>
          </thead>
          <tbody>{rows}</tbody>
        </Table>
      </ScrollArea>
    </>
  )
}
