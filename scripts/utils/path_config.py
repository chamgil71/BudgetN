# scripts/utils/path_config.py
from pathlib import Path

# 💡 1. 프로젝트 루트 자동 추적 (이 파일의 위치 기준)
# 현재위치: scripts/utils/path_config.py -> 부모(utils) -> 부모(scripts) -> 부모(project_root)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# 💡 2. Config 및 템플릿 경로
CONFIG_DIR = PROJECT_ROOT / "config"
DEFAULT_CONFIG_PATH = CONFIG_DIR / "config.yaml"
TEMPLATE_PATH = CONFIG_DIR / "template.json"

# 💡 3. Data 파이프라인 단계별 폴더 경로
DATA_DIR = PROJECT_ROOT / "database"             # 데이터 폴더 (루트의 database/)
SRC_DIR = DATA_DIR / "src"                   # Step 1 입력 (PDF)
RAW_DIR = DATA_DIR / "raw"                   # Step 1 출력 / Step 2 입력 (Raw JSON)
STRUCT_DIR = DATA_DIR / "tmp"                # Step 2 출력 / Step 3 입력 (Structured JSON)
PARSE_RESULT_DIR = DATA_DIR / "parse_result" # Step 3 출력 / Step 4 입력 (Parsed JSON)
OUTPUT_DIR = DATA_DIR / "output"             # Step 4 출력 (최종 병합)

# 💡 4. 주요 결과물 파일 경로
MERGED_JSON_PATH = OUTPUT_DIR / "merged.json"

def ensure_pipeline_dirs():
    """파이프라인 실행 전 필요한 모든 폴더가 있는지 확인하고 없으면 생성합니다."""
    for d in [SRC_DIR, RAW_DIR, STRUCT_DIR, PARSE_RESULT_DIR, OUTPUT_DIR]:
        d.mkdir(parents=True, exist_ok=True)