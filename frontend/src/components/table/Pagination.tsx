import { ChevronLeft, ChevronRight } from "lucide-react";

interface PaginationProps {
  currentPage: number;
  totalPages: number;
  rowsPerPage: number;
  totalRows: number;
  setCurrentPage: (page: number | ((p: number) => number)) => void;
  setRowsPerPage: (rows: number) => void;
}

export default function Pagination({
  currentPage,
  totalPages,
  rowsPerPage,
  totalRows,
  setCurrentPage,
  setRowsPerPage,
}: PaginationProps) {
  return (
    <div className="p-4 border-t border-border flex flex-wrap items-center justify-between gap-4 bg-muted/10 text-sm text-muted-foreground">
      <div className="flex items-center gap-2">
        <span>Rows per page</span>
        <select
          value={rowsPerPage}
          onChange={(e) => {
            setRowsPerPage(Number(e.target.value));
            setCurrentPage(1);
          }}
          className="border border-border rounded-md bg-background px-2 py-1 text-xs focus:ring-1 focus:ring-primary"
        >
          {[10, 25, 50, 100].map((num) => (
            <option key={num} value={num}>
              {num}
            </option>
          ))}
        </select>
        <span>
          Showing {totalRows > 0 ? (currentPage - 1) * rowsPerPage + 1 : 0} to{" "}
          {Math.min(currentPage * rowsPerPage, totalRows)} of {totalRows}
        </span>
      </div>

      <div className="flex items-center gap-1.5">
        <button
          onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
          disabled={currentPage === 1}
          aria-label="Previous Page"
          className="p-1.5 border border-border bg-background rounded-lg hover:bg-muted transition-colors disabled:opacity-40 disabled:pointer-events-none"
        >
          <ChevronLeft className="h-4 w-4" />
        </button>
        <span className="px-3 py-1 font-semibold text-foreground bg-muted rounded-md text-xs">
          Page {currentPage} of {totalPages || 1}
        </span>
        <button
          onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
          disabled={currentPage === totalPages || totalPages === 0}
          aria-label="Next Page"
          className="p-1.5 border border-border bg-background rounded-lg hover:bg-muted transition-colors disabled:opacity-40 disabled:pointer-events-none"
        >
          <ChevronRight className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}
