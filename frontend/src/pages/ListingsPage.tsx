import useSWR from 'swr';
import React, { useState } from 'react';
import {
  createColumnHelper,
  flexRender,
  getCoreRowModel,
  useReactTable,
  getSortedRowModel,
  SortingState,
} from '@tanstack/react-table';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import { Link } from 'react-router-dom';
import { fetcher } from '../utils/fetcher';

const asSqFt = (m) => Math.round(m * 3.28 * 3.28)
const asFt = (m) => Math.round(m * 3.28)

function snakeCaseToTitleCase(word: string) {
  const tokenized = word.toLowerCase().split('_');
  for (let i = 0; i < tokenized.length; i++) {
    tokenized[i] = tokenized[i][0].toUpperCase() + tokenized[i].slice(1);
  }

  return tokenized.join(' ');
}

const columnHelper = createColumnHelper();

const basicAccessor = (cell) => cell.getValue();

const apnAccessor = ({ row }) => (
  <>
    <Link
      to={{ pathname: `/analysis/${row.getValue('analysis_id')}` }}
      className="underline text-darkblue"
    >
      {row.getValue('apn')}
    </Link>
  </>
);

const asSqFtAccessor = ({cell}) => asSqFt(cell.getValue())

const roundingAccessor = ({ cell }) => {
  return cell.getValue().toPrecision(2);
};

const priceAccessor = ({ cell }) => {
  const prev_value =
    cell.row.getValue('metadata')['prev_values'][cell.column.id];
  if (prev_value) {
    return (
      <span>
        <s> {prev_value} </s> {cell.getValue()}{' '}
      </span>
    );
  } else {
    return cell.getValue();
  }
};

const statusAccessor = ({ row }) => {
  return row.getValue('metadata')['category'] == 'new' ? (
    <div className="badge badge-accent">NEW</div>
  ) : (
    ''
  );
};

const initialColumnState = {
  apn: {visible: true, accessor: apnAccessor,},
  address: {visible: true},
  zone: {visible: true,},
  num_existing_buildings: {visible: false,},
  is_flag_lot: {visible: false,},
  carports: {visible: false,},
  garages: {visible: false,},
  parcel_size: {visible: true, accessor: asSqFtAccessor},
  existing_living_area: {visible: false, accessor: asSqFtAccessor},
  existing_floor_area: {visible: false, accessor: asSqFtAccessor},
  existing_FAR: {visible: true, accessor: roundingAccessor},
  num_new_buildings: {visible: false,},
  new_building_areas: {visible: false,},
  total_added_building_area: {visible: false,},
  garage_con_units: {visible: false,},
  garage_con_area: {visible: false,},
  total_new_units: {visible: false,},
  total_added_area: {visible: false,},
  new_FAR: {visible: false,},
  max_FAR: {visible: true, accessor: roundingAccessor},
  potential_FAR: {visible: true, accessor: roundingAccessor},
  limiting_factor: {visible: false,},
  main_building_poly_area: {visible: false,},
  accessory_buildings_polys_area: {visible: false,},
  avail_geom_area: {visible: true, accessor: asSqFtAccessor},
  avail_area_by_FAR: {visible: true, accessor: asSqFtAccessor},
  parcel_sloped_area: {visible: false,},
  parcel_sloped_ratio: {visible: false,},
  total_score: {visible: false,},
  cap_ratio_score: {visible: false,},
  open_space_score: {visible: false,},
  project_size_score: {visible: false,},
  can_lot_split: {visible: false,},
  new_lot_area_ratio: {visible: false,},
  new_lot_area: {visible: false,},
  git_commit_hash: {visible: false,},
  datetime_ran: {visible: false,},
  front_setback: {visible: false,},
  br: {visible: true,},
  ba: {visible: true,},
  price: {visible: true, accessor: priceAccessor},
  zipcode: {visible: false,},
  founddate: {visible: false,},
  seendate: {visible: false,},
  mlsid: {visible: false,},
  mls_floor_area: {visible: false,},
  thumbnail: {visible: false,},
  listing_url: {visible: false,},
  soldprice: {visible: false,},
  status: {visible: true, accessor: statusAccessor},
  analysis_id: {visible: false,},
  metadata: {visible: false,}, // Need to make this one ALWAYS invisible
};

