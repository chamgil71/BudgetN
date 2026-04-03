import json
import sys
from datetime import datetime
from pathlib import Path

# 파이썬 경로 인식 (가장 중요!)
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

# 공통 설정 불러오기
from config.path_config import MERGED_JSON_PATH
from scripts.pipeline._years import get_years

def update_metadata_only():
    Y = get_years()
    year_req = Y['request']   # 예: 2026
    year_orig = Y['original'] # 예: 2025

    print(f"⏳ 데이터 읽는 중... ({MERGED_JSON_PATH.name})")
    
    if not MERGED_JSON_PATH.exists():
        print("❌ merged.json 파일을 찾을 수 없습니다.")
        sys.exit(1)

    with open(MERGED_JSON_PATH, 'r', encoding='utf-8') as f:
        db = json.load(f)

    projects = db.get("projects", [])
    if not projects:
        print("❌ 프로젝트 데이터가 없습니다.")
        sys.exit(1)

    # --- 1. 통계 계산용 동적 변수 준비 ---
    depts = set()
    total_req = 0.0  # 당해년도(26년) 예산
    total_orig = 0.0 # 전년도(25년) 예산
    rnd_cnt = 0
    info_cnt = 0
    new_cnt = 0
    by_dept = {}

    # 헬퍼 함수: 본예산/요구안 추출
    def get_base_budget(p):
        b = p.get("budget", {})
        for k, v in b.items():
            if k.endswith("_budget") or k.endswith("_request"):
                return v or 0.0
        return 0.0

    # --- 2. 1509개 프로젝트 순회하며 집계 ---
    for p in projects:
        dept = p.get("department", "").strip() or "기타"
        depts.add(dept)
        
        b_req = get_base_budget(p)
        b = p.get("budget", {})
        b_orig = b.get(f"{year_orig}_original", 0.0) or b.get(f"{year_orig}_budget", 0.0) or 0.0
        
        total_req += b_req
        total_orig += b_orig
        
        if p.get("is_rnd"): rnd_cnt += 1
        if p.get("is_informatization"): info_cnt += 1
        if p.get("status") == "신규": new_cnt += 1

        by_dept[dept] = by_dept.get(dept, 0.0) + b_req

    # --- 3. 예산 증액 Top 10 뽑기 ---
    def get_increase(proj):
        b = proj.get("budget", {})
        b_req_val = get_base_budget(proj)
        b_orig_val = b.get(f"{year_orig}_original", 0.0) or b.get(f"{year_orig}_budget", 0.0) or 0.0
        return b_req_val - b_orig_val
               
    sorted_projs = sorted(projects, key=get_increase, reverse=True)
    top_inc = [
        {
            "project_name": p.get("project_name", ""),
            "code": p.get("code", ""),
            "increase": get_increase(p)
        }
        for p in sorted_projs[:10] if get_increase(p) > 0
    ]

    # --- 4. 데이터 덮어쓰기 (동적 연도 키 적용) ---
    if "metadata" not in db: db["metadata"] = {}
    if "analysis" not in db: db["analysis"] = {}

    db["metadata"].update({
        "total_projects": len(projects),
        "project_count": len(projects),
        "total_departments": len(depts),
        "departments_count": len(depts),
        # 동적으로 키 생성 (예: total_budget_2026, total_budget_2025)
        f"total_budget_{year_req}": total_req,
        f"total_budget_{year_orig}": total_orig,
        "budget_change": total_req - total_orig,
        "rnd_projects": rnd_cnt,
        "info_projects": info_cnt,
        "new_projects": new_cnt,
        "extraction_date": datetime.now().strftime("%Y-%m-%d"),
        "source": "PDF 직접 파싱 데이터",
        "base_year": year_req
    })

    db["analysis"].update({
        "by_department": by_dept,
        "top_increases": top_inc
    })

    with open(MERGED_JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

    print(f"✅ 메타데이터 및 집계 완료! (총 {len(projects)}건 처리)")
    print(f"💰 {year_req}년 총 예산: {total_req:,.0f} 백만원")

if __name__ == "__main__":
    update_metadata_only()