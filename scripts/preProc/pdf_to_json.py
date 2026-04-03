import pdfplumber
import json
import logging
import argparse
from typing import Dict, Any, Union
from pathlib import Path

logger = logging.getLogger(__name__)

# 💡 [해결 1] main_cli.py가 Pydantic 모델을 기대하는 것을 충족시키기 위한 래퍼 클래스
class DocumentResponse:
    def __init__(self, data: dict):
        self._data = data
        
    def dict(self):
        return self._data
        
    def model_dump(self):
        return self._data


class PdfToJsonConverter:
    @staticmethod
    def extract_data(pdf_path: Union[str, Path]) -> DocumentResponse:
        """PDF에서 페이지별로 텍스트와 표를 Y좌표 기반 순서대로(Blocks) 추출"""
        pdf_path_str = str(pdf_path)
        data = {"source": pdf_path_str, "pages": []}
        
        try:
            with pdfplumber.open(pdf_path_str) as pdf:
                total_pages = len(pdf.pages)
                print(f"\n[PDF 추출 시작] 총 {total_pages}페이지 문서 파싱을 시작합니다.")
                
                for i, page in enumerate(pdf.pages):
                    # 💡 [해결 2] 페이지별 작동 안내창 복구
                    print(f"  ⏳ {i + 1} / {total_pages} 페이지 텍스트 및 표 추출 중...", end='\r')
                    
                    blocks = []
                    tables = page.find_tables()
                    tables.sort(key=lambda t: t.bbox[1]) # Y좌표(위->아래) 정렬
                    
                    current_y = 0
                    for table in tables:
                        # 1. 표 '위'에 있는 텍스트 추출 (Crop)
                        if table.bbox[1] > current_y:
                            bbox = (0, current_y, page.width, table.bbox[1])
                            try:
                                cropped = page.crop(bbox)
                                text = cropped.extract_text()
                                if text and text.strip():
                                    blocks.append({"type": "text", "content": text.strip()})
                            except Exception:
                                pass
                        
                        # 2. 표 데이터 추출
                        blocks.append({"type": "table", "content": table.extract()})
                        current_y = table.bbox[3]
                    
                    # 3. 마지막 표 '아래'에 남은 텍스트 추출
                    if current_y < page.height:
                        bbox = (0, current_y, page.width, page.height)
                        try:
                            cropped = page.crop(bbox)
                            text = cropped.extract_text()
                            if text and text.strip():
                                blocks.append({"type": "text", "content": text.strip()})
                        except Exception:
                            pass

                    # 구버전 파서 호환을 위해 text, tables 필드 생성 + 순서 보존형 blocks 추가
                    full_text = page.extract_text() or ""
                    raw_tables = [t.extract() for t in page.find_tables()]
                    
                    data["pages"].append({
                        "page_number": i + 1,
                        "text": full_text,
                        "tables": raw_tables,
                        "blocks": blocks
                    })
                
                # 추출 완료 안내
                print(f"\n✅ [PDF 추출 완료] {total_pages}페이지 처리 성공")
                logger.info(f"✅ PDF 텍스트/표 순차 추출 완료: {pdf_path_str}")
                
        except Exception as e:
            logger.error(f"❌ PDF 파싱 실패 ({pdf_path_str}): {e}")
            print(f"\n❌ PDF 파싱 실패: {e}")
            
        # 단순 딕셔너리가 아닌, main_cli.py의 .model_dump() 호출을 견디는 객체 반환
        return DocumentResponse(data)


# CLI 실행용 (테스트 단독 실행 시)
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", required=True)
    parser.add_argument("-o", "--output", required=True)
    args = parser.parse_args()
    
    result_obj = PdfToJsonConverter.extract_data(args.input)
    
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        # 파일로 저장할 때는 딕셔너리 형태로 저장
        json.dump(result_obj.dict(), f, ensure_ascii=False, indent=2)