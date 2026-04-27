import argparse
import json
import math
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime
from difflib import SequenceMatcher
from itertools import combinations
from pathlib import Path

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))
from config import path_config
from scripts.pipeline._years import get_years

Y = get_years()

parser = argparse.ArgumentParser()
parser.add_argument("--input", default=str(path_config.MERGED_JSON_PATH))
parser.add_argument("--outdir", default=str(path_config.OUTPUT_DIR))
args, _ = parser.parse_known_args()

DB_PATH = Path(args.input)
OUTDIR = Path(args.outdir)
OUTDIR.mkdir(parents=True, exist_ok=True)

SIM_OUT = OUTDIR / "similarity_analysis.json"
COL_OUT = OUTDIR / "collaboration_analysis.json"
HYB_OUT = OUTDIR / "hybrid_similarity.json"

PROFILE_CONFIG = {
    "rnd": {
        "title": "R&D 연구개발",
        "weights": {"F": 0.25, "C": 0.08, "D": 0.07, "E": 0.30, "S": 0.10},
        "keywords": ["r&d", "연구", "개발", "실증", "원천", "기술개발", "고도화"],
    },
    "training": {
        "title": "인력양성",
        "weights": {"F": 0.30, "C": 0.20, "D": 0.05, "E": 0.15, "S": 0.08},
        "keywords": ["인력", "양성", "교육", "훈련", "대학원", "학위", "인재"],
    },
    "defense": {
        "title": "국방/안보",
        "weights": {"F": 0.20, "C": 0.10, "D": 0.15, "E": 0.25, "S": 0.10},
        "keywords": ["국방", "안보", "방산", "군", "전투", "항공", "우주안보"],
    },
    "infra": {
        "title": "인프라/시스템",
        "weights": {"F": 0.25, "C": 0.10, "D": 0.10, "E": 0.25, "S": 0.10},
        "keywords": ["구축", "인프라", "플랫폼", "센터", "시스템", "운영", "서비스"],
    },
    "general": {
        "title": "일반행정/지원",
        "weights": {"F": 0.20, "C": 0.15, "D": 0.10, "E": 0.25, "S": 0.10},
        "keywords": ["운영", "지원", "정책", "행정", "기획", "평가"],
    },
    "manufacturing": {
        "title": "제조/산업",
        "weights": {"F": 0.25, "C": 0.10, "D": 0.10, "E": 0.25, "S": 0.10},
        "keywords": ["제조", "산업", "공정", "소부장", "스마트팩토리", "설비"],
    },
    "data_platform": {
        "title": "데이터/플랫폼",
        "weights": {"F": 0.25, "C": 0.10, "D": 0.05, "E": 0.30, "S": 0.10},
        "keywords": ["데이터", "db", "플랫폼", "연계", "표준", "상호운용"],
    },
    "medical_bio": {
        "title": "의료/바이오",
        "weights": {"F": 0.20, "C": 0.15, "D": 0.10, "E": 0.25, "S": 0.10},
        "keywords": ["의료", "바이오", "헬스", "건강", "세포", "치료제", "병원"],
    },
    "testbed": {
        "title": "실증/테스트베드",
        "weights": {"F": 0.25, "C": 0.10, "D": 0.10, "E": 0.25, "S": 0.10},
        "keywords": ["실증", "테스트베드", "시범", "검증", "pilot"],
    },
    "education": {
        "title": "교육",
        "weights": {"F": 0.25, "C": 0.15, "D": 0.05, "E": 0.25, "S": 0.10},
        "keywords": ["교육", "학교", "학생", "교원", "수업", "대학"],
    },
    "digital_transform": {
        "title": "디지털전환",
        "weights": {"F": 0.25, "C": 0.10, "D": 0.05, "E": 0.30, "S": 0.10},
        "keywords": ["디지털전환", "dx", "ax", "전환", "지능화", "자동화"],
    },
    "energy_env": {
        "title": "에너지/환경",
        "weights": {"F": 0.25, "C": 0.10, "D": 0.10, "E": 0.25, "S": 0.10},
        "keywords": ["에너지", "환경", "탄소", "기후", "전력", "수소"],
    },
}

STOPWORDS = {
    "및", "의", "을", "를", "이", "가", "에", "로", "으로", "와", "과", "은", "는",
    "한", "하는", "위한", "위해", "사업", "지원", "구축", "운영", "개발", "기반", "고도화",
}

COLLAB_PATTERNS = [
    ("인력양성→산업체 활용 연계", {"training"}, {"rnd", "manufacturing", "infra", "testbed"}),
    ("기술/인프라 공유", {"infra", "data_platform"}, {"rnd", "digital_transform", "manufacturing", "medical_bio"}),
    ("R&D→실증→사업화 가치사슬", {"rnd"}, {"testbed", "manufacturing", "infra"}),
    ("데이터 구축→활용 연계", {"data_platform"}, {"medical_bio", "digital_transform", "manufacturing", "general"}),
    ("정책→기술사업화 연계", {"general"}, {"rnd", "manufacturing", "digital_transform"}),
    ("기반기술→도메인 적용", {"digital_transform", "infra"}, {"medical_bio", "energy_env", "defense", "education"}),
]


def safe_float(v, default=0.0):
    try:
        if v is None or v == "":
            return default
        return float(str(v).replace(",", ""))
    except Exception:
        return default


def clean_text(v):
    if v is None:
        return ""
    return re.sub(r"\s+", " ", str(v)).strip()


def ensure_list(v):
    if v is None:
        return []
    if isinstance(v, list):
        return [clean_text(x) for x in v if clean_text(x)]
    if isinstance(v, str):
        return [x.strip() for x in re.split(r"[,/|·\n]+", v) if x.strip()]
    return [clean_text(v)]


