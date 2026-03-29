import { useParams, Link } from "react-router-dom";
import { useProjects } from "@/hooks/useProjects";
import { ArrowLeft, Printer } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

function fmt(v: number | null | undefined): string {
  if (v == null) return "-";
  return v.toLocaleString("ko-KR");
}

function InfoRow({ label, value, full = false }: { label: string; value: React.ReactNode; full?: boolean }) {
  return (
    <div className={`flex border-b border-border ${full ? "col-span-2" : ""}`}>
      <div className="w-[140px] min-w-[140px] bg-muted/50 px-3 py-2 text-sm font-medium text-muted-foreground border-r border-border shrink-0 print:w-[120px]">
        {label}
      </div>
      <div className="flex-1 px-3 py-2 text-sm text-foreground whitespace-pre-wrap break-words">
        {value ?? "-"}
      </div>
    </div>
  );
}

export default function ProjectDetail() {
  const { id } = useParams<{ id: string }>();
  const { data, isLoading } = useProjects();

  if (isLoading) return <div className="flex items-center justify-center min-h-screen text-muted-foreground">로딩 중...</div>;

  const project = data?.projects.find(p => p.id === id);
  if (!project) return (
    <div className="flex flex-col items-center justify-center min-h-screen gap-4">
      <p className="text-muted-foreground">사업을 찾을 수 없습니다</p>
      <Link to="/"><Button variant="outline">목록으로</Button></Link>
    </div>
  );

  const p = project;

  return (
    <div className="min-h-screen bg-background print:bg-white">
      <div className="max-w-4xl mx-auto px-4 py-6 print:px-0 print:py-2">
        {/* Header */}
        <div className="flex items-center justify-between mb-4 print:hidden">
          <Link to="/">
            <Button variant="ghost" size="sm"><ArrowLeft className="mr-1 h-4 w-4" />목록</Button>
          </Link>
          <Button variant="outline" size="sm" onClick={() => window.print()}>
            <Printer className="mr-1 h-4 w-4" />인쇄
          </Button>
        </div>

        {/* Title */}
        <h1 className="text-xl font-bold text-foreground mb-1 print:text-lg">
          {p.project_name} ({p.code})
        </h1>
        <div className="flex gap-2 mb-6 flex-wrap print:mb-3">
          <Badge variant="secondary">{p.department}</Badge>
          <Badge variant="outline">{p.status}</Badge>
          {p.is_rnd && <Badge className="bg-primary text-primary-foreground">R&D</Badge>}
          {p.keywords.map(k => <Badge key={k} variant="outline" className="text-xs">{k}</Badge>)}
        </div>

        {/* 기본정보 */}
        <section className="border rounded-lg overflow-hidden mb-6 print:mb-3">
          <div className="bg-primary text-primary-foreground px-3 py-2 text-sm font-semibold">기본 정보</div>
          <div className="grid grid-cols-2 print:grid-cols-2">
            <InfoRow label="사업코드" value={p.code} />
            <InfoRow label="사업상태" value={p.status} />
            <InfoRow label="부처" value={p.department} />
            <InfoRow label="과" value={p.division ?? "-"} />
            <InfoRow label="회계유형" value={p.account_type} />
            <InfoRow label="지원유형" value={p.support_type} />
            <InfoRow label="분야" value={p.field} />
            <InfoRow label="부문" value={p.sector} />
            <InfoRow label="시행기관" value={p.implementing_agency} full />
          </div>
        </section>

        {/* 프로그램/단위/세부 */}
        <section className="border rounded-lg overflow-hidden mb-6 print:mb-3">
          <div className="bg-primary text-primary-foreground px-3 py-2 text-sm font-semibold">프로그램 구조</div>
          <div className="grid grid-cols-2">
            <InfoRow label="프로그램" value={`${p.program.name} (${p.program.code})`} full />
            <InfoRow label="단위사업" value={`${p.unit_project.name} (${p.unit_project.code})`} full />
            <InfoRow label="세부사업" value={`${p.detail_project.name} (${p.detail_project.code})`} full />
          </div>
        </section>

        {/* 사업기간/총사업비 */}
        <section className="border rounded-lg overflow-hidden mb-6 print:mb-3">
          <div className="bg-primary text-primary-foreground px-3 py-2 text-sm font-semibold">사업 기간 및 총사업비</div>
          <div className="grid grid-cols-2">
            <InfoRow label="사업기간" value={`${p.project_period.start_year}~${p.project_period.end_year} (${p.project_period.duration})`} />
            <InfoRow label="원문" value={p.project_period.raw} />
            <InfoRow label="총사업비" value={p.total_cost.total != null ? `${fmt(p.total_cost.total)}백만원` : "-"} />
            <InfoRow label="국비" value={p.total_cost.government != null ? `${fmt(p.total_cost.government)}백만원` : "-"} />
          </div>
        </section>

        {/* 예산 */}
        <section className="border rounded-lg overflow-hidden mb-6 print:mb-3">
          <div className="bg-primary text-primary-foreground px-3 py-2 text-sm font-semibold">예산 (백만원)</div>
          <div className="grid grid-cols-2">
            <InfoRow label="'25 결산" value={fmt(p.budget["2025_settlement"])} />
            <InfoRow label="'26 본예산" value={fmt(p.budget["2026_original"])} />
            <InfoRow label="'26 추경" value={fmt(p.budget["2026_supplementary"])} />
            <InfoRow label="'27 요구" value={fmt(p.budget["2027_request"])} />
            <InfoRow label="'27 편성" value={fmt(p.budget["2027_budget"])} />
            <InfoRow label="증감" value={fmt(p.budget.change_amount)} />
          </div>
        </section>

        {/* 연도별 예산 */}
        {Object.keys(p.yearly_budgets).length > 0 && (
          <section className="border rounded-lg overflow-hidden mb-6 print:mb-3">
            <div className="bg-primary text-primary-foreground px-3 py-2 text-sm font-semibold">연도별 예산 (백만원)</div>
            <div className="grid grid-cols-2">
              {Object.entries(p.yearly_budgets).map(([year, amount]) => (
                <InfoRow key={year} label={`${year}년`} value={fmt(amount)} />
              ))}
            </div>
          </section>
        )}

        {/* 하위사업 */}
        {p.sub_projects.length > 0 && (
          <section className="border rounded-lg overflow-hidden mb-6 print:mb-3">
            <div className="bg-primary text-primary-foreground px-3 py-2 text-sm font-semibold">하위 사업</div>
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-muted/50 border-b border-border">
                  <th className="px-3 py-2 text-left font-medium text-muted-foreground">사업명</th>
                  <th className="px-3 py-2 text-right font-medium text-muted-foreground">2024</th>
                  <th className="px-3 py-2 text-right font-medium text-muted-foreground">2025</th>
                  <th className="px-3 py-2 text-right font-medium text-muted-foreground">2026</th>
                </tr>
              </thead>
              <tbody>
                {p.sub_projects.map((sp, i) => (
                  <tr key={i} className="border-b border-border">
                    <td className="px-3 py-2">{sp.name}</td>
                    <td className="px-3 py-2 text-right">{fmt(sp.budget_2024)}</td>
                    <td className="px-3 py-2 text-right">{fmt(sp.budget_2025)}</td>
                    <td className="px-3 py-2 text-right">{fmt(sp.budget_2026)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>
        )}

        {/* 담당자 */}
        {p.project_managers.length > 0 && (
          <section className="border rounded-lg overflow-hidden mb-6 print:mb-3">
            <div className="bg-primary text-primary-foreground px-3 py-2 text-sm font-semibold">담당자 정보</div>
            {p.project_managers.map((pm, i) => (
              <div key={i} className="grid grid-cols-2 border-b border-border last:border-0">
                <InfoRow label="세부사업" value={pm.sub_project} full />
                <InfoRow label="관리부서" value={pm.managing_dept} />
                <InfoRow label="시행기관" value={pm.implementing_agency} />
                <InfoRow label="담당자" value={pm.manager ?? "-"} />
                <InfoRow label="연락처" value={pm.phone ?? "-"} />
              </div>
            ))}
          </section>
        )}

        {/* 개요 */}
        {Object.keys(p.overview).length > 0 && (
          <section className="border rounded-lg overflow-hidden mb-6 print:mb-3">
            <div className="bg-primary text-primary-foreground px-3 py-2 text-sm font-semibold">사업 개요</div>
            <div className="grid grid-cols-1">
              {Object.entries(p.overview).map(([key, val]) => (
                <InfoRow key={key} label={key} value={val} full />
              ))}
            </div>
          </section>
        )}

        {/* 사업목적 */}
        <section className="border rounded-lg overflow-hidden mb-6 print:mb-3">
          <div className="bg-primary text-primary-foreground px-3 py-2 text-sm font-semibold">사업 목적 및 내용</div>
          <div className="grid grid-cols-1">
            <InfoRow label="사업목적" value={p.purpose} full />
          </div>
        </section>

        {/* 법적근거 */}
        {p.legal_basis && (
          <section className="border rounded-lg overflow-hidden mb-6 print:mb-3">
            <div className="bg-primary text-primary-foreground px-3 py-2 text-sm font-semibold">법적 근거</div>
            <div className="px-3 py-2 text-sm whitespace-pre-wrap">{p.legal_basis}</div>
          </section>
        )}

        {/* 성과 */}
        {p.effectiveness && (
          <section className="border rounded-lg overflow-hidden mb-6 print:mb-3">
            <div className="bg-primary text-primary-foreground px-3 py-2 text-sm font-semibold">성과 및 기대효과</div>
            <div className="px-3 py-2 text-sm whitespace-pre-wrap">{p.effectiveness}</div>
          </section>
        )}

        {/* AI 도메인 */}
        {p.ai_domains.length > 0 && (
          <section className="border rounded-lg overflow-hidden mb-6 print:mb-3">
            <div className="bg-primary text-primary-foreground px-3 py-2 text-sm font-semibold">AI 관련 분야</div>
            <div className="px-3 py-2 flex gap-2 flex-wrap">
              {p.ai_domains.map(d => <Badge key={d} variant="secondary">{d}</Badge>)}
            </div>
          </section>
        )}

        {/* 페이지 참조 */}
        <div className="text-xs text-muted-foreground text-right mt-4 print:mt-2">
          원문 페이지: {p.page_start}~{p.page_end}p
        </div>
      </div>
    </div>
  );
}
