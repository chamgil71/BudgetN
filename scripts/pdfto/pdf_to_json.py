import argparse
import sys
import logging
import json
import yaml
import pdfplumber

from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel


# -------------------------
# Logging 설정
# -------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


# -------------------------
# Pydantic Models
# -------------------------
class TableModel(BaseModel):
    rows: List[List[Optional[str]]]


class PageModel(BaseModel):
    page_number: int
    text: Optional[str]
    tables: List[TableModel] = []


class DocumentModel(BaseModel):
    pages: List[PageModel]


# -------------------------
# Converter Class
# -------------------------
class PdfToJsonConverter:

    @staticmethod
    def extract_data(pdf_path: Path) -> Optional[DocumentModel]:
        logger.info(f"📄 PDF 파싱 시작: {pdf_path.name}")

        pages = []

        try:
            with pdfplumber.open(pdf_path) as pdf:
                total = len(pdf.pages)
                logger.info(f"총 페이지 수: {total}")

                for i, page in enumerate(pdf.pages, start=1):
                    logger.info(f"[{i}/{total}] 페이지 처리 중...")

                    text = page.extract_text()

                    raw_tables = page.extract_tables()
                    tables = [
                        TableModel(rows=table)
                        for table in raw_tables
                    ]

                    page_model = PageModel(
                        page_number=i,
                        text=text,
                        tables=tables
                    )

                    pages.append(page_model)

            logger.info(f"✅ PDF 파싱 완료: {pdf_path.name}")
            return DocumentModel(pages=pages)

        except Exception as e:
            logger.error(f"❌ PDF 읽기 실패 ({pdf_path.name}): {str(e)}")
            return None

    @staticmethod
    def save_outputs(doc: DocumentModel, pdf_path: Path, output_dir: Path):

        output_dir.mkdir(parents=True, exist_ok=True)

        base_name = pdf_path.stem
        json_path = output_dir / f"{base_name}_raw.json"
        yaml_path = output_dir / f"{base_name}_raw.yaml"

        # JSON 저장
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(doc.model_dump(), f, indent=2, ensure_ascii=False)

        logger.info(f"💾 JSON 저장 완료: {json_path.name}")

        # YAML 저장
        with open(yaml_path, "w", encoding="utf-8") as f:
            yaml.dump(doc.model_dump(), f, allow_unicode=True, default_flow_style=False)

        logger.info(f"💾 YAML 저장 완료: {yaml_path.name}")


# -------------------------
# Target Processing
# -------------------------
def process_targets(input_target: Path, output_dir: Path):

    pdf_files = []

    if input_target.is_file() and input_target.suffix.lower() == ".pdf":
        pdf_files.append(input_target)

    elif input_target.is_dir():
        pdf_files = list(input_target.glob("*.pdf"))

    else:
        logger.error(f"유효한 PDF 파일이나 폴더가 아닙니다: {input_target}")
        return

    if not pdf_files:
        logger.warning("처리할 PDF가 없습니다.")
        return

    logger.info(f"총 {len(pdf_files)}개 PDF 처리 시작")

    for idx, pdf_path in enumerate(pdf_files, start=1):
        logger.info(f"===== [{idx}/{len(pdf_files)}] 파일 처리 시작 =====")

        doc = PdfToJsonConverter.extract_data(pdf_path)

        if doc:
            PdfToJsonConverter.save_outputs(doc, pdf_path, output_dir)

    logger.info("🎉 전체 작업 완료")


# -------------------------
# CLI
# -------------------------
def main():
    parser = argparse.ArgumentParser(description="PDF → JSON/YAML 변환기")

    parser.add_argument(
        "-i", "--input",
        default="src",    
        help="PDF 파일 또는 폴더 경로(default: src)"
    )

    parser.add_argument(
        "-o", "--output",
        default="input",
        help="출력 폴더 (default: input)"
    )

    args = parser.parse_args()

    input_path = Path(args.input).resolve()
    output_dir = Path(args.output).resolve()

    process_targets(input_path, output_dir)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("사용자 중단")
        sys.exit(0)
    except Exception as e:
        logger.critical(f"시스템 오류: {e}")
        sys.exit(1)