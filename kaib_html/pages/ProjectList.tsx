import { useState, useMemo } from "react";
import { Link } from "react-router-dom";
import { useProjects } from "@/hooks/useProjects";
import { Input } from "@/components/ui/input";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";
import {
  Pagination, PaginationContent, PaginationItem, PaginationLink,
  PaginationNext, PaginationPrevious, PaginationEllipsis,
} from "@/components/ui/pagination";
import { ArrowUpDown, Search } from "lucide-react";
import { Button } from "@/components/ui/button";

type SortKey = "code" | "project_name" | "department" | "account_type";
type SortDir = "asc" | "desc";

const PAGE_SIZE = 20;

export default function ProjectList() {
  const { data, isLoading, error } = useProjects();
  const [search, setSearch] = useState("");
  const [sortKey, setSortKey] = useState<SortKey>("code");
  const [sortDir, setSortDir] = useState<SortDir>("asc");
  const [page, setPage] = useState(1);

  const toggleSort = (key: SortKey) => {
    if (sortKey === key) setSortDir(d => (d === "asc" ? "desc" : "asc"));
    else { setSortKey(key); setSortDir("asc"); }
    setPage(1);
  };

  const filtered = useMemo(() => {
    if (!data) return [];
    const q = search.toLowerCase();
    return data.projects.filter(p =>
      p.code.toLowerCase().includes(q) ||
      p.project_name.toLowerCase().includes(q) ||
      p.department.toLowerCase().includes(q) ||
      p.account_type.toLowerCase().includes(q)
    );
  }, [data, search]);

  const sorted = useMemo(() => {
    return [...filtered].sort((a, b) => {
      const va = (a[sortKey] ?? "").toString();
      const vb = (b[sortKey] ?? "").toString();
      return sortDir === "asc" ? va.localeCompare(vb, "ko") : vb.localeCompare(va, "ko");
    });
  }, [filtered, sortKey, sortDir]);

  const totalPages = Math.ceil(sorted.length / PAGE_SIZE);
  const pageItems = sorted.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  const SortHeader = ({ label, field }: { label: string; field: SortKey }) => (
    <Button
      variant="ghost"
      size="sm"
      className="h-auto p-0 font-medium text-muted-foreground hover:text-foreground"
      onClick={() => toggleSort(field)}
    >
      {label}
      <ArrowUpDown className="ml-1 h-3 w-3" />
    </Button>
  );

  const renderPageNumbers = () => {
    const items: React.ReactNode[] = [];
    const maxVisible = 5;
    let start = Math.max(1, page - Math.floor(maxVisible / 2));
    let end = Math.min(totalPages, start + maxVisible - 1);
    if (end - start < maxVisible - 1) start = Math.max(1, end - maxVisible + 1);

    if (start > 1) {
      items.push(
        <PaginationItem key={1}><PaginationLink onClick={() => setPage(1)}>1</PaginationLink></PaginationItem>
      );
      if (start > 2) items.push(<PaginationItem key="e1"><PaginationEllipsis /></PaginationItem>);
    }
    for (let i = start; i <= end; i++) {
      items.push(
        <PaginationItem key={i}>
          <PaginationLink isActive={i === page} onClick={() => setPage(i)}>{i}</PaginationLink>
        </PaginationItem>
      );
    }
    if (end < totalPages) {
      if (end < totalPages - 1) items.push(<PaginationItem key="e2"><PaginationEllipsis /></PaginationItem>);
      items.push(
        <PaginationItem key={totalPages}>
          <PaginationLink onClick={() => setPage(totalPages)}>{totalPages}</PaginationLink>
        </PaginationItem>
      );
    }
    return items;
  };

  if (isLoading) return <div className="flex items-center justify-center min-h-screen text-muted-foreground">로딩 중...</div>;
  if (error) return <div className="flex items-center justify-center min-h-screen text-destructive">데이터 로딩 실패</div>;

  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-7xl mx-auto px-4 py-8">
        <h1 className="text-2xl font-bold text-foreground mb-1">정부 R&D 사업 목록</h1>
        <p className="text-sm text-muted-foreground mb-6">
          총 {data?.projects.length ?? 0}개 사업 | 검색결과 {filtered.length}개
        </p>

        <div className="relative mb-4">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="사업코드, 사업명, 부처, 회계 검색..."
            value={search}
            onChange={e => { setSearch(e.target.value); setPage(1); }}
            className="pl-10"
          />
        </div>

        <div className="border rounded-lg overflow-hidden">
          <Table>
            <TableHeader>
              <TableRow className="bg-muted/50">
                <TableHead className="w-[120px]"><SortHeader label="사업코드" field="code" /></TableHead>
                <TableHead><SortHeader label="사업명" field="project_name" /></TableHead>
                <TableHead className="w-[160px]"><SortHeader label="부처" field="department" /></TableHead>
                <TableHead className="w-[100px]"><SortHeader label="회계" field="account_type" /></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {pageItems.map(p => (
                <TableRow key={p.id} className="hover:bg-muted/30 cursor-pointer">
                  <TableCell className="font-mono text-sm">{p.code}</TableCell>
                  <TableCell>
                    <Link
                      to={`/project/${encodeURIComponent(p.id)}`}
                      className="text-primary hover:underline font-medium"
                    >
                      {p.project_name}
                    </Link>
                  </TableCell>
                  <TableCell className="text-sm">{p.department}</TableCell>
                  <TableCell className="text-sm">{p.account_type}</TableCell>
                </TableRow>
              ))}
              {pageItems.length === 0 && (
                <TableRow>
                  <TableCell colSpan={4} className="text-center text-muted-foreground py-12">
                    검색 결과가 없습니다
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </div>

        {totalPages > 1 && (
          <div className="mt-4">
            <Pagination>
              <PaginationContent>
                <PaginationItem>
                  <PaginationPrevious
                    onClick={() => setPage(p => Math.max(1, p - 1))}
                    className={page === 1 ? "pointer-events-none opacity-50" : "cursor-pointer"}
                  />
                </PaginationItem>
                {renderPageNumbers()}
                <PaginationItem>
                  <PaginationNext
                    onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                    className={page === totalPages ? "pointer-events-none opacity-50" : "cursor-pointer"}
                  />
                </PaginationItem>
              </PaginationContent>
            </Pagination>
          </div>
        )}
      </div>
    </div>
  );
}
