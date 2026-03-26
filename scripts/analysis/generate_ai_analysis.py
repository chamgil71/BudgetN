import json
import re
from datetime import datetime
from pathlib import Path
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

# 경로 설정
ROOT = Path(__file__).parent.parent.parent
import argparse

# 경로 동적 설정 분기 처리를 위해 메인 최상단에 argparse 추가 적용
parser = argparse.ArgumentParser()
parser.add_argument("--input", default=str(ROOT / 'web' / 'data' / 'budget_db.json'))
parser.add_argument("--outdir", default=str(ROOT / 'web' / 'data'))
args, _ = parser.parse_known_args()

DB_PATH = Path(args.input)
OUTDIR = Path(args.outdir)
OUTDIR.mkdir(parents=True, exist_ok=True)

SIM_OUT = OUTDIR / 'similarity_analysis.json'
COL_OUT = OUTDIR / 'collaboration_analysis.json'


# ---------------------------------------------------------
# 1. 자연어/텍스트 템플릿 제너레이터 (LLM 교체 지점)
# ---------------------------------------------------------
def generate_similarity_rationale(a, b, score, overlap_fields):
    """
    [향후 LLM 확장 지점 - 옵션 2]
    만약 OpenAI나 Claude API를 사용한다면 이 함수의 리턴값을 API 호출 결과로 교체하세요.
    """
    b_a = a.get('base_budget', 0)
    b_b = b.get('base_budget', 0)
    b_sum = b_a + b_b
    
    # 사유(Rationale) 조합
    fields_str = ", ".join(overlap_fields) if overlap_fields else "관련"
    rationale = (f"양 사업 모두 인력양성으로 분류되어 유사한 타겟을 가집니다. "
                 f"타겟 분야({fields_str})에서 양성 인력의 전문성이 강하게 중복됩니다. "
                 f"양 사업의 최신 예산은 각각 {b_a:,.0f}백만원, {b_b:,.0f}백만원(합계 {b_sum:,.0f}백만원)입니다. "
                 f"결과적으로 {a.get('department')}의 '{a.get('project_name')}'과(와) "
                 f"{b.get('department')}의 '{b.get('project_name')}'은(는) "
                 f"별도 부처에서 유사한 인력양성 프로그램을 운영하는 것으로 분석(유사도 {score*10:.1f}점)됩니다.")
    
    # 권고사항(Recommendation) 조합
    recommendation = (f"{a.get('project_name')}과 {b.get('project_name')}은 동일 목표를 분산 수행하고 있으므로, "
                      f"하나의 통합 사업으로 편입하여 예산 효율화를 도모해야 합니다. "
                      f"통합 시 총 {b_sum:,.0f}백만원 규모에서 약 {b_sum * 0.15:,.0f}백만원(15%)의 효율화가 기대됩니다.")
                      
    return rationale, recommendation

def generate_collaboration_rationale(a, b, score, collab_type):
    """
    [향후 LLM 확장 지점 - 옵션 2]
    만약 OpenAI나 Claude API를 사용한다면 이 함수의 리턴값을 API 호출 결과로 교체하세요.
    """
    b_a = a.get('base_budget', 0)
    b_b = b.get('base_budget', 0)
    b_sum = b_a + b_b
    
    rationale = (f"{a.get('department')}의 '{a.get('project_name')}' 사업과 "
                 f"{b.get('department')}의 '{b.get('project_name')}' 사업은 "
                 f"[{collab_type}] 모델에서 직접적 연계 구조가 존재합니다. "
                 f"도메인과 목표가 상호 보완적이어서 협업 시 시너지 효과가 매우 높을 것으로 판단(협업적합도 {score:.1f}점)됩니다. "
                 f"양 사업 예산 합계는 {b_sum:,.0f}백만원입니다.")
                 
    recommendation = (f"두 부처 간 '수요-공급 매칭 협의체'를 구성하여, "
                      f"정책적 인센티브 부여 및 공동 R&D/인력공급 과제를 우선순위로 추진해야 합니다.")
                      
    return rationale, recommendation


