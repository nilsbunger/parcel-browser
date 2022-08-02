import useSWR from 'swr';
import React, { useState } from 'react';
import {
  createColumnHelper,
  flexRender,
  getCoreRowModel,
  useReactTable,
} from '@tanstack/react-table';
import { Link } from 'react-router-dom';
import { fetcher } from '../utils/fetcher';

function snakeCaseToTitleCase(word: string) {
  const tokenized = word.toLowerCase().split('_');
  for (let i = 0; i < tokenized.length; i++) {
    tokenized[i] = tokenized[i][0].toUpperCase() + tokenized[i].slice(1);
  }

  return tokenized.join(' ');
}

const columnHelper = createColumnHelper();

const initialColumnState = {
    "apn": true,
    "address": true,
    "zone": true,
    "num_existing_buildings": false,
    "is_flag_lot": false,
    "carports": false,
    "garages": false,
    "parcel_size": true,
    "existing_living_area": false,
    "existing_floor_area": false,
    "existing_FAR": true,
    "num_new_buildings": false,
    "new_building_areas": false,
    "total_added_building_area": false,
    "garage_con_units": false,
    "garage_con_area": false,
    "total_new_units": false,
    "total_added_area": false,
    "new_FAR": false,
    "max_FAR": true,
    "potential_FAR": true,
    "limiting_factor": false,
    "main_building_poly_area": false,
    "accessory_buildings_polys_area": false,
    "avail_geom_area": false,
    "avail_area_by_FAR": true,
    "parcel_sloped_area": false,
    "parcel_sloped_ratio": false,
    "total_score": false,
    "cap_ratio_score": false,
    "open_space_score": false,
    "project_size_score": false,
    "can_lot_split": false,
    "new_lot_area_ratio": false,
    "new_lot_area": false,
    "git_commit_hash": false,
    "datetime_ran": false,
    "front_setback": false,
    "bedrooms": true,
    "bathrooms": true,
    "price": true,
    "zipcode": false,
    "founddate": false,
    "seendate": false,
    "mlsid": false,
    "mls_floor_area": false,
    "thumbnail": false,
    "listing_url": false,
    "soldprice": false,
    "status": true
}

function roundIfNumber(val:any): any {
    if (typeof val == "number") {
        console.log (val + " is a number")
        return val.toPrecision(3)
    }
    return val
}

export function ListingsPage() {
  const { data, error } = useSWR('/dj/api/listings', fetcher);
  const [columnVisibility, setColumnVisibility] = useState(initialColumnState);

  const columns = data
    ? data.schema.fields.map((field) =>
        columnHelper.accessor(field.name, {
          header: snakeCaseToTitleCase(field.name),
          cell:
            field.name === 'apn'
              ? ({ row }) => (
                  <Link to={{ pathname: `/listings/${row.getValue('apn')}` }}>
                    {row.getValue('apn')}
                  </Link>
                )
              : ['price', 'bedrooms', 'bathrooms'].includes(field.name) // fields which should not get rounded
                ? ({ row }) => row.getValue(field.name)
                : ({ row }) => roundIfNumber(row.getValue(field.name)),
        })
      )
    : [];

  const table = useReactTable({
    data: data ? data.data : [],
    columns,
    state: {
      columnVisibility,
    },
    onColumnVisibilityChange: setColumnVisibility,
    getCoreRowModel: getCoreRowModel(),
  });

  if (error) return <div>failed to load</div>;
  if (!data) return <div>loading...</div>;
  console.log(columnVisibility);
  // console.log(table.getRowModel());
  return (
    <>
      <h1>Hello world from pages/ListingsPage.tsx!</h1>
      <table>
        <thead>
          {table.getHeaderGroups().map((headerGroup) => (
            <tr key={headerGroup.id}>
              {headerGroup.headers.map((header) => (
                <th key={header.id}>
                  {header.isPlaceholder
                    ? null
                    : flexRender(
                        header.column.columnDef.header,
                        header.getContext()
                      )}
                </th>
              ))}
            </tr>
          ))}
        </thead>
        <tbody>
          {table.getRowModel().rows.map((row) => (
            <tr key={row.id}>
              {row.getVisibleCells().map((cell) => (
                <td key={cell.id}>
                  {flexRender(cell.column.columnDef.cell, cell.getContext())}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
              <label>
        <input
          {...{
            type: 'checkbox',
            checked: table.getIsAllColumnsVisible(),
            onChange: table.getToggleAllColumnsVisibilityHandler(),
          }}
        />{' '}
        Toggle All
      </label>
      {table.getAllLeafColumns().map((column) => {
        return (
          <div key={column.id} className="px-1">
            <label>
              <input
                {...{
                  type: 'checkbox',
                  checked: column.getIsVisible(),
                  onChange: column.getToggleVisibilityHandler(),
                }}
              />{' '}
              {column.id}
            </label>
          </div>
        );
      })}

    </>
  );
}