def normalize_keyword_token(text):
    return re.sub(r"[^0-9a-zA-Z가-힣]+", "", text).lower()


def token_set(*parts):
    tokens = set()
    for part in parts:
        for item in ensure_list(part):
            for tok in re.findall(r"[0-9a-zA-Z가-힣]{2,}", item.lower()):
                if tok not in STOPWORDS:
                    tokens.add(tok)
    return tokens


def get_budget_fields(project):
    budget = project.get("budget") or {}
    return {
        "settlement": safe_float(budget.get(f"{Y['settlement']}_settlement")),
        "original": safe_float(budget.get(f"{Y['original']}_original")),
        "supplementary": safe_float(budget.get(f"{Y['supplementary']}_supplementary")),
        "request": safe_float(budget.get(f"{Y['request']}_request")),
        "base": safe_float(budget.get(f"{Y['budget']}_budget")) or safe_float(budget.get(f"{Y['budget']}_request")),
        "change_amount": safe_float(budget.get("change_amount")),
        "change_rate": budget.get("change_rate"),
    }


def get_year_series(project):
    yearly = project.get("yearly_budgets") or {}
    parsed = {}
    if isinstance(yearly, dict):
        parsed = {str(k): safe_float(v) for k, v in yearly.items() if safe_float(v, None) is not None}
    elif isinstance(yearly, list):
        for item in yearly:
            if isinstance(item, dict):
                year = item.get("year") or item.get("label") or item.get("name")
                value = item.get("budget") or item.get("amount") or item.get("value")
                if year is not None and value is not None:
                    parsed[str(year)] = safe_float(value)
    if not parsed:
        budgets = get_budget_fields(project)
        parsed = {
            str(Y["settlement"]): budgets["settlement"],
            str(Y["original"]): budgets["original"],
            str(Y["budget"]): budgets["base"],
        }
    return {k: v for k, v in parsed.items() if v is not None}


def infer_profile(project):
    name = " ".join([
        clean_text(project.get("project_name")),
        clean_text(project.get("purpose")),
        clean_text(project.get("description")),
        " ".join(ensure_list(project.get("ai_domains"))),
        " ".join(ensure_list(project.get("ai_tech_types"))),
        " ".join(ensure_list(project.get("rnd_stage"))),
    ]).lower()
    scores = Counter()

    if project.get("is_rnd"):
        scores["rnd"] += 3
    if project.get("is_informatization"):
        scores["infra"] += 3

    for profile, cfg in PROFILE_CONFIG.items():
        for kw in cfg["keywords"]:
            if kw in name:
                scores[profile] += 1

    domains = " ".join(ensure_list(project.get("ai_domains"))).lower()
    if "교육" in domains or "인재" in domains:
        scores["training"] += 2
    if "데이터" in domains:
        scores["data_platform"] += 2
    if "의료" in domains or "바이오" in domains:
        scores["medical_bio"] += 2
    if "로봇" in domains or "제조" in domains:
        scores["manufacturing"] += 2

    if not scores:
        scores["general"] = 1
    return scores.most_common(1)[0][0]


def infer_type_codes(project, profile):
    codes = []
    if project.get("is_rnd"):
        codes.append("T02")
    if project.get("is_informatization"):
        codes.append("T03")
    if profile == "training":
        codes.append("T04")
    if profile == "data_platform":
        codes.append("T07")
    if profile == "general":
        codes.append("T08")
    if profile == "testbed":
        codes.append("T10")
    if profile == "education":
        codes.append("T11")
    if not codes:
        codes.append("T98")
    return sorted(set(codes))


def infer_beneficiaries(project, profile):
    text = " ".join([
        clean_text(project.get("project_name")),
        clean_text(project.get("purpose")),
        clean_text(project.get("description")),
        clean_text((project.get("execution_detail") or {}).get("recipients")),
    ])
    beneficiaries = set()
    keyword_map = {
        "B01": ["학생", "대학원", "교원", "인재"],
        "B02": ["기업", "중소", "스타트업", "산업체"],
        "B03": ["지자체", "공공", "기관"],
        "B04": ["농업", "농가"],
        "B05": ["환자", "병원", "의료인"],
        "B08": ["국민", "전체", "사회", "서비스"],
    }
    for code, kws in keyword_map.items():
        if any(kw in text for kw in kws):
            beneficiaries.add(code)
    if not beneficiaries:
        beneficiaries.add("B08")
    if profile == "training":
        beneficiaries.add("B01")
    return sorted(beneficiaries)


def infer_agency_code(project):
    text = " ".join([
        clean_text(project.get("implementing_agency")),
        clean_text(project.get("department")),
        clean_text(project.get("division")),
    ])
    if any(k in text for k in ["대학", "학교", "교육원"]):
        return "A01"
    if any(k in text for k in ["연구원", "연구기관", "출연연"]):
        return "A02"
    if any(k in text for k in ["기업", "협회", "센터", "조합"]):
        return "A03"
    if any(k in text for k in ["부", "청", "공단", "공사", "재단", "공공"]):
        return "A04"
    return "A99"


def extract_period(project):
    raw = clean_text((project.get("project_period") or {}).get("raw"))
    start = (project.get("project_period") or {}).get("start_year")
    end = (project.get("project_period") or {}).get("end_year")
    try:
        start = int(start) if start not in (None, "") else None
    except Exception:
        start = None
    try:
        end = int(end) if end not in (None, "") else None
    except Exception:
        end = None
    years = [int(x) for x in re.findall(r"(20\d{2})", raw)]
    if not start and years:
        start = years[0]
    if not end and len(years) > 1:
        end = years[-1]
    return start, end, raw


def hhi_from_subs(subs, base_key):
    values = [max(0.0, safe_float(s.get(base_key))) for s in subs]
    total = sum(values)
    if total <= 0:
        return 1.0 if values else 0.0
    shares = [v / total for v in values if v > 0]
    return sum(s * s for s in shares)


