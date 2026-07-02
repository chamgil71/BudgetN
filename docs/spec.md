# BudgetN 사양서 (spec.md)

> [!IMPORTANT]
> 본 사양서는 개발 요구사항 및 설계의 **닻(anchor)**입니다.
> 에이전트 단독으로 수정할 수 없으며, 변경 시 반드시 사용자의 사전 승인을 받아야 합니다.
> 아래 `TODO` 표시 구간은 초기 골격이며, 실제 값은 사용자 확정 후 채웁니다.

## 1. 개요 및 목적
- **비즈니스 배경**: 정부 예산 자료가 PDF·XLSX·YAML 등 이질적 포맷으로 흩어져 있어 통합 분석이 어렵다.
- **해결하려는 문제**: 다양한 입력 포맷을 단일 canonical 데이터베이스(`merged.json`)로 수렴시키고, 사업 간 유사도·부처 협업 관계를 자동 분석한다.
- **최종 목표**: PDF 파싱 → 통합 → 분석 → 웹 대시보드 자동 배포까지 이어지는 7단계 파이프라인을 `master_builder.py` 한 줄로 재현 가능하게 유지한다.

## 2. 세부 요구사항 및 범위
- **기능 요구사항** (README 기준 시드 — 상세화 TODO):
  - F-1: 멀티 포맷(PDF/XLSX/YAML/JSON) 수집 → canonical schema(`merged.json`) 수렴
  - F-2: TF-IDF + Cosine Similarity + Jaccard 기반 사업 유사도·부처 협업 네트워크 산출
  - F-3: 네트워크 없이 동작하는 Embedded JS Fallback(`embedded-*.js`) 번들링
  - F-4: `main` 푸시 시 GitHub Actions로 `web/dist` GitHub Pages 자동 배포
  - F-5: _TODO — 추가 기능 요구사항_
- **비기능 요구사항**:
  - 성능: 전체 파이프라인 재생성 허용 시간 baseline _TODO_
  - 보안: 입력 데이터/키의 하드코딩 금지, `config/`·환경변수 주입
  - 재현성: 단계별 입·출력 파일 경계 유지

## 3. 시스템 아키텍처 및 설계
- **데이터 흐름**: `입력(PDF/XLSX/YAML)` → `파싱(backend/scripts)` → `통합(merged.json)` → `분석(TF-IDF)` → `web/ 정적 대시보드`
- **7단계 파이프라인 명세**: _TODO — 각 단계 입·출력 파일명 표로 확정_
- **데이터 스키마(`merged.json`)**: _TODO — canonical schema 필드 명세_

## 4. 검증 계획
- **테스트 시나리오**: 파이프라인 재생성 후 산출 JSON 스키마 정합성 및 대시보드 빌드 성공 확인
- **검증 명령**:
  ```bash
  python master_builder.py
  cd web && npm run build
  ```
- **기대 성공 지표**: 파이프라인 무오류 완주 + 대시보드 정적 빌드 성공. 유닛 테스트 합격선 _TODO_.
