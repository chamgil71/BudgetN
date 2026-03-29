# 정부 R&D 사업 정적 사이트 생성 가이드

## 개요

`generate_html.py` 하나로 **목록 페이지(app.html)**와 **개별 상세 페이지(html/*.html)**를 자동 생성합니다.
React/TSX 파일은 **필요 없습니다**. Python + JSON만 있으면 됩니다.

## 필요 파일

| 파일 | 설명 |
|------|------|
| `scripts/generate_html.py` | 사이트 생성 스크립트 |
| `merged.json` | 사업 데이터 (JSON) |

## 사용법

```bash
# 기본: 현재 디렉토리에 생성
python scripts/generate_html.py merged.json

# 출력 디렉토리 지정 (예: docs/ 폴더)
python scripts/generate_html.py merged.json ./docs
```

## 생성 결과

```
{출력디렉토리}/
├── app.html                          ← 목록 페이지 (브라우저에서 이것을 열기)
└── html/
    ├── 4231-301_4대지역외_AX_대전환_기획.html
    ├── 2602-367_AI_AGENT_선도_국가_사업.html
    ├── 2602-365_AGI_준비_프로젝트.html
    └── ... (사업 수만큼 생성)
```

## 사용 흐름

1. **JSON 파일 준비** — `merged.json` (아래 형식 참고)
2. **스크립트 실행** — `python scripts/generate_html.py merged.json ./docs`
3. **브라우저에서 확인** — `docs/app.html` 열기
4. **목록에서 사업명 클릭** → 상세 페이지로 이동

## JSON 데이터 형식

```json
{
  "projects": [
    {
      "id": "PRJ-XXXXX",
      "project_name": "사업명",
      "code": "1234-567",
      "department": "부처명",
      "account_type": "일반회계",
      "status": "계속",
      "field": "분야",
      "sector": "부문",
      "division": "과명",
      "support_type": "출연",
      "implementing_agency": "시행기관",
      "program": { "code": "1200", "name": "프로그램명" },
      "unit_project": { "code": "1234", "name": "단위사업명" },
      "detail_project": { "code": "567", "name": "세부사업명" },
      "project_period": {
        "start_year": 2024,
        "end_year": 2028,
        "duration": "5년",
        "raw": "'24~'28"
      },
      "total_cost": { "total": 50000, "government": 40000 },
      "budget": {
        "2025_settlement": 10000,
        "2026_original": 12000,
        "2026_supplementary": null,
        "2027_request": 15000,
        "2027_budget": 14000,
        "change_amount": 2000
      },
      "sub_projects": [
        { "name": "세부1", "budget_2024": 1000, "budget_2025": 2000, "budget_2026": 3000 }
      ],
      "project_managers": [
        {
          "sub_project": "세부사업명",
          "managing_dept": "관리과",
          "implementing_agency": "시행기관",
          "manager": "홍길동",
          "phone": "044-000-0000"
        }
      ],
      "purpose": "사업 목적 설명",
      "legal_basis": "법적 근거",
      "keywords": ["AI", "반도체"],
      "ai_domains": ["자연어처리"]
    }
  ]
}
```

## GitHub Actions 연동

워크플로에서 사용할 경우:

```yaml
- name: 사이트 빌드
  run: python scripts/generate_html.py data/merged.json ./docs
```

생성된 `docs/` 폴더를 Vercel이나 GitHub Pages에서 정적 호스팅하면 됩니다.

## FAQ

**Q: React/TSX 파일도 필요한가요?**
A: 아닙니다. `generate_html.py`가 순수 HTML을 생성하므로 Python만 있으면 됩니다. TSX는 별도 개발서버용입니다.

**Q: JSON을 업데이트하면?**
A: 스크립트를 다시 실행하면 app.html과 모든 상세 페이지가 재생성됩니다.

**Q: 파일명 규칙은?**
A: `{사업코드}_{사업명}.html` (공백→언더스코어, 슬래시→언더스코어)

**Q: 로컬에서 바로 열 수 있나요?**
A: 네. `app.html`을 더블클릭하면 브라우저에서 바로 열립니다. 서버 불필요.
