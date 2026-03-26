"""
_years.py  —  연도 설정 공통 모듈
config.yaml의 base_year를 읽어 모든 연도값 자동 계산
어느 스크립트에서도 from _years import get_years 로 사용
"""
from pathlib import Path
import yaml

def get_years(cfg_or_path=None):
    """
    config의 years 섹션을 읽어 전체 연도 dict 반환
    base_year 하나로 모든 연도 자동 계산
    
    반환값:
      base_year:     2026  ← 예산 기준연도 (정부안 연도)
      settlement:    2024  ← 결산 (base-2)
      original:      2025  ← 본예산 (base-1)
      supplementary: 2025  ← 추경 (base-1)
      request:       2026  ← 부처 요구안 (base)
      budget:        2026 (base) = base_year
      sub_years:  [2024, 2025, 2026]  ← 내역사업 3개년
      label_settlement: '2024결산'
      label_original:   '2025본예산'
      label_budget:     '2026정부안'
      label_sub: ['2024예산', '2025예산', '2026예산']
    """
    # config 로드
    cfg = {}
    if cfg_or_path is None:
        # 기본 경로 탐색
        root = Path(__file__).parent.parent.parent
        for p in [root/"config"/"config.yaml", root/"config.yaml"]:
            if p.exists():
                with open(p, encoding="utf-8") as f:
                    cfg = yaml.safe_load(f) or {}
                break
    elif isinstance(cfg_or_path, (str, Path)):
        with open(cfg_or_path, encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
    elif isinstance(cfg_or_path, dict):
        cfg = cfg_or_path

    y_cfg = cfg.get("years", {})

    # base_year 결정 (기본값 2026)
    base = int(y_cfg.get("base_year", 2026))

    # 자동 계산 (수동 override 가능)
    settlement    = int(y_cfg.get("settlement",    base - 2))
    original      = int(y_cfg.get("original",      base - 1))
    supplementary = int(y_cfg.get("supplementary", base - 1))
    request       = int(y_cfg.get("request",       base))
    budget        = int(y_cfg.get("budget",        base))
    sub_years     = y_cfg.get("sub_years", [base-2, base-1, base])
    sub_years     = [int(y) for y in sub_years]

    return {
        # 숫자값
        "base_year":     base,
        "settlement":    settlement,
        "original":      original,
        "supplementary": supplementary,
        "request":       request,
        "budget":        budget,
        "sub_years":     sub_years,
        # 레이블 (템플릿/출력용)
        "label_settlement":  f"{settlement}결산",
        "label_original":    f"{original}본예산",
        "label_supplementary": f"{supplementary}추경",
        "label_request":     f"{request}요구",
        "label_budget":      f"{budget}정부안",
        "label_sub":         [f"{y}예산" for y in sub_years],
        # 컬럼명 → JSON 필드 매핑 (convert.py용)
        "col_map": {
            f"{settlement}결산":    "budget.2024_settlement|to_float",
            f"{original}본예산":    "budget.2025_original|to_float",
            f"{supplementary}추경": "budget.2025_supplementary|to_float",
            f"{request}요구":       "budget.2026_request|to_float",
            f"{budget}정부안":        "budget.2026_budget|to_float",
        },
        "sub_col_map": {
            f"{sub_years[0]}예산":  "budget_2024|to_float",
            f"{sub_years[1]}예산":  "budget_2025|to_float",
            f"{sub_years[2]}예산":  "budget_2026|to_float",
        },
    }


def years_summary(Y):
    """연도 설정 요약 출력"""
    return (f"기준연도: {Y['base_year']} "
            f"(결산={Y['settlement']} / 본예산={Y['original']} / 정부안={Y['budget']})")


if __name__ == "__main__":
    # 직접 실행 시 현재 설정 확인
    Y = get_years()
    print("=== 현재 연도 설정 ===")
    print(f"  base_year    : {Y['base_year']}")
    print(f"  결산연도     : {Y['settlement']}  (budget.2024_settlement)")
    print(f"  본예산연도   : {Y['original']}  (budget.2025_original)")
    print(f"  추경연도     : {Y['supplementary']}  (budget.2025_supplementary)")
    print(f"  요구연도     : {Y['request']}  (budget.2026_request)")
    print(f"  정부안연도   : {Y['budget']}  ★(budget.2026_budget = 정부안)")
    print(f"  내역사업연도 : {Y['sub_years']}  (budget_2024/2025/2026)")
    print()
    print("  템플릿 컬럼명:")
    for col, fld in Y['col_map'].items():
        print(f"    '{col}' → {fld}")
    print()
    print("  2027년으로 바꾸려면: config/config.yaml → years.base_year: 2027")