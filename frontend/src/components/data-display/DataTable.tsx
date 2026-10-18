import type { ReactNode } from 'react';

export interface DataColumn<T> {
  key: string;
  header: string;
  render?: (row: T) => ReactNode;
  className?: string;
  headerClassName?: string;
  align?: 'left' | 'center' | 'right';
}

interface DataTableProps<T> {
  columns: DataColumn<T>[];
  rows: T[];
  getRowKey: (row: T) => string | number;
  emptyMessage?: string;
  caption?: string;
  onRowClick?: (row: T) => void;
  className?: string;
}

function DataTable<T extends Record<string, unknown>>({
  columns,
  rows,
  getRowKey,
  emptyMessage = 'No records to display.',
  caption,
  onRowClick,
  className = '',
}: DataTableProps<T>) {
  return (
    <div className={`data-table-wrapper ${className}`.trim()}>
      <table className="data-table">
        {caption && <caption className="data-table__caption">{caption}</caption>}

        <thead>
          <tr>
            {columns.map((column) => (
              <th
                key={column.key}
                scope="col"
                className={column.headerClassName}
                style={{ textAlign: column.align ?? 'left' }}
              >
                {column.header}
              </th>
            ))}
          </tr>
        </thead>

        <tbody>
          {rows.length === 0 ? (
            <tr>
              <td
                className="data-table__empty"
                colSpan={columns.length || 1}
              >
                {emptyMessage}
              </td>
            </tr>
          ) : (
            rows.map((row) => (
              <tr
                key={getRowKey(row)}
                className={onRowClick ? 'data-table__row--clickable' : ''}
                onClick={onRowClick ? () => onRowClick(row) : undefined}
              >
                {columns.map((column) => (
                  <td
                    key={column.key}
                    className={column.className}
                    style={{ textAlign: column.align ?? 'left' }}
                  >
                    {column.render
                      ? column.render(row)
                      : String(row[column.key] ?? '—')}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}

export default DataTable;