export function ListingsPage() {
  const { data, error } = useSWR('/dj/api/listings', fetcher);
  const initialVisibility = Object.fromEntries(
    Object.entries(initialColumnState).map(([k, v]) => [k, v['visible']])
  );
  const [columnVisibility, setColumnVisibility] =
    useState<Record<string, boolean>>(initialVisibility);

  if (error) return <div>failed to load</div>;
  if (!data) return <div>loading...</div>;

  const dates = Object.keys(data).sort().reverse();

  const toggleVisibility = (event, x) => {
    console.log('Vis = ', columnVisibility);
    console.log('Should toggle', event.target.id);
    setColumnVisibility((prev) => {
      const new_vis = Object.assign({}, prev);
      new_vis[event.target.id] = !new_vis[event.target.id];
      return new_vis;
    });
    console.log(columnVisibility);
  };
  // Render each date as a separate table
  return (
    <div>
      <MapContainer
        center={[data[dates[0]][0].centroid_y, data[dates[0]][0].centroid_x]}
        zoom={13}
        scrollWheelZoom={true}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {Object.values(data).map((listings) =>
          (listings as unknown[]).map((listing) => (
            <Marker position={[listing.centroid_y, listing.centroid_x]}>
              <Popup>
                <p>
                  APN:
                  <Link
                    to={{
                      pathname: `/analysis/${listing.analysis_id}`,
                    }}
                    className="underline text-darkblue"
                  >
                    {listing.apn}
                  </Link>
                </p>
              </Popup>
            </Marker>
          ))
        )}
      </MapContainer>
      <div id="tablegrouper">
        <div className="badge badge-primary">neutral</div>
        {dates.map((date) => (
          <ListingTable
            key={date}
            date={date}
            data={data[date]}
            columnVisibility={columnVisibility}
          />
        ))}

        {/*Render column visibility checkboxes*/}
        <label>
          <input
            {...{
              type: 'checkbox',
              readOnly: true,
              // checked: table.getIsAllColumnsVisible(),
              // onChange: table.getToggleAllColumnsVisibilityHandler(),
            }}
          />{' '}
          Toggle All
        </label>
        {Object.keys(initialVisibility).map((columnKey) => {
          return (
            <div key={(columnKey += 'viz_chkbx')} className="px-1">
              <label>
                <input
                  id={columnKey}
                  {...{
                    type: 'checkbox',
                    checked: columnVisibility[columnKey],
                    onChange: toggleVisibility,
                  }}
                />{' '}
                {columnKey}
              </label>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function ListingTable({ date, data, columnVisibility }) {
  // Render a single day's listing table
  const [sorting, setSorting] = React.useState<SortingState>([]);

  const columns = Object.keys(initialColumnState).map((field) =>
    columnHelper.accessor(field, {
      header: snakeCaseToTitleCase(field),
      cell: initialColumnState[field].accessor || basicAccessor,
    })
  );

  const table = useReactTable({
    data: data,
    columns,
    state: {
      columnVisibility,
      sorting,
    },
    // onColumnVisibilityChange: setColumnVisibility,
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
  });

  return (
    <>
      <h1 className="pt-8">{date} Listings</h1>
      <table className="table-auto border-spacing-2 overflow-x-auto whitespace-nowrap border-separate">
        <thead>
          {table.getHeaderGroups().map((headerGroup) => (
            <tr key={headerGroup.id}>
              {headerGroup.headers.map((header) => (
                <th key={header.id}>
                  {header.isPlaceholder ? null : (
                    <div
                      {...{
                        className: header.column.getCanSort()
                          ? 'cursor-pointer select-none '
                          : '',
                        onClick: header.column.getToggleSortingHandler(),
                      }}
                    >
                      {flexRender(
                        header.column.columnDef.header,
                        header.getContext()
                      )}
                      {{
                        asc: ' 🔼',
                        desc: ' 🔽',
                      }[header.column.getIsSorted() as string] ?? null}
                    </div>
                  )}
                </th>
              ))}
            </tr>
          ))}
        </thead>
        <tbody>
          {table.getRowModel().rows.map((row) => (
            <tr key={row.id}>
              {row.getVisibleCells().map((cell) => {
                let foo = flexRender(
                  cell.column.columnDef.cell,
                  cell.getContext()
                );
                if (foo === null || foo.props.renderValue() === null) {
                  return <td key={cell.id}>None </td>;
                }
                if (typeof foo.props.renderValue() === 'object') {
                  console.log(
                    'WE have a problem in table cell rendering: ',
                    foo.props.renderValue()
                  );
                  return <td key={cell.id}>BAD</td>;
                } else {
                  return <td key={cell.id}> {foo} </td>;
                }
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </>
  );
}