def best_string_similarity(a, b):
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, normalize_keyword_token(a), normalize_keyword_token(b)).ratio()


def build_tfidf_similarity(texts, analyzer="char_wb", ngram_range=(2, 4)):
    if not HAS_SKLEARN:
        return None
    try:
        vec = TfidfVectorizer(analyzer=analyzer, ngram_range=ngram_range, min_df=1)
        mat = vec.fit_transform([t if t else " " for t in texts])
        return cosine_similarity(mat)
    except Exception:
        return None


def normalize_projects(projects):
    normalized = []
    for idx, project in enumerate(projects):
        budget_fields = get_budget_fields(project)
        profile = infer_profile(project)
        sub_projects = ensure_list(project.get("sub_projects"))
        actual_subs = project.get("sub_projects") or []
        sub_names = [clean_text(x.get("name")) for x in actual_subs if isinstance(x, dict)]
        kpis = [clean_text(k.get("name") or k.get("description") or k) for k in (project.get("kpi") or [])]
        domains = ensure_list(project.get("ai_domains")) or [clean_text(project.get("field")) or clean_text(project.get("sector"))]
        domains = [d for d in domains if d]
        primary_domain = domains[0] if domains else "기타"
        beneficiaries = infer_beneficiaries(project, profile)
        agency_code = infer_agency_code(project)
        start_year, end_year, period_raw = extract_period(project)
        year_series = get_year_series(project)
        sub_base_key = f"budget_{Y['budget']}"
        text_domain = " ".join(filter(None, [
            clean_text(project.get("project_name")),
            clean_text(project.get("purpose")),
            clean_text(project.get("description")),
            clean_text(project.get("legal_basis")),
            clean_text(project.get("effectiveness")),
            " ".join(domains),
            " ".join(ensure_list(project.get("ai_tech_types"))),
        ]))
        text_structure = " ".join(filter(None, sub_names + kpis + [
            clean_text((project.get("unit_project") or {}).get("name")),
            clean_text((project.get("detail_project") or {}).get("name")),
        ]))
        merged_tokens = token_set(
            project.get("project_name"),
            project.get("purpose"),
            project.get("description"),
            project.get("legal_basis"),
            domains,
            project.get("ai_tech_types"),
            project.get("rnd_stage"),
            project.get("keywords"),
            sub_names,
            kpis,
        )
        normalized.append({
            "idx": idx,
            "raw": project,
            "id": project.get("id"),
            "project_name": clean_text(project.get("project_name")),
            "department": clean_text(project.get("department")) or "미상 부처",
            "division": clean_text(project.get("division")),
            "implementing_agency": clean_text(project.get("implementing_agency")),
            "primary_domain": primary_domain,
            "domains": domains,
            "profile": profile,
            "types": infer_type_codes(project, profile),
            "beneficiaries": beneficiaries,
            "agency_code": agency_code,
            "base_budget": budget_fields["base"],
            "change_rate": safe_float(budget_fields["change_rate"], None) if budget_fields["change_rate"] is not None else None,
            "budget_fields": budget_fields,
            "year_series": year_series,
            "sub_projects": actual_subs,
            "sub_names": sub_names,
            "sub_hhi": hhi_from_subs(actual_subs, sub_base_key),
            "sub_count": len(actual_subs),
            "kpis": [k for k in kpis if k],
            "keywords": sorted(merged_tokens),
            "token_set": merged_tokens,
            "text_domain": text_domain,
            "text_structure": text_structure,
            "period_raw": period_raw,
            "start_year": start_year,
            "end_year": end_year,
            "effectiveness": clean_text(project.get("effectiveness")),
            "sub_project_name": sub_names[0] if sub_names else clean_text((project.get("detail_project") or {}).get("name")),
        })
    return normalized


def overlap_coeff(a, b):
    sa, sb = set(a), set(b)
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / max(1, min(len(sa), len(sb)))


def jaccard(a, b):
    sa, sb = set(a), set(b)
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def agency_similarity(a_code, b_code):
    if a_code == "A99" or b_code == "A99":
        return 1.0
    if a_code == b_code:
        return 1.0
    close = {("A01", "A02"), ("A02", "A01"), ("A03", "A04"), ("A04", "A03")}
    return 0.5 if (a_code, b_code) in close else 0.2


def budget_scale_similarity(a_budget, b_budget):
    if a_budget <= 0 or b_budget <= 0:
        return 0.3
    ratio = min(a_budget, b_budget) / max(a_budget, b_budget)
    return max(0.2, ratio)


def trend_score(a_series, b_series):
    keys = sorted(set(a_series.keys()) | set(b_series.keys()))
    if len(keys) < 2:
        return 0.5, {"note": "insufficient history"}
    av = [safe_float(a_series.get(k)) for k in keys]
    bv = [safe_float(b_series.get(k)) for k in keys]
    if max(av) == 0 or max(bv) == 0:
        return 0.5, {"note": "new project detected - neutral score applied"}
    achg = (av[-1] - av[0]) / max(abs(av[0]), 1.0)
    bchg = (bv[-1] - bv[0]) / max(abs(bv[0]), 1.0)
    diff = abs(achg - bchg)
    score = max(0.0, 1.0 - min(1.0, diff))
    return score, {
        "a_series": av,
        "b_series": bv,
        "a_trend": round(achg, 3),
        "b_trend": round(bchg, 3),
        "a_years": len([x for x in av if x > 0]),
        "b_years": len([x for x in bv if x > 0]),
    }


