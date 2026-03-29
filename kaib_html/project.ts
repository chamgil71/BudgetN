export interface Project {
  id: string;
  name: string;
  project_name: string;
  code: string;
  department: string;
  division: string | null;
  account_type: string;
  field: string;
  sector: string;
  program: { code: string; name: string };
  unit_project: { code: string; name: string };
  detail_project: { code: string; name: string };
  status: string;
  support_type: string;
  implementing_agency: string;
  subsidy_rate: string | null;
  loan_rate: string | null;
  project_managers: {
    sub_project: string;
    managing_dept: string;
    implementing_agency: string;
    manager: string | null;
    phone: string | null;
  }[];
  budget: {
    "2025_settlement": number | null;
    "2026_original": number | null;
    "2026_supplementary": number | null;
    "2027_request": number | null;
    "2027_budget": number | null;
    change_amount: number | null;
    change_rate: number | null;
  };
  project_period: {
    start_year: number;
    end_year: number;
    duration: string;
    raw: string;
  };
  total_cost: {
    total: number | null;
    government: number | null;
    raw: string | null;
  };
  sub_projects: {
    name: string;
    budget_2024: number | null;
    budget_2025: number | null;
    budget_2026: number | null;
  }[];
  purpose: string;
  description: string;
  legal_basis: string;
  is_rnd: boolean;
  is_informatization: boolean;
  keywords: string[];
  page_start: number;
  page_end: number;
  kpi: any[];
  overview: Record<string, string>;
  budget_calculation: any[];
  effectiveness: string;
  execution_detail: {
    method: string | null;
    recipients: string | null;
    subsidy_rate_detail: string | null;
  };
  yearly_budgets: Record<string, number>;
  history: any[];
  ai_domains: string[];
}

export interface ProjectsData {
  projects: Project[];
}
