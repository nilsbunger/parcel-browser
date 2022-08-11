import useSWR from 'swr';
import * as React from 'react';
import { useState } from 'react';
import {
  createColumnHelper,
  flexRender,
  getCoreRowModel,
  useReactTable,
  getSortedRowModel,
  SortingState,
  getFilteredRowModel,
  getFacetedRowModel,
  getFacetedUniqueValues,
  getFacetedMinMaxValues,
  getPaginationRowModel,
  Table,
  Column,
  ColumnFiltersState,
} from '@tanstack/react-table';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import { Link } from 'react-router-dom';
import { fetcher } from '../utils/fetcher';
import { Listing } from '../types';
import ListingsMap from '../components/layout/ListingsMap';
import { Updater, useImmer } from 'use-immer';

const asSqFt = (m) => Math.round(m * 3.28 * 3.28);
const asFt = (m) => Math.round(m * 3.28);

function snakeCaseToTitleCase(word: string) {
  const tokenized = word.toLowerCase().split('_');
  for (let i = 0; i < tokenized.length; i++) {
    tokenized[i] = tokenized[i][0].toUpperCase() + tokenized[i].slice(1);
  }

  return tokenized.join(' ');
}

const columnHelper = createColumnHelper();

const basicAccessor = (cell) => {
  return String(cell.getValue()).slice(0, 20);
};

const apnAccessor = ({ row }) => (
  <Link
    to={{ pathname: `/analysis/${row.getValue('analysis_id')}` }}
    className="underline text-darkblue"
  >
    {row.getValue('apn')}
  </Link>
);

const addressAccessor = ({ row }) => (
  <div
    className={
      'relative ' +
      (row.getValue('apn').slice(8, 10) !== '00' ? 'bg-gray-300' : '')
    }
  >
    <Link
      to={{ pathname: `/analysis/${row.original.analyzedlisting_set.id}` }}
      className="underline text-darkblue"
    >
      {row.getValue('address').slice(0, 20)}
    </Link>
    {row.getValue('metadata')['category'] == 'new' && (
      <div className="badge badge-accent text-2xs absolute top-[-6px] px-1 right-0">
        NEW
      </div>
    )}{' '}
    {row.original.is_tpa && (
      <div className="mb-1 gap-2 badge badge-primary text-med">TPA</div>
    )}
  </div>
);

const asSqFtAccessor = ({ cell }) => asSqFt(cell.getValue()).toLocaleString();

const roundingAccessor = ({ cell }) => {
  return cell.getValue().toPrecision(2);
};