def sub_project_similarity(a, b):
    names_a = a["sub_names"]
    names_b = b["sub_names"]
    if not names_a and not names_b:
        return 0.0, {
            "name_overlap": 0.0,
            "hhi_a": 0.0,
            "hhi_b": 0.0,
            "concentration_sim": 0.0,
            "count_a": 0,
            "count_b": 0,
            "count_ratio": 0.0,
            "matching_subs": [],
        }
    matches = []
    best_sum = 0.0
    for sa in names_a[:8]:
        best = 0.0
        best_name = None
        for sb in names_b[:8]:
            sim = best_string_similarity(sa, sb)
            if sim > best:
                best = sim
                best_name = sb
        if best_name and best >= 0.45:
            matches.append({"a_name": sa, "b_name": best_name, "name_sim": round(best, 2)})
        best_sum += best
    denom = max(1, min(len(names_a), len(names_b), 8))
    name_overlap = best_sum / denom if denom else 0.0
    concentration_sim = max(0.0, 1.0 - abs(a["sub_hhi"] - b["sub_hhi"]))
    count_ratio = min(max(a["sub_count"], 1), max(b["sub_count"], 1)) / max(max(a["sub_count"], 1), max(b["sub_count"], 1))
    score = 0.45 * name_overlap + 0.35 * concentration_sim + 0.20 * count_ratio
    return score, {
        "name_overlap": round(name_overlap, 2),
        "hhi_a": round(a["sub_hhi"], 3),
        "hhi_b": round(b["sub_hhi"], 3),
        "concentration_sim": round(concentration_sim, 2),
        "count_a": a["sub_count"],
        "count_b": b["sub_count"],
        "count_ratio": round(count_ratio, 2),
        "matching_subs": matches[:5],
    }


def kpi_similarity(a, b):
    if not a["kpis"] and not b["kpis"]:
        return 0.0
    score = jaccard(token_set(a["kpis"]), token_set(b["kpis"]))
    return round(score, 2)


def period_similarity(a, b):
    if a["start_year"] and a["end_year"] and b["start_year"] and b["end_year"]:
        start = max(a["start_year"], b["start_year"])
        end = min(a["end_year"], b["end_year"])
        union_start = min(a["start_year"], b["start_year"])
        union_end = max(a["end_year"], b["end_year"])
        overlap = max(0, end - start + 1)
        union = max(1, union_end - union_start + 1)
        return round(overlap / union, 2)
    raw_score = best_string_similarity(a["period_raw"], b["period_raw"])
    return round(raw_score, 2)


def type_gate(a, b):
    if set(a["types"]) & set(b["types"]):
        return 1.0
    if a["profile"] == b["profile"]:
        return 0.85
    return 0.0


def similarity_level(score):
    if score >= 9:
        return "매우높음(Very High)"
    if score >= 7:
        return "높음(High)"
    if score >= 5:
        return "중간(Medium)"
    return "낮음(Low)"


def format_project_node(item):
    return {
        "id": item["id"],
        "project_name": item["project_name"],
        "sub_project_name": item["sub_project_name"],
        "department": item["department"],
        "division": item["division"],
        "budget_2026": round(item["base_budget"], 1),
        "change_rate": item["change_rate"],
        "types": item["types"],
        "fields": item["domains"],
    }


def generate_similarity_rationale(a, b, analysis, total_score):
    combined_budget = a["base_budget"] + b["base_budget"]
    return (
        f"A사업은 {', '.join(a['types'])}, B사업은 {', '.join(b['types'])} 성격을 가져 유사 프로필로 분류된다. "
        f"분야 유사도(F={analysis['field_similarity']['score']:.2f}), 수혜대상 유사도(C={analysis['beneficiary_similarity']['score']:.2f}), "
        f"텍스트 유사도(E={analysis['text_similarity']['score']:.2f})가 높다. "
        f"양 사업의 {Y['budget']}년 예산은 각각 {a['base_budget']:,.0f}백만원, {b['base_budget']:,.0f}백만원이며 합계는 {combined_budget:,.0f}백만원이다. "
        f"내역사업 구조 및 사업기간이 유사하여 중복 투자 가능성이 있다. "
        f"결과적으로 {a['department']}의 '{a['project_name']}'과(와) {b['department']}의 '{b['project_name']}'은(는) "
        f"유사/중복 가능성이 높은 사업으로 판단된다(유사도 {total_score:.1f}점)."
    )


def generate_similarity_recommendation(a, b):
    combined_budget = a["base_budget"] + b["base_budget"]
    savings = combined_budget * 0.15
    return (
        f"{a['project_name']}과 {b['project_name']}은 역할 분담과 범위 경계를 명확히 재설계해야 한다. "
        f"총 {combined_budget:,.0f}백만원 규모에서 약 {savings:,.0f}백만원 수준의 중복 절감 여지가 있어 "
        f"공동 기획, 통합 KPI 관리, 중복 내역사업 정비를 우선 검토할 필요가 있다."
    )


def determine_collaboration_type(a, b):
    pa, pb = a["profile"], b["profile"]
    for label, sources, targets in COLLAB_PATTERNS:
        if pa in sources and pb in targets:
            return label, "A_to_B"
        if pb in sources and pa in targets:
            return label, "B_to_A"
    if a["primary_domain"] == b["primary_domain"]:
        return "기술/인프라 공유", "A_to_B"
    return None, None


def collaboration_components(a, b, domain_sim, structure_sim, text_sim):
    collab_type, direction = determine_collaboration_type(a, b)
    if not collab_type:
        return None
    linkage_clarity = 1.5
    if a["profile"] != b["profile"]:
        linkage_clarity += 1.0
    if structure_sim >= 0.25:
        linkage_clarity += 0.5
    domain_match = min(2.0, 1.0 + domain_sim)
    synergy_size = min(3.0, math.log10(max(a["base_budget"] + b["base_budget"], 1.0) + 1) * 0.9)
    irreplaceability = 1.0
    if text_sim < 0.55 and domain_sim >= 0.5:
        irreplaceability += 0.5
    if a["department"] != b["department"]:
        irreplaceability += 0.3
    total = min(10.0, linkage_clarity + domain_match + synergy_size + irreplaceability)
    return {
        "collaboration_type": collab_type,
        "direction": direction,
        "linkage_clarity": round(min(3.0, linkage_clarity), 2),
        "domain_match": round(domain_match, 2),
        "synergy_size": round(synergy_size, 2),
        "irreplaceability": round(min(2.0, irreplaceability), 2),
        "score": round(total, 1),
    }


