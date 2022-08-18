import useSWR from 'swr';
import * as React from 'react';
import { useEffect, useState } from 'react';
import {
  ColumnFiltersState,
  createColumnHelper,
  getCoreRowModel,
  getFacetedMinMaxValues,
  getFacetedRowModel,
  getFacetedUniqueValues,
  getFilteredRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  SortingState,
  useReactTable,
} from '@tanstack/react-table';
import { Link } from 'react-router-dom';
import { fetcher, swrLaggy } from '../utils/fetcher';
import { Listing } from '../types';
import ListingsMap from '../components/layout/ListingsMap';
import { useImmer } from 'use-immer';
import TablePagination from '../components/TablePagination';
import ListingTable from '../components/ListingTable';

const asSqFt = (m) => Math.round(m * 3.28 * 3.28);
const asFt = (m) => Math.round(m * 3.28);
const oneDay = 1000 * 60 * 60 * 24; // in ms (time units)

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
      to={{ pathname: `/analysis/${row.getValue('analysis_id')}` }}
      className="underline text-darkblue"
    >
      {row.getValue('address').slice(0, 20)}
    </Link>

    {row.original.is_tpa && (
      <div className="mb-1 gap-2 badge badge-primary text-med">TPA</div>
    )}{' '}
    {row.original.is_mf && (
      <div className="badge badge-accent text-med">
        MF
      </div>
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

// calculate days since found
const founddateAccessor = ({ cell }) => {
  const foundDate = cell.getValue();
  let foundtime = (new Date(foundDate)).getTime()
  let nowtime = Date.now()
  return Math.round((nowtime - foundtime) / oneDay);
};

const mfFilterFn = (row, columnId, filterValue) => {
  return (row.original.is_mf || !filterValue)
}

// To set a column to be filterable, set enableColumnFilter to true, and make sure to provide
// a filterFn (https://tanstack.com/table/v8/docs/api/features/filters)
const initialColumnState = {
  founddate: {
    visible: true,
    headername: "DSU",
    accessor: founddateAccessor,
  },
  apn: { visible: false, accessor: apnAccessor },
  address: { visible: true, accessor: addressAccessor },
  zone: { visible: true },
  is_mf: {
    visible: false,
    enableColumnFilter: true,
    filterFn: mfFilterFn,
  },
  max_cap_rate: {
    visible: true,
    headername: "CapRate",
  },
  num_existing_buildings: { visible: false },
  is_flag_lot: { visible: false },
  carports: { visible: false },
  garages: { visible: false },
  neighborhood: {
    visible: true,
    enableColumnFilter: true,
    filterFn: 'includesString',
  },
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
  price: {
    visible: true,
    accessor: priceAccessor,
    enableColumnFilter: true,
    filterFn: 'inNumberRange',
  },
  zipcode: { visible: false },
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

// Create query parameters for filtering, depending on type of filter
function columnFiltersToQuery(filters: ColumnFiltersState) {
  const query = {};
  filters.forEach((item) => {
    if (Array.isArray(item.value) && item.value.length == 2) {
      // Then it's a min max filter
      query[`${item.id}__gte`] = parseInt(item.value[0]) || undefined;
      query[`${item.id}__lte`] = parseInt(item.value[1]) || undefined;
    } else if (typeof item.value === 'string') {
      query[`${item.id}__contains`] = item.value;
    } else if (typeof item.value == 'boolean') {
      query[`${item.id}`] = item.value;
    }
  });
  return query;
}

export function ListingsPage() {
  const [pageSize, setPageSize] = useState<number>(50);
  const [pageIndex, setPageIndex] = useState<number>(0);
  const [sorting, setSorting] = React.useState<SortingState>([]);
  const [columnFilters, setColumnFilters] = useImmer<ColumnFiltersState>([]);
  const [isMfChecked, setIsMfChecked] = React.useState<boolean>(false);

  const { data, error, isValidating } = useSWR(
    [
      '/api/listings',
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
    fetcher,
    { use: [swrLaggy] }
  );
  console.log (data)
  useEffect(() => {
    document.title = 'Listings'
  }, []);

  const listings = data
    ? (data.items.map((item) => {
      const listing = {
        ...item,
        // This weird type casting helps squash errors. Only temporary
        ...(item.analysis as object),
      };
      delete listing.analysis;
      return listing;
    }) as Listing[])
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
    filterFn: initialColumnState[fieldname].filterFn,
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

  if (error) return (
    <div className="md:container px-8 lg:px-16 pt-2">
      <h2>Failed to load</h2>
      <p>Try <a href='/dj/accounts/login/'>logging in?</a></p>
    </div>)

  const onMfFilterCheck = (e) => {
    setIsMfChecked(!isMfChecked)
    setColumnFilters((draft) => {
      // convoluted solution from react-table for updating column filters.
      const isMfFilter = draft.find((columnFilter) => columnFilter.id==='is_mf')
      if (!isMfFilter) {
        draft.push({id: 'is_mf', value:!isMfChecked})
      } else {
        isMfFilter.value = !isMfChecked
      }
    });
  }

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
        <p>{isValidating ? 'Fetching...' : 'Up to date'}</p>
        <TablePagination
          table={table}
          pageIndex={pageIndex}
          pageSize={pageSize}
          setPageIndex={setPageIndex}
          setPageSize={setPageSize}
        />
        <div className="form-control w-36">
          <label className="cursor-pointer label">
            <input type="checkbox" value="{isMfChecked}" className="checkbox checkbox-accent"
                   onChange={onMfFilterCheck}/>
            <span className="label-text">Multifamily-only</span>
          </label>
        </div>

        <ListingTable table={table} setColumnFilters={setColumnFilters}/>

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