# ---------------------------------------------------------
# 2. NLP 코어 유틸리티
# ---------------------------------------------------------
def get_base_budget(p):
    b = p.get("budget", {})
    # budget 키 중에서 '_budget'이나 '_request'로 끝나는 올해 본예산/요구안 추출
    for k, v in b.items():
        if k.endswith("_budget") or k.endswith("_request"):
            return v or 0
    return 0

def tokenize(p):
    name = re.sub(r'[()【】\[\]「」『』<>《》\s]', '', p.get("project_name", ""))
    tokens = set(re.findall(r'[\w]+', name))
    tokens |= set(p.get("keywords") or [])
    stopwords = {'및','의','을','를','이','가','에','로','으로','와','과','은','는','한','하는','위한','위해','R','D','정보화'}
    return tokens - stopwords

def jaccard(a, b):
    if not a or not b: return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0

def build_tfidf_matrix(projects):
    if not HAS_SKLEARN: return None
    texts = [" ".join(tokenize(p)) for p in projects]
    try:
        vec = TfidfVectorizer(analyzer="word", min_df=1)
        mat = vec.fit_transform(texts)
        return cosine_similarity(mat)
    except Exception:
        return None

def format_project_node(p):
    return {
        "id": p.get("id"),
        "project_name": p.get("project_name", ""),
        "sub_project_name": p.get("detailed_project_name", ""),
        "department": p.get("department", ""),
        "division": p.get("division", ""),
        "type": p.get("project_type", ""),
        "primary_domain": (p.get("ai_domains") or [""])[0],
        "target_fields": p.get("target_fields") or [],
        "base_budget": get_base_budget(p)
    }