def collaboration_rationale(a, b, collab):
    direction = " → ".join([a["department"], b["department"]]) if collab["direction"] == "A_to_B" else " → ".join([b["department"], a["department"]])
    return (
        f"{collab['collaboration_type']} 유형으로 {direction} 연계가 성립한다. "
        f"도메인 적합도 {collab['domain_match']}, 연계 명확성 {collab['linkage_clarity']}, 시너지 규모 {collab['synergy_size']} 수준으로 "
        f"협업 시 정책-기술 연동 효과가 높다."
    )


def collaboration_recommendation(a, b, collab):
    return (
        f"{a['department']}와 {b['department']}는 '{collab['collaboration_type']}' 기준 공동 과제 기획과 데이터/성과 공유 체계를 구축해야 한다. "
        f"협업 KPI와 공급-수요 역할 정의를 함께 두는 것이 우선순위다."
    )


def build_union_find(items):
    parent = {i: i for i in items}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    return parent, find, union


def build_similarity_outputs(projects):
    normalized = normalize_projects(projects)
    domain_matrix = build_tfidf_similarity([p["text_domain"] for p in normalized])
    structure_matrix = build_tfidf_similarity([p["text_structure"] for p in normalized], ngram_range=(2, 5))

    sim_pairs = []
    collab_pairs = []
    profile_pairs = defaultdict(list)

    for i, j in combinations(range(len(normalized)), 2):
        a = normalized[i]
        b = normalized[j]
        if not a["project_name"] or not b["project_name"]:
            continue
        if a["id"] == b["id"]:
            continue

        field_sim = overlap_coeff(a["domains"], b["domains"])
        beneficiary_sim = jaccard(a["beneficiaries"], b["beneficiaries"])
        token_sim = jaccard(a["token_set"], b["token_set"])
        domain_tfidf = float(domain_matrix[i, j]) if domain_matrix is not None else token_sim
        structure_tfidf = float(structure_matrix[i, j]) if structure_matrix is not None else 0.0
        text_sim = domain_tfidf * 0.4 + structure_tfidf * 0.6
        sub_score, sub_detail = sub_project_similarity(a, b)
        gate = type_gate(a, b)

        if gate <= 0 and field_sim < 0.5 and token_sim < 0.25 and text_sim < 0.30:
            continue

        dominant_profile = a["profile"] if a["profile"] == b["profile"] else ("training" if "training" in {a["profile"], b["profile"]} else a["profile"])
        weights = PROFILE_CONFIG.get(dominant_profile, PROFILE_CONFIG["general"])["weights"]
        agency_sim = agency_similarity(a["agency_code"], b["agency_code"])
        base_raw = (
            field_sim * weights["F"]
            + beneficiary_sim * weights["C"]
            + agency_sim * weights["D"]
            + text_sim * weights["E"]
            + sub_score * weights["S"]
        )
        if a["primary_domain"] == b["primary_domain"] and a["primary_domain"] != "기타":
            base_raw *= 1.18
        bonus = max(0.0, (text_sim - 0.8) * 12.0)
        score = min(10.0, base_raw * max(0.7, gate) * 10.0 + bonus)

        budget_scale = budget_scale_similarity(a["base_budget"], b["base_budget"])
        trend, trend_detail = trend_score(a["year_series"], b["year_series"])
        kpi_score = kpi_similarity(a, b)
        period_score = period_similarity(a, b)

        if score >= 5.0:
            analysis = {
                "type_gate": round(gate, 2),
                "field_similarity": {"score": round(field_sim, 2), "a_fields": a["domains"], "b_fields": b["domains"]},
                "beneficiary_similarity": {"score": round(beneficiary_sim, 2), "a_beneficiaries": a["beneficiaries"], "b_beneficiaries": b["beneficiaries"]},
                "agency_similarity": {"score": round(agency_sim, 2), "a_agency": a["agency_code"], "b_agency": b["agency_code"]},
                "text_similarity": {"score": round(text_sim, 2), "domain_tfidf": round(domain_tfidf, 2), "structure_tfidf": round(structure_tfidf, 2), "text_bonus": round(bonus, 2)},
                "budget_analysis": {
                    "scale_score": round(budget_scale, 2),
                    "a_budget": round(a["base_budget"], 1),
                    "b_budget": round(b["base_budget"], 1),
                    "a_change_rate": a["change_rate"],
                    "b_change_rate": b["change_rate"],
                    "trend_score": round(trend, 2),
                    "trend_detail": trend_detail,
                },
                "sub_project_analysis": {"score": round(sub_score, 2), "detail": sub_detail},
                "kpi_analysis": {"score": round(kpi_score, 2), "a_kpis": a["kpis"][:5], "b_kpis": b["kpis"][:5]},
                "period_analysis": {"score": round(period_score, 2), "a_period": a["period_raw"], "b_period": b["period_raw"]},
                "a_effectiveness": a["effectiveness"][:1200],
                "b_effectiveness": b["effectiveness"][:1200],
                "a_yearly_budgets": a["year_series"],
                "b_yearly_budgets": b["year_series"],
            }
            pair = {
                "pair_id": f"PAIR-{len(sim_pairs)+1:06d}",
                "similarity_score": round(score, 1),
                "similarity_level": similarity_level(score),
                "project_a": format_project_node(a),
                "project_b": format_project_node(b),
                "analysis": analysis,
                "rationale": generate_similarity_rationale(a, b, analysis, score),
                "recommendation": generate_similarity_recommendation(a, b),
            }
            sim_pairs.append(pair)
            profile_pairs[dominant_profile].append(pair)

        collab = collaboration_components(a, b, field_sim, sub_score, text_sim)
        if collab and a["department"] != b["department"] and collab["score"] >= 5.0:
            collab_pairs.append({
                "pair_id": f"COL-{len(collab_pairs)+1:06d}",
                "collaboration_score": collab["score"],
                "collaboration_level": "반드시 협업 필요" if collab["score"] >= 8 else "협업 권장",
                "collaboration_type": collab["collaboration_type"],
                "project_a": format_project_node(a),
                "project_b": format_project_node(b),
                "analysis": collab,
                "rationale": collaboration_rationale(a, b, collab),
                "recommendation": collaboration_recommendation(a, b, collab),
            })

    sim_pairs.sort(key=lambda x: x["similarity_score"], reverse=True)
    collab_pairs.sort(key=lambda x: x["collaboration_score"], reverse=True)
    return normalized, sim_pairs[:1200], collab_pairs[:800], profile_pairs


