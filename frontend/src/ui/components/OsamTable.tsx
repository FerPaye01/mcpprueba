import {
  useReactTable,
  getCoreRowModel,
  flexRender
} from '@tanstack/react-table';

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

  const table = useReactTable({
    data,
    columns: tableColumns,
    getCoreRowModel: getCoreRowModel()
  });

  return (
    <div className="w-full overflow-x-auto my-6 rounded-[2rem] border border-slate-200/60 shadow-xl shadow-slate-100 bg-white">
      <table className="min-w-full divide-y divide-slate-100">
        <thead className="bg-slate-50/70 select-none">
          {table.getHeaderGroups().map(headerGroup => (
            <tr key={headerGroup.id}>
              {headerGroup.headers.map(header => (
                <th
                  key={header.id}
                  className="px-6 py-5 text-left text-[10px] font-black uppercase text-osi-blue tracking-widest border-b border-slate-100 whitespace-nowrap"
                >
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
  );
}
