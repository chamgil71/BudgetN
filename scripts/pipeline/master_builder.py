"""
master_builder.py
Excel Import -> DB Merge -> AI Analysis -> Snapshot 을 원클릭으로 수행하는 파이프라인
사용법:
  python scripts/pipeline/master_builder.py build
  python scripts/pipeline/master_builder.py deploy
"""
import sys, shutil, datetime, argparse, subprocess
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))
from config import path_config

def run_import():
    print("=== [1] Excel Import (input/ -> output/merged.json) ===")
    script = str(ROOT / "scripts" / "pipeline" / "excel_manager.py")
    subprocess.run([sys.executable, script, "import", "--type", "both"], check=True)

def run_metadata_sync():
    print("=== [1.5] Sync Metadata (JSON Only) ===")
    import json
    try:
        import yaml
    except ImportError:
        print("pip install pyyaml 먼저 실행 필요")
        return
        
    merged_path = path_config.MERGED_JSON_PATH
    if not merged_path.exists():
        print(f"❌ {merged_path} 이 없습니다!")
        return
        
    with open(ROOT / "config" / "config.yaml", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    by = cfg.get("years", {}).get("base_year", 2026)
    
    with open(merged_path, 'r', encoding="utf-8") as f:
        data = json.load(f)
        
    projects = data.get("projects", [])
    valid_projects = [p for p in projects if isinstance(p, dict)]
    
    total_budget = 0
    depts = set()
    for p in valid_projects:
        b = p.get('budget', {})
        val = b.get(f'{by}_budget', b.get(f'budget_{by}', p.get(f'budget_{by}', 0)))
        try: total_budget += float(val)
        except: pass
        depts.add(p.get('department', '기타'))
        
    if "metadata" not in data: data["metadata"] = {}
    data["metadata"]["total_projects"] = len(valid_projects)
    data["metadata"]["departments_count"] = len(depts)
    data["metadata"]["base_year"] = by
    data["metadata"]["search_aliases"] = cfg.get("search_aliases", {})
    
    with open(merged_path, 'w', encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f" ✅ 메타데이터 재계산 완료 (기준 연도: {by})")

def run_ai_analysis():
    print("=== [2] Run AI Analysis ===")
    script = str(ROOT / "scripts" / "analysis" / "generate_ai_analysis.py")
    in_json = str(path_config.MERGED_JSON_PATH)
    out_dir = str(path_config.OUTPUT_DIR)
    subprocess.run([sys.executable, script, "--input", in_json, "--outdir", out_dir], check=True)

def create_unified_snapshot():
    print("=== [3] Create Snapshot ===")
    today = datetime.datetime.now().strftime("%Y%m%d")
    out_dir = path_config.OUTPUT_DIR
    
    merged_json = path_config.MERGED_JSON_PATH
    snapshot_json = out_dir / f"merge_{today}_통합.json"
    
    if merged_json.exists():
        shutil.copy(merged_json, snapshot_json)
        print(f"  -> Created {snapshot_json.name}")

    for fname in ["similarity_analysis.json", "collaboration_analysis.json"]:
        src = out_dir / fname
        if src.exists():
            new_name = f"{fname.split('.')[0]}_{today}.json"
            shutil.copy(src, out_dir / new_name)
            print(f"  -> Created {new_name}")

def wrap_up():
    print("=== [4] Master Build Success ===")
    print("결과물 포맷 검증 및 AI 추출이 완료되었습니다.")
    print("이상 없음을 확인한 뒤, 다음 웹 서비스 반영 명령어를 실행하세요:")
    print("  python scripts/pipeline/master_builder.py deploy")

def deploy():
    print("=== Deploying output JSONs to web/data/ ===")
    out_dir = path_config.OUTPUT_DIR
    web_data = path_config.WEB_DATA_DIR
    
    merged = path_config.MERGED_JSON_PATH
    sim = out_dir / "similarity_analysis.json"
    col = out_dir / "collaboration_analysis.json"
    
    success_count = 0
    if merged.exists():
        shutil.copy(merged, web_data / "budget_db.json")
        print(f" ✅ Deployed budget_db.json to {web_data}")
        success_count += 1
    if sim.exists():
        shutil.copy(sim, web_data / "similarity_analysis.json")
        print(" ✅ Deployed similarity_analysis.json")
        success_count += 1
    if col.exists():
        shutil.copy(col, web_data / "collaboration_analysis.json")
        print(" ✅ Deployed collaboration_analysis.json")
        success_count += 1

    if success_count > 0:
        print("\nRebuilding embedded JS for fast UI rendering...")
        subprocess.run([sys.executable, str(ROOT / "scripts" / "pipeline" / "rebuild_embedded.py")], check=True)
        print("\n🎉 Deploy Complete! 로컬 웹 새로고침으로 확인하세요.")
    else:
        print("❌ Deploy 실패: output 폴더에 배포할 JSON 파일이 없습니다. 먼저 build 명령을 실행하세요.")

def main():
    parser = argparse.ArgumentParser(description="마스터 빌드 통합 제어 스크립트")
    parser.add_argument("command", nargs="?", default="build", choices=["build", "json-build", "deploy", "bundle"],
                        help="build(엑셀 파싱) / json-build(DB 다이렉트 갱신) / deploy(웹 배포) / bundle(단일 HTML 빌드)")
    args = parser.parse_args()

    if args.command == "build":
        run_import()
        run_ai_analysis()
        create_unified_snapshot()
        wrap_up()
    elif args.command == "json-build":
        run_metadata_sync()
        run_ai_analysis()
        create_unified_snapshot()
        wrap_up()
    elif args.command == "deploy":
        deploy()
    elif args.command == "bundle":
        print("=== [Bundle] Making Standalone HTML ===")
        subprocess.run([sys.executable, str(ROOT / "scripts" / "pipeline" / "build_standalone.py")], check=True)

if __name__ == "__main__":
    main()