def build_clusters(sim_pairs):
    ids = set()
    for p in sim_pairs:
        ids.add(p["project_a"]["id"])
        ids.add(p["project_b"]["id"])
    parent, find, union = build_union_find(ids)
    for p in sim_pairs:
        if p["similarity_score"] >= 7.2:
            union(p["project_a"]["id"], p["project_b"]["id"])
    grouped = defaultdict(list)
    for pid in ids:
        grouped[find(pid)].append(pid)
    return [sorted(v) for v in grouped.values() if len(v) > 1]


def make_cluster_records(cluster_ids, sim_pairs, normalized):
    project_map = {p["id"]: p for p in normalized}
    pair_lookup = defaultdict(list)
    for pair in sim_pairs:
        key = tuple(sorted([pair["project_a"]["id"], pair["project_b"]["id"]]))
        pair_lookup[key].append(pair)

    records = []
    duplicate_groups = []
    for idx, ids in enumerate(cluster_ids, 1):
        members = [project_map[i] for i in ids if i in project_map]
        if not members:
            continue
        kw_counter = Counter()
        total_budget = 0.0
        for m in members:
            kw_counter.update(m["keywords"][:8])
            total_budget += m["base_budget"]
        top_keywords = [k for k, _ in kw_counter.most_common(5)] or ["유사", "중복"]
        avg_score = []
        for a, b in combinations(ids, 2):
            for p in pair_lookup.get(tuple(sorted([a, b])), []):
                avg_score.append(p["similarity_score"])
        mean_score = round(sum(avg_score) / len(avg_score), 1) if avg_score else 7.0
        cluster_name = f"{top_keywords[0]} 중심 유사 클러스터"
        record = {
            "cluster_id": f"CL-{idx:03d}",
            "cluster_name": cluster_name,
            "top_keywords": top_keywords,
            "projects": [{"id": m["id"], "name": m["project_name"], "department": m["department"], "budget_base": round(m["base_budget"], 1)} for m in members],
            "project_count": len(members),
            "total_budget": round(total_budget, 1),
            "similarity_score": mean_score,
            "reason": f"{', '.join(top_keywords[:3])} 키워드와 유사 구조 기준",
        }
        records.append(record)
        duplicate_groups.append({
            "group_name": cluster_name,
            "projects": record["projects"],
            "project_count": len(members),
            "total_budget": round(total_budget, 1),
            "reason": record["reason"],
            "grade": "A" if mean_score >= 9 else "B" if mean_score >= 8 else "C",
        })
    return records, duplicate_groups


def build_profile_output(profile_pairs, normalized):
    project_map = {p["id"]: p for p in normalized}
    profiles = {}
    total_pairs = 0
    total_clusters = 0
    for profile, cfg in PROFILE_CONFIG.items():
        pairs = sorted(profile_pairs.get(profile, []), key=lambda x: x["similarity_score"], reverse=True)[:300]
        cluster_ids = build_clusters(pairs)
        clusters, _ = make_cluster_records(cluster_ids, pairs, normalized)
        total_pairs += len(pairs)
        total_clusters += len(clusters)
        profiles[profile] = {
            "metadata": {
                "title": f"{Y['base_year']}년 AI 재정사업 유사/중복성 분석 - {cfg['title']}",
                "profile": profile,
                "generated_at": datetime.now().isoformat(),
                "version": "10.0",
                "methodology": "docs/similarity_logic_analysis.md 기반 가중합 + 텍스트/내역사업 구조 분석",
                "formula": f"score = (F×{cfg['weights']['F']:.2f} + C×{cfg['weights']['C']:.2f} + D×{cfg['weights']['D']:.2f} + E×{cfg['weights']['E']:.2f} + S×{cfg['weights']['S']:.2f}) × TypeGate × 10 + text_bonus",
                "total_items_analyzed": sum(1 for p in normalized if p["profile"] == profile),
                "total_pairs_found": len(pairs),
                "total_clusters_found": len(clusters),
                "score_range": {"min": 5.0, "max": 10.0, "threshold": 5.0},
            },
            "pairs": pairs,
            "clusters": clusters,
        }
    return {
        "generated_at": datetime.now().isoformat(),
        "version": "10.0",
        "llm_enhanced": False,
        "llm_model": None,
        "total_profiles": len(PROFILE_CONFIG),
        "total_pairs": total_pairs,
        "total_clusters": total_clusters,
        "profiles": profiles,
    }


