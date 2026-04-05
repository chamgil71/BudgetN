# ⚡ KAIB2026 운영자 퀵 가이드 (Quick Guide)
> **Fast-Track Operations & Deployment**

본 문서는 데이터 업데이트부터 웹 배포까지 빈번하게 쓰이는 핵심 명령어 및 절차를 요약합니다.

---

## 📌 상황 1: PDF 예산서에서 처음부터 데이터를 추출할 때
비정형 PDF 파일을 `input/` 폴더에 넣고 다음 단계를 순차적으로 실행합니다.

1. **PDF 텍스트/표 추출**
   ```bash
   python scripts/preProc/pdf_to_json.py -i ./input
   ```
2. **사업 단위 분할 및 정밀 파싱**
   ```bash
   python scripts/preProc/budget_parser.py -i ./input -o ./output/individual
   ```
3. **최종 병합 및 스키마 검증**
   ```bash
   python scripts/preProc/json_manager.py merge -i ./output/individual -o ./output/merged.json
   ```

---

## 📌 상황 2: 엑셀(XLSX) 파일을 수정/추가하여 통합할 때
`input/` 폴더에 수정된 엑셀 파일을 넣고 통합 빌드를 수행합니다.

```bash
# 엑셀 임포트 -> JSON 병합 -> AI 분석(유사도/협업) 일괄 수행
python scripts/pipeline/master_builder.py build

# 생성된 결과를 웹 대시보드(web/data)에 배포
python scripts/pipeline/master_builder.py deploy
```

---

## 📌 상황 3: 오프라인(폐쇄망) 배포용 단일 HTML 제작
인터넷이나 서버 구동이 불가능한 환경(USB 배포 등)을 위해 모든 데이터를 포함한 HTML 통파일을 생성합니다.

```bash
# 단일 HTML 압축 생성 (20MB 내외)
python scripts/pipeline/master_builder.py bundle
```
- **산출물**: `output/KAIB2026_Standalone.html` (클릭 시 즉시 구동)

---

## 📌 상황 4: 특정 키워드 검색 동의어 추가
"AI 반도체" 검색 시 "지능형 반도체"가 함께 나오도록 설정합니다.

1. `config/config.yaml`의 `search_aliases:` 하단에 키워드 추가
   ```yaml
   search_aliases:
     '지능형 반도체': ['AI 반도체', 'AI-Semiconductor']
   ```
2. `master_builder.py build` -> `deploy` 재실행

---

## 💡 대시보드 검색 꿀팁 (Advanced Search)
대시보드 상단 검색창은 다음의 특수 구문을 지원합니다.

- **AND 검색 (공백)**: `로봇 인공지능` (두 키워드 모두 포함)
- **OR 검색 (`|`)**: `의료 | 실감` (둘 중 하나라도 포함)
- **NOT 검색 (`-`)**: `인공지능 -인력` (인공지능 포함, 인력양성 제외)
- **구문 검색 (`""`)**: `"스마트 공정"` (정확히 일치하는 문구만)
- **부처 검색**: `과기부` (동의어 사전에 의해 과학기술정보통신부 자동 검색)
