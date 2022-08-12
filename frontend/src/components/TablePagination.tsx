// A generic component that displays pagination for a given table.

import { Table } from '@tanstack/react-table';
import * as React from 'react';

type Props = {
  table: Table<any>;
  pageIndex: number;
  pageSize: number;
  setPageIndex: React.Dispatch<React.SetStateAction<number>>;
  setPageSize: React.Dispatch<React.SetStateAction<number>>;
};

function TablePagination({
  table,
  pageIndex,
  pageSize,
  setPageIndex,
  setPageSize,
}: Props) {
  return (
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
  );
}

export default TablePagination;