const priceAccessor = ({ cell }) => {
  const prev_value =
    cell.row.getValue('metadata')['prev_values'][cell.column.id];
  if (prev_value) {
    return (
      <span>
        ${cell.getValue().toLocaleString()} <s> {prev_value} </s>
      </span>
    );
  } else {
    return '$' + cell.getValue().toLocaleString();
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
  apn: { visible: false, accessor: apnAccessor },
  address: { visible: true, accessor: addressAccessor },
  zone: { visible: true },
  num_existing_buildings: { visible: false },
  is_flag_lot: { visible: false },
  carports: { visible: false },
  garages: { visible: false },
  neighborhood: { visible: true },
  parcel_size: {
    visible: true,
    headername: 'Lot size',
    accessor: asSqFtAccessor,
  },
  existing_living_area: { visible: false, accessor: asSqFtAccessor },
  existing_floor_area: { visible: false, accessor: asSqFtAccessor },
  existing_FAR: { visible: false, accessor: roundingAccessor },
  num_new_buildings: { visible: false },
  new_building_areas: { visible: false },
  total_added_building_area: { visible: false },
  garage_con_units: { visible: false },
  garage_con_area: { visible: false },
  total_new_units: { visible: false },
  total_added_area: { visible: false },
  new_FAR: { visible: false },
  max_FAR: { visible: false, accessor: roundingAccessor },
  potential_FAR: { visible: false, accessor: roundingAccessor },
  limiting_factor: { visible: false },
  main_building_poly_area: { visible: false },
  accessory_buildings_polys_area: { visible: false },
  avail_geom_area: { visible: false, accessor: asSqFtAccessor },
  avail_area_by_FAR: {
    visible: true,
    headername: 'Build sqft',
    accessor: asSqFtAccessor,
  },
  parcel_sloped_area: { visible: false },
  parcel_sloped_ratio: { visible: false },
  total_score: { visible: false },
  cap_ratio_score: { visible: false },
  open_space_score: { visible: false },
  project_size_score: { visible: false },
  can_lot_split: { visible: false },
  new_lot_area_ratio: { visible: false },
  new_lot_area: { visible: false },
  git_commit_hash: { visible: false },
  datetime_ran: { visible: false },
  front_setback: { visible: false },
  br: { visible: true },
  ba: { visible: true },
  price: { visible: true, accessor: priceAccessor, enableColumnFilter: true },
  zipcode: { visible: false },
  founddate: { visible: false },
  seendate: { visible: false },
  mlsid: { visible: false },
  mls_floor_area: { visible: false },
  thumbnail: { visible: false },
  listing_url: { visible: false },
  soldprice: { visible: false },
  status: { visible: false, accessor: statusAccessor },
  analysis_id: { visible: false },
  metadata: { visible: false }, // Need to make this one ALWAYS invisible
};

type QueryResponse = {
  items: (Listing & { analyzedlisting_set: { details: object } })[];
  count: number;
};

function columnFiltersToQuery(filters: ColumnFiltersState) {
  const query = {};
  filters.forEach((item) => {
    if (Array.isArray(item.value) && item.value.length == 2) {
      // Then it's a min max filter
      query[`${item.id}__gte`] = parseInt(item.value[0]) || undefined;
      query[`${item.id}__lte`] = parseInt(item.value[1]) || undefined;
    }
  });
  return query;
}

export function ListingsPage() {
  const [minPrice, setMinPrice] = useState();
  const [maxPrice, setMaxPrice] = useState();
  const [pageSize, setPageSize] = useState<number>(50);
  const [pageIndex, setPageIndex] = useState<number>(0);
  const [sorting, setSorting] = React.useState<SortingState>([]);
  const [columnFilters, setColumnFilters] = useImmer<ColumnFiltersState>([]);

  const { data, error } = useSWR<QueryResponse>(
    [
      'api/listings',
      {
        params: {
          limit: pageSize,
          offset: pageIndex * pageSize,
          order_by: sorting.length > 0 ? sorting[0].id : undefined,
          asc: sorting.length > 0 ? !sorting[0].desc : undefined,
          ...columnFiltersToQuery(columnFilters),
        },
      },
    ],
    fetcher
  );

  // We gotta do this weird conversion as the data comes in weirdly shaped from the backend
  // Fix the backend to get this to be the correct shape
  const listings = data
    ? (data.items.map((item) => ({
        ...item,
        // This weird type casting helps squash errors. Only temporary
        ...item.analyzedlisting_set.details,
        metadata: {
          category: 'new',
          prev_values: {},
        },
      })) as Listing[])
    : [];

  const initialVisibility = Object.fromEntries(
    Object.entries(initialColumnState).map(([k, v]) => [k, v['visible']])
  );
  const [columnVisibility, setColumnVisibility] =
    useState<Record<string, boolean>>(initialVisibility);

  const toggleVisibility = (event) => {
    // console.log('Vis = ', columnVisibility);
    // console.log('Should toggle', event.target.id);
    setColumnVisibility((prev) => {
      const new_vis = Object.assign({}, prev);
      new_vis[event.target.id] = !new_vis[event.target.id];
      return new_vis;
    });
    // console.log(columnVisibility);
  };

  const columns = Object.keys(initialColumnState).map((fieldname) => ({
    accessorKey: fieldname,
    cell: initialColumnState[fieldname].accessor || basicAccessor,
    header:
      initialColumnState[fieldname].headername ||
      snakeCaseToTitleCase(fieldname),
    enableColumnFilter:
      initialColumnState[fieldname].enableColumnFilter || false,
  }));
  const table = useReactTable({
    data: listings,
    columns,
    state: {
      columnVisibility,
      sorting,
      pagination: {
        pageIndex,
        pageSize,
      },
      columnFilters,
    },
    // onColumnVisibilityChange: setColumnVisibility,
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    manualSorting: true,
    manualPagination: true,
    pageCount: data ? Math.ceil(data.count / pageSize) : null,
    getFilteredRowModel: getFilteredRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    getFacetedRowModel: getFacetedRowModel(),
    getFacetedUniqueValues: getFacetedUniqueValues(),
    getFacetedMinMaxValues: getFacetedMinMaxValues(),
  });

  if (error) return <div>failed to load</div>;
  if (!data) return <div>loading...</div>;

  // Render each date as a separate table
  return (
    <div className={'flex flex-row'}>
      <ListingsMap
        listings={table.getRowModel().rows.map((row) => row.original)}
      />
      <div
        id="tablegrouper"
        className={'overflow-y-auto max-h-[80vh] grow px-5 overflow-x-auto'}
      >
        <div className="pagination">
          <button
            onClick={() => setPageIndex(0)}
            disabled={!table.getCanPreviousPage()}
            className="btn btn-xs btn-outline btn-square"
          >
            {'<<'}
          </button>{' '}
          <button
            onClick={() => setPageIndex((prev) => prev - 1)}
            disabled={!table.getCanPreviousPage()}
            className="btn btn-xs btn-outline btn-square"
          >
            {'<'}
          </button>{' '}
          <button
            onClick={() => setPageIndex((prev) => prev + 1)}
            disabled={!table.getCanNextPage()}
            className="btn btn-xs btn-outline btn-square"
          >
            {'>'}
          </button>{' '}
          <button
            onClick={() => setPageIndex(table.getPageCount() - 1)}
            disabled={!table.getCanNextPage()}
            className="btn btn-xs btn-outline btn-square"
          >
            {'>>'}
          </button>{' '}
          <span className="ml-4 mr-4">
            Page{' '}
            <strong>
              {pageIndex + 1} of {table.getPageCount()}
            </strong>{' '}
          </span>
          <span>
            Go to page:{' '}
            <input
              type="number"
              value={pageIndex + 1}
              onChange={(e) => {
                const page = e.target.value ? Number(e.target.value) - 1 : 0;
                setPageIndex(page);
              }}
              style={{ width: '100px' }}
              className="border rounded px-2 border-gray-400"
            />
          </span>{' '}
          <select
            value={pageSize}
            onChange={(e) => {
              setPageSize(Number(e.target.value));
            }}
            className="ml-4"
          >
            {[10, 25, 50, 100, 250, 500].map((pageSize) => (
              <option key={pageSize} value={pageSize}>
                Show {pageSize}
              </option>
            ))}
          </select>
        </div>
        <ListingTable table={table} setColumnFilters={setColumnFilters} />

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
                  type="checkbox"
                  checked={columnVisibility[columnKey]}
                  onChange={toggleVisibility}
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

function ListingTable({
  table,
  setColumnFilters,
}: {
  table: Table<Listing>;
  setColumnFilters: Updater<ColumnFiltersState>;
}) {
  return (
    <>
      <table className="table-auto pb-8 border-spacing-2 overflow-x-auto whitespace-nowrap border-separate">
        <thead>
          {table.getHeaderGroups().map((headerGroup) => (
            <tr key={headerGroup.id}>
              {headerGroup.headers.map((header) => {
                return (
                  <th key={header.id} colSpan={header.colSpan}>
                    {header.isPlaceholder ? null : (
                      <>
                        <div
                          {...{
                            className: header.column.getCanSort()
                              ? 'cursor-pointer select-none'
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
                        {header.column.getCanFilter() ? (
                          <div>
                            <Filter
                              column={header.column}
                              table={table}
                              setColumnFilters={setColumnFilters}
                            />
                          </div>
                        ) : null}
                      </>
                    )}
                  </th>
                );
              })}
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
      <div className="h-2" />
    </>
  );
}

function Filter({
  column,
  table,
  setColumnFilters,
}: {
  column: Column<any, unknown>;
  table: Table<any>;
  setColumnFilters: Updater<ColumnFiltersState>;
}) {
  const firstValue = table
    .getPreFilteredRowModel()
    .flatRows[0]?.getValue(column.id);

  const columnFilterValue = column.getFilterValue();

  // Converting to sqft if necessary
  let modifier = (x) => x;
  if (column.accessorFn === asSqFtAccessor) {
    modifier = asSqFt;
  }

  const sortedUniqueValues = React.useMemo(
    () =>
      typeof firstValue === 'number'
        ? []
        : Array.from(column.getFacetedUniqueValues().keys()).sort(),
    [column.getFacetedUniqueValues()]
  );

  return typeof firstValue === 'number' ? (
    <div>
      <div className="flex space-x-2">
        <DebouncedInput
          type="number"
          min={modifier(Number(column.getFacetedMinMaxValues()?.[0] ?? ''))}
          max={modifier(Number(column.getFacetedMinMaxValues()?.[1] ?? ''))}
          value={(columnFilterValue as [number, number])?.[0] ?? ''}
          onChange={(value) => {
            setColumnFilters((draft) => {
              const filterIndex = draft.findIndex(
                (item) => item.id === column.id
              );
              if (filterIndex === -1) {
                draft.push({
                  id: column.id,
                  value: [modifier(value), undefined],
                });
              } else {
                draft[filterIndex].value[0] = modifier(value);
              }
            });
            // column.setFilterValue((old: [number, number]) => [
            //   modifier(value),
            //   old?.[1],
            // ]);
          }}
          placeholder={`Min ${
            column.getFacetedMinMaxValues()?.[0]
              ? `(${modifier(column.getFacetedMinMaxValues()?.[0])})`
              : ''
          }`}
          className="w-24 border shadow rounded"
        />
        <DebouncedInput
          type="number"
          min={modifier(Number(column.getFacetedMinMaxValues()?.[0] ?? ''))}
          max={modifier(Number(column.getFacetedMinMaxValues()?.[1] ?? ''))}
          value={(columnFilterValue as [number, number])?.[1] ?? ''}
          onChange={(value) => {
            setColumnFilters((draft) => {
              const filterIndex = draft.findIndex(
                (item) => item.id === column.id
              );
              if (filterIndex === -1) {
                draft.push({
                  id: column.id,
                  value: [undefined, modifier(value)],
                });
              } else {
                draft[filterIndex].value[1] = modifier(value);
              }
            });
            // column.setFilterValue((old: [number, number]) => [
            //   old?.[0],
            //   modifier(value),
            // ]);
          }}
          placeholder={`Max ${
            column.getFacetedMinMaxValues()?.[1]
              ? `(${modifier(column.getFacetedMinMaxValues()?.[1])})`
              : ''
          }`}
          className="w-24 border shadow rounded"
        />
      </div>
      <div className="h-1" />
    </div>
  ) : (
    <>
      <datalist id={column.id + 'list'}>
        {sortedUniqueValues.slice(0, 5000).map((value: any) => (
          <option value={value} key={value} />
        ))}
      </datalist>
      <DebouncedInput
        type="text"
        value={(columnFilterValue ?? '') as string}
        onChange={(value) => column.setFilterValue(value)}
        placeholder={`Search... (${column.getFacetedUniqueValues().size})`}
        className="w-36 border shadow rounded"
        list={column.id + 'list'}
      />
      <div className="h-1" />
    </>
  );
}

// A debounced input react component
// from https://tanstack.com/table/v8/docs/examples/react/filters
function DebouncedInput({
  value: initialValue,
  onChange,
  debounce = 500,
  ...props
}: {
  value: string | number;
  onChange: (value: string | number) => void;
  debounce?: number;
} & Omit<React.InputHTMLAttributes<HTMLInputElement>, 'onChange'>) {
  const [value, setValue] = React.useState(initialValue);

  React.useEffect(() => {
    setValue(initialValue);
  }, [initialValue]);

  React.useEffect(() => {
    const timeout = setTimeout(() => {
      onChange(value);
    }, debounce);

    return () => clearTimeout(timeout);
  }, [value]);

  return (
    <input
      {...props}
      value={value}
      onChange={(e) => setValue(e.target.value)}
      className="input input-bordered w-[160px] max-w-xs"
    />
  );
}
