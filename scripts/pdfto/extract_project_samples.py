import json
import os
import argparse
import sys

def extract_project_samples():
    parser = argparse.ArgumentParser(description="merged.json의 project 리스트에서 샘플 추출")
    
    # 옵션 설정 (하드코딩 방지)
    parser.add_argument("-i", "--input", required=True, help="원본 merged.json 경로")
    parser.add_argument("-o", "--output", default="sample_project.json", help="저장할 파일명")
    parser.add_argument("-n", "--count", type=int, default=5, help="추출할 사업(project) 개수")

    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"❌ 에러: 파일을 찾을 수 없습니다: {args.input}")
        sys.exit(1)

    try:
        with open(args.input, 'r', encoding='utf-8') as f:
            full_data = json.load(f)

        # 1. 구조 확인 (metadata, project, analysis 존재 여부)
        if 'project' not in full_data:
            print("❌ 에러: JSON에 'project' 키가 존재하지 않습니다. 구조를 확인해주세요.")
            sys.exit(1)

        # 2. 데이터 추출 (기존 구조 복사 후 project만 슬라이싱)
        sample_data = full_data.copy()
        original_count = len(full_data['project'])
        target_count = min(original_count, args.count)
        
        sample_data['project'] = full_data['project'][:target_count]

        # 3. 저장
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(sample_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 추출 완료!")
        print(f"   - 원본 사업 수: {original_count}개")
        print(f"   - 샘플 사업 수: {target_count}개 (대상: {args.output})")
        print(f"   - 계층 구조(metadata, analysis)는 그대로 유지되었습니다.")

    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    extract_project_samples()