# KAIB2026 경로 지정 규칙 정리 및 리팩토링 계획

## 1. 개요
최근 프로젝트 구조 변경으로 인해 `input`, `output`, `raw`, `parse_result` 등 대다수의 데이터 산출물이 `database/` 폴더 하위로 이동되었습니다. 기존 스크립트 중 일부가 여전히 루트 디렉토리의 구 버전 경로를 참조하거나, 코드 내에 경로가 하드코딩되어 있어 오동작 가능성이 확인되었습니다.

## 2. 주요 문제점 분석

### ① 설정 파일(`config/config.yaml`) 불일치
*   현재 `paths` 섹션이 이전 구조(`input/`, `output/` 등)를 그대로 유지하고 있습니다.
*   파이프라인 실행 시 잘못된 경로에 파일을 생성하거나 찾지 못하는 원인이 됩니다.

### ② 코드 내 경로 하드코딩
*   **`master_builder.py`**: `ROOT / "output" / "merged.json"`, `ROOT / "web" / "data"` 등이 하드코딩되어 있습니다.
*   **`sync_data.py`**: `Path('web/data/budget_db.json')` 등이 하드코딩되어 있습니다.
*   **`convert.py`**: `watch_mode` 등에서 `config.yaml`의 구 버전 경로를 그대로 사용합니다.

### ③ 경로 정의 중복
*   **`main_cli.py`**: 클래스 내부에서 `self.data_dir = self.project_root / "database"` 등을 별도로 정의하고 있습니다.
*   **`path_config.py`**: 중앙 관리용 파일이 존재하지만, 정작 주요 스크립트들이 이를 임포트하여 사용하지 않고 있습니다.

## 3. 리팩토링 및 정리 대상 파일

| 파일 경로 | 문제 유형 | 수정 방향 |
| :--- | :--- | :--- |
| `config/config.yaml` | 설정값 오류 | `paths` 하위 경로들을 `database/` 기준으로 업데이트 |
| `scripts/utils/path_config.py` | 활용도 낮음 | 모든 스크립트가 참조하는 **Single Source of Truth**로 확립 |
| `scripts/pipeline/master_builder.py` | 하드코딩 | `path_config.py`의 상수(PROJECT_ROOT, OUTPUT_DIR 등) 사용 |
| `scripts/pipeline/convert.py` | 설정 의존적 | `path_config.py`를 통해 경로를 가져오도록 수정 |
| `scripts/preProc/main_cli.py` | 중복 정의 | 내부 경로 변수들을 `path_config.py` 참조로 대체 |
| `scripts/legacy_tools/sync_data.py` | 하드코딩 | `web/data` 경로 등을 `path_config.py`에 추가 후 참조 |

## 4. 제안하는 폴더 지정 규칙 (Standard)

모든 스크립트는 다음 규칙을 준수해야 합니다:
1.  **직접 문자열 경로 사용 금지**: `os.path.join("a", "b")` 대신 `path_config.py`의 상수를 사용합니다.
2.  **상대 경로 지양**: `PROJECT_ROOT`를 기준으로 한 절대 경로(Path객체)를 사용합니다.
3.  **환경 변화 대응**: 폴더 구조가 바뀌면 `path_config.py` 한 곳만 수정하면 되도록 구성합니다.

## 5. 단계별 실행 계획
1.  [ ] `config.yaml` 경로 값 수정
2.  [ ] `path_config.py`에 웹 배포 경로(`WEB_DATA_DIR`) 등 누락된 상수 추가
3.  [ ] 파이프라인 핵심 파일(`master_builder`, `convert`, `main_cli`) 리팩토링
4.  [ ] 유틸리티 및 기타 스크립트(`sync_data` 등) 정리