def build_collaboration_network(collab_pairs):
    node_map = {}
    for pair in collab_pairs:
        a = pair["project_a"]
        b = pair["project_b"]
        for side, other in [(a, b), (b, a)]:
            node = node_map.setdefault(side["id"], {
                "hub_project": side,
                "out_degree": 0,
                "in_degree": 0,
                "total_score": 0.0,
                "connected_departments": set(),
                "description": "",
            })
            node["out_degree"] += 1
            node["total_score"] += pair["collaboration_score"]
            node["connected_departments"].add(other["department"])
    network = []
    for node in node_map.values():
        total_degree = node["out_degree"] + node["in_degree"]
        avg_score = node["total_score"] / max(node["out_degree"], 1)
        hub_type = "supply_hub" if avg_score >= 7.5 else "demand_hub"
        network.append({
            "hub_project": node["hub_project"],
            "hub_type": hub_type,
            "out_degree": node["out_degree"],
            "in_degree": node["in_degree"],
            "connected_departments": sorted(node["connected_departments"]),
            "description": f"{node['hub_project']['project_name']}은(는) {len(node['connected_departments'])}개 부처와 협업 연결을 가진 허브 사업이다.",
        })
    network.sort(key=lambda x: (x["out_degree"] + x["in_degree"]), reverse=True)
    return network


def build_collaboration_chains(collab_pairs):
    adjacency = defaultdict(list)
    for pair in collab_pairs:
        a = pair["project_a"]
        b = pair["project_b"]
        adjacency[a["id"]].append((b["id"], pair))
        adjacency[b["id"]].append((a["id"], pair))

    chains = []
    seen = set()
    for source_id, edges in adjacency.items():
        if len(edges) < 2:
            continue
        sorted_edges = sorted(edges, key=lambda x: x[1]["collaboration_score"], reverse=True)
        path = [source_id]
        used_pairs = []
        for target_id, pair in sorted_edges[:3]:
            if target_id not in path:
                path.append(target_id)
                used_pairs.append(pair)
        if len(path) < 3:
            continue
        key = tuple(path)
        if key in seen:
            continue
        seen.add(key)
        departments = []
        total_budget = 0.0
        names = []
        for pair in used_pairs:
            for proj in [pair["project_a"], pair["project_b"]]:
                if proj["department"] not in departments:
                    departments.append(proj["department"])
                names.append(proj["project_name"])
                total_budget += proj.get("budget_2026", 0.0)
        chains.append({
            "chain_id": f"CHAIN-{len(chains)+1:03d}",
            "chain_name": " → ".join(names[:3]),
            "chain_type": "value_chain",
            "chain_length": len(path),
            "departments": departments,
            "total_budget_base": round(total_budget, 1),
            "synergy_scenario": f"{' → '.join(departments[:4])} 순으로 공급-수요 가치사슬을 구성할 수 있다.",
            "project_ids": path,
        })
    chains.sort(key=lambda x: (x["chain_length"], x["total_budget_base"]), reverse=True)
    return chains[:50]


def build_flow_analysis(normalized):
    by_department_year = defaultdict(lambda: defaultdict(float))
    for item in normalized:
        for year, val in item["year_series"].items():
            by_department_year[item["department"]][year] += safe_float(val)
    return {
        "by_department_year": {dept: {year: round(val, 1) for year, val in years.items()} for dept, years in by_department_year.items()},
        "base_year": Y["base_year"],
    }


def build_keyword_clusters(normalized):
    domain_map = defaultdict(list)
    for item in normalized:
        domain_map[item["primary_domain"]].append(item)
    clusters = []
    for domain, items in domain_map.items():
        if len(items) < 3:
            continue
        total_budget = sum(x["base_budget"] for x in items)
        top_keywords = Counter()
        for item in items:
            top_keywords.update(item["keywords"][:6])
        clusters.append({
            "cluster_name": f"{domain} 테마",
            "domain": domain,
            "project_count": len(items),
            "total_budget": round(total_budget, 1),
            "top_keywords": [k for k, _ in top_keywords.most_common(6)],
        })
    clusters.sort(key=lambda x: x["total_budget"], reverse=True)
    return clusters[:30]


def build_same_agency(normalized):
    agency_map = defaultdict(list)
    for item in normalized:
        agency = item["implementing_agency"]
        if agency:
            agency_map[agency].append(item)
    groups = []
    for agency, items in agency_map.items():
        depts = {x["department"] for x in items}
        if len(items) < 2 or len(depts) < 2:
            continue
        groups.append({
            "agency": agency,
            "project_count": len(items),
            "departments": sorted(depts),
            "projects": [{"id": x["id"], "name": x["project_name"], "department": x["department"], "budget_base": round(x["base_budget"], 1)} for x in items[:10]],
        })
    groups.sort(key=lambda x: x["project_count"], reverse=True)
    return groups[:20]


