# ⚡ KAIB2026 파이프라인 퀵 가이드 (Quick Guide)

## 📌 상황 1: 엑셀 또는 예전 JSON 파일로 처음부터 데이터 빌드할 때
`input/` 폴더 내에 엑셀(총괄표, A4요약표) 파일이나 다른 시스템에서 받아온 `~.json` 파일을 마구잡이로 넣어두면, 파이프라인이 하나의 `budget_db.json`으로 병합시켜줍니다.

```powershell
# 엑셀 파싱 -> 연도 자동변경 -> 병합 -> AI 분석 일괄 수행
python scripts/pipeline/master_builder.py build

# 완성된 결과물들을 웹 서버(대시보드)에 덮어씌워 배포
python scripts/pipeline/master_builder.py deploy
```

---

## 📌 상황 2: 엑셀 없이, 기존에 생성된 DB만 갱신할 때
이미 어제 배포가 다 끝났는데, `output/merged.json` 원본 내용을 누군가 수동으로 조금 수정했거나, `config.yaml`의 **기준연도(base_year)** 만 바꿔서 대시보드를 새로고침하고 싶을 때 사용합니다.

```powershell
# 엑셀 임포트 생략 -> JSON 다이렉트 메타데이터 갱신 및 AI 분석
python scripts/pipeline/master_builder.py json-build

# 완성된 결과물들을 웹 서버(대시보드)에 덮어씌워 배포
python scripts/pipeline/master_builder.py deploy
```

---

## 📌 상황 3: 오프라인(USB) 배포용 단일 HTML 파일로 구워낼 때
웹 서버(`python -m http.server`)를 켤 수 없는 폐쇄망 환경에서 클릭 한 번으로 대시보드를 열어보고 싶을 때, 모든 CSS, JS, 데이터를 HTML 통파일 하나에 압축해줍니다.

```powershell
# 단일 HTML 파일 압축 생성 (20MB 내외)
python scripts/pipeline/master_builder.py bundle
```
> **👉 보관 위치:** `output/KAIB2026_Standalone.html`

---

## 📌 상황 4: 특정 부처 약칭이나 동의어를 추가/수정하고 싶을 때
"과기부" 검색 시 "과학기술정보통신부"가 나오게 하려면 `config/config.yaml` 파일만 수정하면 됩니다.

1. **`config/config.yaml`** 열기
2. **`search_aliases:`** 섹션 하단에 원하는 키워드 추가
   ```yaml
   search_aliases:
     '내약칭': ['검색될_풀네임1', '검색될_풀네임2']
   ```
3. 수정 후 위의 **[상황 2]** 절차(`json-build` -> `deploy`)를 수행하여 반영.

---

## 💡 검색 꿀팁 (Advanced Search)
개요 탭과 사업목록 탭의 검색창은 다음의 강력한 기능을 똑같이 지원합니다.
- **띄어쓰기**: `로봇 과기부` (로봇과 과기부가 모두 포함된 사업 - AND)
- **파이프 기호(`|`)**: `로봇 | 드론` (로봇 또는 드론 중 하나라도 포함 - OR)
- **마이너스 기호(`-`)**: `인공지능 -의료` (인공지능 포함하되 의료는 제외 - NOT)
- **구문 검색(`""`)**: `"스마트 제조"` (정확히 해당 문구가 붙어있는 것만 검색)