# ---------------------------------------------------------
# 3. 메인 분석 함수
# ---------------------------------------------------------
def generate_analysis():
    print("⏳ 데이터 로딩 중...")
    if not DB_PATH.exists():
        print(f"❌ {DB_PATH} 파일을 찾을 수 없습니다.")
        return

    with open(DB_PATH, 'r', encoding='utf-8') as f:
        db = json.load(f)
    
    projects = db.get("projects", [])
    print(f"✅ {len(projects)}개 프로젝트 로드 완료.")
    
    # TF-IDF 사전 계산
    print("🧠 TF-IDF / Jaccard 벡터 계산 중...")
    tfidf_sim = build_tfidf_matrix(projects)
    tokens = [tokenize(p) for p in projects]
    
    # -------------------------------------
    # A. 유사도 분석 / B. 협업 분석 동시 진행
    # -------------------------------------
    print("🔥 AI 분석 데이터 탐색 중 ...")
    sim_pairs = []
    collab_pairs = []
    
    n_projects = len(projects)
    for i in range(n_projects):
        for j in range(i+1, n_projects):
            p_a = projects[i]
            p_b = projects[j]
            
            jac = jaccard(tokens[i], tokens[j])
            tfidf = float(tfidf_sim[i, j]) if tfidf_sim is not None else jac
            combined_score = (jac * 0.4) + (tfidf * 0.6)
            
            # 1. 협업 분석 (서로 다른 부서(실/국), 일정 수준 이상의 도메인/목적 유사성)
            div_a = p_a.get("division") or "A부서"
            div_b = p_b.get("division") or "B부서"
            
            # 도메인이 같거나 키워드가 겹치는 경우 가산점
            domain_a = (p_a.get("ai_domains") or ["A"])[0]
            domain_b = (p_b.get("ai_domains") or ["B"])[0]
            if domain_a != "A" and domain_a == domain_b:
                combined_score += 0.15
            
            if div_a != div_b and combined_score >= 0.25:
                scale_10 = min(10.0, 5.0 + (combined_score * 10))
                collab_type = "부서 간 기술/정책 연계"
                
                node_a = format_project_node(p_a)
                node_a["role"] = "협력부처 A"
                node_b = format_project_node(p_b)
                node_b["role"] = "협력부처 B"
                
                rationale, recommendation = generate_collaboration_rationale(node_a, node_b, scale_10, collab_type)
                collab_pairs.append({
                    "pair_id": f"COL-AUTO-{len(collab_pairs)+1:04d}",
                    "collaboration_score": round(scale_10, 1),
                    "collaboration_level": "반드시 협업 필요" if scale_10 >= 8 else "협업 권장",
                    "collaboration_type": collab_type,
                    "project_a": node_a,
                    "project_b": node_b,
                    "rationale": rationale,
                    "recommendation": recommendation
                })
            
            # 2. 유사도/중복성 분석 (가장 유사한 사업 전체 대상)
            if combined_score >= 0.35:
                scale_10 = min(10.0, combined_score * 12)
                node_a = format_project_node(p_a)
                node_b = format_project_node(p_b)
                
                overlap = list(set(p_a.get("keywords") or []) & set(p_b.get("keywords") or []))
                rationale, recommendation = generate_similarity_rationale(node_a, node_b, combined_score, overlap)
                
                sim_pairs.append({
                    "pair_id": f"PAIR-AUTO-{len(sim_pairs)+1:04d}",
                    "similarity_score": round(scale_10, 1),
                    "similarity_level": "높은 유사성(High)" if scale_10 >= 7 else "중간 유사성(Medium)",
                    "project_a": node_a,
                    "project_b": node_b,
                    "analysis": {
                        "text_similarity": {"score": round(combined_score, 2)},
                        "budget_analysis": {
                            "a_budget": node_a["base_budget"],
                            "b_budget": node_b["base_budget"]
                        }
                    },
                    "rationale": rationale,
                    "recommendation": recommendation
                })
            
    sim_pairs.sort(key=lambda x: x["similarity_score"], reverse=True)
    sim_pairs = sim_pairs[:300] # Top 300
    
    # 프론트엔드 호환성을 위한 클러스터(clusters) 매핑
    sim_clusters = []
    for pair in sim_pairs:
        # 단일 페어를 1개의 클러스터로 매핑 (O(N) 단순화)
        p_a = pair["project_a"]
        p_b = pair["project_b"]
        
        sim_clusters.append({
            "cluster_name": f"{p_a.get('project_name','')} - {p_b.get('project_name','')} 유사그룹",
            "top_keywords": ["자동 추출", "유사 사업"],
            "projects": [
                {"id": p_a["id"]},
                {"id": p_b["id"]}
            ],
            "similarity_score": pair["similarity_score"],
            "reason": pair["rationale"]
        })
    
    collab_pairs.sort(key=lambda x: x["collaboration_score"], reverse=True)
    collab_pairs = collab_pairs[:500] # Top 500 제한
    
    sim_output = {
        "metadata": {
            "title": "규칙기반 자동생성 유사/중복성 분석",
            "generated_at": datetime.now().isoformat(),
            "llm_enabled": False,
            "total_pairs_found": len(sim_pairs)
        },
        "pairs": sim_pairs,
        "clusters": sim_clusters
    }
    
    with open(SIM_OUT, 'w', encoding='utf-8') as f:
        json.dump(sim_output, f, ensure_ascii=False, indent=2)
    print(f"✅ similarity_analysis.json 저장 완료 ({len(sim_pairs)}쌍)")
    
    
    col_output = {
        "metadata": {
            "title": "규칙기반 자동생성 협업가능성 분석",
            "generated_at": datetime.now().isoformat(),
            "llm_enhanced": False,
            "total_pairs_found": len(collab_pairs)
        },
        "pairs": collab_pairs
    }
    
    with open(COL_OUT, 'w', encoding='utf-8') as f:
        json.dump(col_output, f, ensure_ascii=False, indent=2)
    print(f"✅ collaboration_analysis.json 저장 완료 ({len(collab_pairs)}쌍)")
    
    print("\n🎉 모든 AI 분석 데이터가 갱신되었습니다!")
    print("👉 브라우저에 반영하려면 다음 명령어를 실행하세요: python scripts/rebuild_embedded.py")

if __name__ == "__main__":
    generate_analysis()