def update_merged_db(db, normalized, sim_pairs, duplicate_groups, collab_pairs, collab_chains, collab_network, keyword_clusters):
    projects = db.get("projects", [])
    total_base = sum(x["base_budget"] for x in normalized)
    total_orig = sum(x["budget_fields"]["original"] for x in normalized)
    by_department = defaultdict(float)
    by_type = Counter()
    by_domain = defaultdict(float)

    for item in normalized:
        by_department[item["department"]] += item["base_budget"]
        by_type[item["profile"]] += 1
        by_domain[item["primary_domain"]] += item["base_budget"]

    def inc_value(item):
        return item["budget_fields"]["base"] - item["budget_fields"]["original"]

    sorted_items = sorted(normalized, key=inc_value, reverse=True)
    top_inc = [{
        "project_name": x["project_name"],
        "code": x["raw"].get("code"),
        "increase": round(inc_value(x), 1),
    } for x in sorted_items[:15] if inc_value(x) > 0]
    top_dec = [{
        "project_name": x["project_name"],
        "code": x["raw"].get("code"),
        "decrease": round(inc_value(x), 1),
    } for x in sorted(normalized, key=inc_value)[:15] if inc_value(x) < 0]

    db.setdefault("metadata", {})
    db.setdefault("analysis", {})
    db["metadata"].update({
        "total_projects": len(projects),
        "project_count": len(projects),
        "total_departments": len(by_department),
        "departments_count": len(by_department),
        f"total_budget_{Y['budget']}": round(total_base, 1),
        f"total_budget_{Y['original']}": round(total_orig, 1),
        "budget_change": round(total_base - total_orig, 1),
        "rnd_projects": sum(1 for x in normalized if x["raw"].get("is_rnd")),
        "info_projects": sum(1 for x in normalized if x["raw"].get("is_informatization")),
        "new_projects": sum(1 for x in normalized if clean_text(x["raw"].get("status")) == "신규"),
        "extraction_date": datetime.now().strftime("%Y-%m-%d"),
        "source": "database/raw 기반 parse_result 통합 데이터",
        "base_year": Y["base_year"],
    })
    db["analysis"].update({
        "by_department": {k: round(v, 1) for k, v in by_department.items()},
        "by_type": dict(by_type),
        "by_domain": {k: round(v, 1) for k, v in by_domain.items()},
        "top_increases": top_inc,
        "top_decreases": top_dec,
        "duplicates": duplicate_groups[:80],
        "duplicate_network": [{"source": p["project_a"]["id"], "target": p["project_b"]["id"], "weight": p["similarity_score"]} for p in sim_pairs[:300]],
        "keyword_clusters": keyword_clusters,
        "same_agency": build_same_agency(normalized),
        "clusters": duplicate_groups[:80],
        "flow": build_flow_analysis(normalized),
        "collaboration": {
            "total_pairs": len(collab_pairs),
            "high_potential_pairs": collab_pairs[:100],
            "collaboration_chains": collab_chains,
            "collaboration_hubs": collab_network[:40],
        },
    })


def save_outputs(db, normalized, sim_pairs, collab_pairs, profile_pairs):
    cluster_ids = build_clusters(sim_pairs)
    sim_clusters, duplicate_groups = make_cluster_records(cluster_ids, sim_pairs, normalized)
    collab_network = build_collaboration_network(collab_pairs)
    collab_chains = build_collaboration_chains(collab_pairs)
    keyword_clusters = build_keyword_clusters(normalized)

    training_pairs = [p for p in sim_pairs if "T04" in set(p["project_a"]["types"]) | set(p["project_b"]["types"])][:400]
    training_cluster_ids = build_clusters(training_pairs)
    training_clusters, _ = make_cluster_records(training_cluster_ids, training_pairs, normalized)

    sim_output = {
        "metadata": {
            "title": "2026년 AI 재정사업 유사/중복성 분석",
            "generated_at": datetime.now().isoformat(),
            "version": "10.0",
            "methodology": "docs/similarity_logic_analysis.md 기반 가중합 + 텍스트/내역사업 구조 분석",
            "formula": "score = (F×W_F + C×W_C + D×W_D + E×W_E + S×W_S) × TypeGate × 10 + text_bonus",
            "llm_enabled": False,
            "total_pairs_found": len(training_pairs),
            "score_range": {"min": 5.0, "max": 10.0, "threshold": 5.0},
        },
        "pairs": training_pairs,
        "clusters": training_clusters,
    }
    with open(SIM_OUT, "w", encoding="utf-8") as f:
        json.dump(sim_output, f, ensure_ascii=False, indent=2)

    hybrid_output = build_profile_output(profile_pairs, normalized)
    with open(HYB_OUT, "w", encoding="utf-8") as f:
        json.dump(hybrid_output, f, ensure_ascii=False, indent=2)

    collab_output = {
        "metadata": {
            "title": "2026년 AI 재정사업 협업 가능성 분석",
            "generated_at": datetime.now().isoformat(),
            "version": "2.0",
            "methodology": "도메인 보완성 + 가치사슬 + 예산 시너지 기반 협업 분석",
            "total_pairs_found": len(collab_pairs),
            "total_sub_projects_analyzed": sum(p["sub_count"] for p in normalized),
        },
        "summary_statistics": {
            "total_pairs": len(collab_pairs),
            "average_score": round(sum(p["collaboration_score"] for p in collab_pairs) / max(len(collab_pairs), 1), 2),
            "type_counts": dict(Counter(p["collaboration_type"] for p in collab_pairs)),
        },
        "pairs": collab_pairs,
        "high_potential_pairs": collab_pairs[:120],
        "collaboration_chains": collab_chains,
        "collaboration_network": collab_network,
    }
    with open(COL_OUT, "w", encoding="utf-8") as f:
        json.dump(collab_output, f, ensure_ascii=False, indent=2)

    update_merged_db(db, normalized, sim_pairs, duplicate_groups, collab_pairs, collab_chains, collab_network, keyword_clusters)
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

    print(f"similarity_analysis.json saved ({len(training_pairs)} pairs)")
    print(f"hybrid_similarity.json saved ({hybrid_output['total_pairs']} pairs / {hybrid_output['total_clusters']} clusters)")
    print(f"collaboration_analysis.json saved ({len(collab_pairs)} pairs)")


def generate_analysis():
    print("Loading merged data...")
    if not DB_PATH.exists():
        print(f"Missing input file: {DB_PATH}")
        return 1
    with open(DB_PATH, "r", encoding="utf-8") as f:
        db = json.load(f)
    projects = db.get("projects", [])
    print(f"Projects loaded: {len(projects)}")
    normalized, sim_pairs, collab_pairs, profile_pairs = build_similarity_outputs(projects)
    save_outputs(db, normalized, sim_pairs, collab_pairs, profile_pairs)
    print("Analysis rebuild completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(generate_analysis())
