import { useState } from 'react';
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  flexRender
} from '@tanstack/react-table';
import type { SortingState } from '@tanstack/react-table';
import { 
  ArrowUpDown, 
  ChevronUp, 
  ChevronDown, 
  ChevronLeft, 
  ChevronRight, 
  Search 
} from 'lucide-react';

interface OsamColumn {
  id: string;
  label: string;
  type: string;
  format: string;
}

interface OsamTableProps {
  columns: OsamColumn[];
  data: any[];
}

export function OsamTable({ columns, data }: OsamTableProps) {
  // Map our OSAM columns specification to TanStack columns
  const tableColumns = columns.map(col => ({
    accessorKey: col.id,
    header: col.label,
    cell: (info: any) => {
      const val = info.getValue();
      if (val === null || val === undefined) return '-';
      
      // Basic formatting based on columns specification format
      if (col.format && col.format.startsWith('number')) {
        const parts = col.format.split(':');
        const decimals = parseInt(parts[1] || '2', 10);
        return typeof val === 'number' 
          ? val.toLocaleString(undefined, { minimumFractionDigits: decimals, maximumFractionDigits: decimals }) 
          : val;
      }
      if (col.format && col.format.startsWith('currency')) {
        const parts = col.format.split(':');
        const currency = parts[1] || 'USD';
        const decimals = parseInt(parts[2] || '2', 10);
        return typeof val === 'number' 
          ? val.toLocaleString(undefined, { style: 'currency', currency, minimumFractionDigits: decimals }) 
          : val;
      }
      return String(val);
    }
  }));

  const [sorting, setSorting] = useState<SortingState>([]);
  const [globalFilter, setGlobalFilter] = useState('');

  const table = useReactTable({
    data,
    columns: tableColumns,
    state: {
      sorting,
      globalFilter
    },
    onSortingChange: setSorting,
    onGlobalFilterChange: setGlobalFilter,
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    getCoreRowModel: getCoreRowModel(),
    initialState: {
      pagination: {
        pageSize: 5
      }
    }
  });

  return (
    <div className="w-full flex flex-col gap-4 my-4 animate-in fade-in duration-300">
      
      {/* Buscador Global (Estilo Excel/Power BI) */}
      <div className="relative group max-w-xs self-start">
        <input
          type="text"
          value={globalFilter ?? ''}
          onChange={e => setGlobalFilter(e.target.value)}
          placeholder="Filtrar registros..."
          className="w-full bg-slate-50 border border-slate-200/80 focus:border-osi-blue/15 focus:bg-white rounded-xl pl-9 pr-4 py-2 text-xs font-bold text-slate-600 outline-none transition-all focus:ring-4 focus:ring-osi-blue/5"
        />
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-400 group-focus-within:text-osi-blue transition-colors" />
      </div>

      {/* Grid de Tabla */}
      <div className="w-full overflow-x-auto rounded-[2rem] border border-slate-200/60 shadow-xl shadow-slate-100 bg-white">
        <table className="min-w-full divide-y divide-slate-100">
          <thead className="bg-slate-50/70 select-none">
            {table.getHeaderGroups().map(headerGroup => (
              <tr key={headerGroup.id}>
                {headerGroup.headers.map(header => {
                  const isSortable = header.column.getCanSort();
                  const sortedState = header.column.getIsSorted();
                  
                  return (
                    <th
                      key={header.id}
                      onClick={header.column.getToggleSortingHandler()}
                      className={`px-6 py-5 text-left text-[10px] font-black uppercase text-osi-blue tracking-widest border-b border-slate-100 whitespace-nowrap ${
                        isSortable ? 'cursor-pointer select-none hover:bg-slate-100/50 transition-colors' : ''
                      }`}
                    >
                      <div className="flex items-center gap-1.5">
                        {header.isPlaceholder
                          ? null
                          : flexRender(
                              header.column.columnDef.header,
                              header.getContext()
                            )}
                        {isSortable && (
                          <span className="text-slate-400">
                            {sortedState === 'asc' ? (
                              <ChevronUp className="w-3.5 h-3.5 text-osi-blue" />
                            ) : sortedState === 'desc' ? (
                              <ChevronDown className="w-3.5 h-3.5 text-osi-blue" />
                            ) : (
                              <ArrowUpDown className="w-3 h-3 opacity-45 hover:opacity-100 transition-opacity" />
                            )}
                          </span>
                        )}
                      </div>
                    </th>
                  );
                })}
              </tr>
            ))}
          </thead>
          <tbody className="divide-y divide-slate-50">
            {table.getRowModel().rows.map(row => (
              <tr key={row.id} className="hover:bg-slate-50/30 transition-colors">
                {row.getVisibleCells().map(cell => (
                  <td
                    key={cell.id}
                    className="px-6 py-4.5 text-[13px] font-semibold text-slate-700 whitespace-nowrap"
                  >
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Controles de Paginación (Estilo Excel/Power BI) */}
      <div className="flex items-center justify-between px-4 py-1 select-none text-slate-500">
        
        {/* Selector de registros por página */}
        <div className="flex items-center gap-1.5 text-xs font-bold">
          <span>Mostrar</span>
          <select
            value={table.getState().pagination.pageSize}
            onChange={e => {
              table.setPageSize(Number(e.target.value));
            }}
            className="bg-white border border-slate-200 rounded-lg px-2 py-1 outline-none text-slate-700 font-black cursor-pointer hover:bg-slate-50/50 transition-colors"
          >
            {[5, 10, 20, 50].map(pageSize => (
              <option key={pageSize} value={pageSize}>
                {pageSize}
              </option>
            ))}
          </select>
          <span className="opacity-60">por página</span>
        </div>

        {/* Indicador de página y controles de avance */}
        <div className="flex items-center gap-4 text-xs font-bold">
          <span className="opacity-80">
            Página <strong className="text-slate-800 font-black">{table.getState().pagination.pageIndex + 1}</strong> de{' '}
            <strong className="text-slate-800 font-black">{table.getPageCount() || 1}</strong>
          </span>
          
          <div className="flex items-center gap-1">
            <button
              onClick={() => table.previousPage()}
              disabled={!table.getCanPreviousPage()}
              className="p-1.5 bg-slate-50 hover:bg-slate-100 text-slate-600 rounded-lg border border-slate-200/40 cursor-pointer active:scale-95 disabled:opacity-40 disabled:pointer-events-none transition-all"
              title="Página anterior"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <button
              onClick={() => table.nextPage()}
              disabled={!table.getCanNextPage()}
              className="p-1.5 bg-slate-50 hover:bg-slate-100 text-slate-600 rounded-lg border border-slate-200/40 cursor-pointer active:scale-95 disabled:opacity-40 disabled:pointer-events-none transition-all"
              title="Página siguiente"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>

      </div>

    </div>
  );
}
