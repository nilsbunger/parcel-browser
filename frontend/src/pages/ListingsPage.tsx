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

export function ListingsPage() {
  const { data, error } = useSWR('/dj/api/listings', fetcher);
  const [columnVisibility, setColumnVisibility] = useState({});

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
              : ({ row }) => row.getValue(field.name),
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
  console.log(table.getRowModel());
  return (
    <>
      <h1>Hello world from pages/ListingsPage.tsx!</h1>
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
    </>
  );
}
