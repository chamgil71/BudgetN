from pathlib import Path

# 1. 프로젝트 루트 자동 추적
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# 2. 주요 폴더 경로 (Single Source of Truth)
CONFIG_DIR = PROJECT_ROOT / "config"
DATA_DIR   = PROJECT_ROOT / "database"

# 3. 데이터 파이프라인 단계별 폴더 (database/ 하위)
INPUT_DIR        = DATA_DIR / "input"         # 원본 엑셀/데이터
SRC_DIR          = DATA_DIR / "src"           # 원본 PDF 등
RAW_DIR          = DATA_DIR / "raw"           # 1차 파싱 결과
STRUCT_DIR       = DATA_DIR / "structure"     # 구조화 데이터 (기존 tmp)
PARSE_RESULT_DIR = DATA_DIR / "parse_result"  # 분석 결과
OUTPUT_DIR       = DATA_DIR / "output"        # 웹 배포용 최종 합본
BACKUP_DIR       = DATA_DIR / "backup"        # 백업

# 4. 기타 주요 경로
MERGED_JSON_PATH = OUTPUT_DIR / "merged.json"
WEB_DIR          = PROJECT_ROOT / "web"
WEB_DATA_DIR     = WEB_DIR / "data"
LOGS_DIR         = PROJECT_ROOT / "logs"

def ensure_pipeline_dirs():
    """파이프라인 실행 전 필요한 모든 폴더가 있는지 확인하고 없으면 생성합니다."""
    dirs = [
        INPUT_DIR, SRC_DIR, RAW_DIR, STRUCT_DIR, 
        PARSE_RESULT_DIR, OUTPUT_DIR, BACKUP_DIR, 
        WEB_DATA_DIR, LOGS_DIR
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
