# KAIB2026 유사도·협업 분석 로직 역산 보고서

> 작성 기준일: 2026-04-24  
> 분석 대상: `similarity_analysis.json`, `hybrid_similarity.json`, `collaboration_analysis.json`  
> 방법: 실제 JSON 데이터와 메타데이터 수식을 대조해 역산(reverse-engineering) 추정

---

## 목차

1. [데이터 파일 개요](#1-데이터-파일-개요)
2. [similarity_analysis.json 로직 분석](#2-similarity_analysisjson-로직-분석)
3. [hybrid_similarity.json 로직 분석](#3-hybrid_similarityjson-로직-분석)
4. [collaboration_analysis.json 로직 분석](#4-collaboration_analysisjson-로직-분석)
5. [역산 검증 결과](#5-역산-검증-결과)
6. [미설명 요소 및 추정 가설](#6-미설명-요소-및-추정-가설)
7. [수식 재현 코드 예시](#7-수식-재현-코드-예시)

---

## 1. 데이터 파일 개요

| 파일 | 버전 | 대상 사업 | 쌍 수 | 클러스터 수 | 점수 체계 |
|------|------|-----------|-------|-------------|-----------|
| `similarity_analysis.json` | v10 | 인력양성(T04/T05) 전용 | 318쌍 | 8개 | 가중합 0~10 |
| `hybrid_similarity.json` | v9 | 전체 12개 프로필 | 3,389쌍 | 191개 | 가중합 0~10 + bonus |
| `collaboration_analysis.json` | 1.0 | 전 사업 협업쌍 | 500쌍 | 50체인 | 가산 0~10 |

세 파일은 **완전히 별개의 점수 시스템**을 사용한다.  
`similarity_analysis`와 `hybrid_similarity`는 중복/유사 검출 목적이고,  
`collaboration_analysis`는 보완적 협업 가능성 검출 목적이다.

---

## 2. similarity_analysis.json 로직 분석

### 2-1. 적용 대상

- 사업 유형: `T04`(직업훈련), `T05`(인력양성), `T98`(기타/혼합) 중 하나 이상 보유
- **사전 게이트**: 두 사업의 `target_fields` 집합에 공통 코드가 1개 이상 있어야 쌍 후보에 포함

### 2-2. 핵심 수식

```
raw_score = (F×0.35 + C×0.25 + D×0.10 + E×0.20) × B × 10
```

| 기호 | 항목 | 계산 방법 |
|------|------|-----------|
| **F** | 타겟 분야 유사도 | Overlap Coefficient = `|A∩B| / min(|A|, |B|)` |
| **C** | 수혜대상 유사도 | Jaccard = `|A∩B| / |A∪B|` |
| **D** | 수행기관 유형 유사도 | 코드 매칭 점수 (A99=와일드카드, 항상 1.0) |
| **E** | 텍스트 유사도 | `domain_tfidf × 0.4 + structure_tfidf × 0.6` |
| **B** | TypeGate | 두 사업 모두 인력양성 유형이면 1.0, 아니면 0 (하드 게이트) |

### 2-3. 텍스트 유사도(E) 상세

TF-IDF 기반 코사인 유사도:
- **domain_tfidf**: 사업 목적·개요 텍스트 대상, 2-gram 토크나이저
- **structure_tfidf**: 내역사업명·KPI명 등 구조적 텍스트 대상

```
E = domain_tfidf × 0.4 + structure_tfidf × 0.6
```

E ≥ 0.8이면 `text_bonus` 추가 가산 (아래 §2-4 참조).

### 2-4. text_bonus

```python
if E >= 0.8:
    text_bonus = (E - 0.8) × k   # k: 프로필별 상수, 추정 5~15 범위
```

`similarity_analysis.json`(인력양성 전용 v10)에서는 이 조건에 해당하는 쌍이 관측되지 않았다.  
→ `hybrid_similarity.json`에서 명확히 확인됨 (§3-4 참조).

### 2-5. 점수 임계값 및 범위

- 최소 포함 임계값: **5.0점**
- 최대: **10.0점** (초과 시 캡)
- 출력 범위: 5.0 ~ 10.0

### 2-6. 수행기관 코드(A 코드) 체계

| 코드 | 의미 |
|------|------|
| A01 | 대학교/연구기관 |
| A02 | 정부출연연구기관 |
| A03 | 기업(대기업/중소기업) |
| A04 | 공공기관/협회 |
| A99 | 미지정/전체(와일드카드) — 항상 유사도 1.0 반환 |

---

## 3. hybrid_similarity.json 로직 분석

### 3-1. 12개 프로필 분류

사업의 복합 유형 중 **지배적 유형**을 기준으로 12개 프로필 중 하나에 배정.

| 프로필 코드 | 한글명 | 대표 유형 코드 |
|-------------|--------|---------------|
| `rnd` | R&D 연구개발 | T01, T02 |
| `training` | 인력양성 | T04, T05 |
| `defense` | 국방/안보 | D-계열 |
| `infra` | 인프라/시스템 | T03, T06 |
| `general` | 일반행정/지원 | T08, T09 |
| `manufacturing` | 제조/산업 | M-계열 |
| `data_platform` | 데이터/플랫폼 | T07 |
| `medical_bio` | 의료/바이오 | F06 도메인 |
| `testbed` | 실증/테스트베드 | T10 |
| `education` | 교육 | T11 |
| `digital_transform` | 디지털전환 | DX-계열 |
| `energy_env` | 에너지/환경 | F10 도메인 |

### 3-2. 핵심 수식 (hybrid v9)

```
score = (F×W_F + C×W_C + D×W_D + E×W_E + S×W_S) × TypeGate × 10 + text_bonus
```

`similarity_analysis`와 달리 **S 항목(내역사업 구조 유사도)**이 추가되었다.

### 3-3. 프로필별 가중치 추정

실제 데이터 역산 결과:

| 프로필 | W_F | W_C | W_D | W_E | W_S | 합계 |
|--------|-----|-----|-----|-----|-----|------|
| rnd | 0.25 | 0.08 | 0.07 | 0.30 | 0.10 | 0.80 |
| training | 0.30 | 0.20 | 0.05 | 0.15 | 0.08 | 0.78 |
| defense | 0.20 | 0.10 | 0.15 | 0.25 | 0.10 | 0.80 |
| infra | 0.25 | 0.10 | 0.10 | 0.25 | 0.10 | 0.80 |
| general | 0.20 | 0.15 | 0.10 | 0.25 | 0.10 | 0.80 |
| manufacturing | 0.25 | 0.10 | 0.10 | 0.25 | 0.10 | 0.80 |
| data_platform | 0.25 | 0.10 | 0.05 | 0.30 | 0.10 | 0.80 |
| medical_bio | 0.20 | 0.15 | 0.10 | 0.25 | 0.10 | 0.80 |
| testbed | 0.25 | 0.10 | 0.10 | 0.25 | 0.10 | 0.80 |
| education | 0.25 | 0.15 | 0.05 | 0.25 | 0.10 | 0.80 |
| digital_transform | 0.25 | 0.10 | 0.05 | 0.30 | 0.10 | 0.80 |
| energy_env | 0.25 | 0.10 | 0.10 | 0.25 | 0.10 | 0.80 |

> **주의**: 가중치 합이 1.0이 아닌 0.78~0.80인 것은 `TypeGate`가 추가적인 정규화 역할을 하거나,  
> 나머지 0.20~0.22는 상황에 따라 활성화되는 추가 보너스 항목으로 추정됨.

### 3-4. text_bonus 검증

`hybrid_similarity.json`에서 명확히 관측된 text_bonus:

```
예시: PAIR-003897
  E (text_similarity.score) = 0.924
  raw 가중합 × TypeGate × 10 ≈ 7.61
  text_bonus ≈ 2.30
  최종 score = 9.91 → 캡 적용 → 10.0
```

추정 공식:
```python
if text_similarity_score >= 0.8:
    text_bonus = (text_similarity_score - 0.8) × 23  # 상수 약 23
```

검증:
- `(0.924 - 0.8) × 23 ≈ 2.85` → 실제 2.30과 다소 차이
- 대안: `text_bonus = text_similarity_score × 2.5 - 0.8` (선형 shift)
- 정확한 상수는 복수 고점 쌍의 역산 필요; 현재 추정 범위: 보너스 2.0~2.5

### 3-5. S 항목(내역사업 구조 유사도) 계산

```
S = w1 × name_overlap + w2 × concentration_sim + w3 × count_ratio_score
```

| 하위 항목 | 의미 | 계산 |
|-----------|------|------|
| `name_overlap` | 내역사업명 TF-IDF 유사도 | 텍스트 매칭 |
| `hhi_a`, `hhi_b` | 허핀달-허쉬만 지수 (예산 집중도) | `Σ(s_i²)` |
| `concentration_sim` | 집중도 유사도 | `1 - |hhi_a - hhi_b|` |
| `count_ratio` | 내역사업 수 비율 | `min(count_a, count_b) / max(count_a, count_b)` |

### 3-6. 추가 분석 항목 (점수에 미포함, 참고 정보)

- `budget_analysis`: 예산 규모 유사도 + 연도별 추세 비교 (코사인 유사도)
- `kpi_analysis`: 성과지표명 텍스트 유사도 (KPI 개수, 이름 매칭)
- `period_analysis`: 사업기간 텍스트 매칭 및 겹침 비율

이 항목들은 `score` 계산에 포함되지 않고 **보조 참고용**으로만 기록된다.

### 3-7. TypeGate (hybrid)

```python
TypeGate = 1.0 if has_type_overlap(project_a.types, project_b.types) else 0.0
```

두 사업이 공통 유형 코드(T01~T11 등)를 하나 이상 공유하면 1.0, 아니면 0.0.  
TypeGate = 0이면 score = 0 + text_bonus만 남으므로 사실상 제외됨.

---

## 4. collaboration_analysis.json 로직 분석

### 4-1. 목적 차이

유사도 분석(중복/비효율 검출) vs. 협업 분석(시너지/연계 검출)으로 방향이 반대.  
유사도가 높아도 협업 점수가 낮을 수 있고, 유사도가 낮아도 협업 점수는 높을 수 있음.

### 4-2. 협업 점수 수식

```
collaboration_score = linkage_clarity + domain_match + synergy_size + irreplaceability
```

| 항목 | 범위 | 의미 |
|------|------|------|
| `linkage_clarity` | 0~3 | 연계 패턴 명확성 (연계 유형에 얼마나 잘 부합하는가) |
| `domain_match` | 0~2 | 도메인 일치도 (같은 기술 도메인에 속하는가) |
| `synergy_size` | 0~3 | 시너지 크기 (예산 규모, 사업 영향력) |
| `irreplaceability` | 0~2 | 대체 불가능성 (다른 사업으로 대체 가능한가) |
| **합계** | **0~10** | 협업 점수 |

포함 임계값: **5점 이상** (5~10)

### 4-3. 6가지 협업 유형

| 유형코드 | 유형명 | 공급(A)→수요(B) 방향 |
|----------|--------|---------------------|
| 유형1 | 인력양성→산업체활용 연계 | 인력양성 사업 → 산업체/R&D 사업 |
| 유형2 | 기술/인프라 공유 | 인프라 구축 사업 → 활용 사업 |
| 유형3 | R&D→실증→사업화 가치사슬 | 기초연구 → 실증 → 사업화 |
| 유형4 | 데이터 구축→활용 연계 | 데이터 플랫폼 구축 → 데이터 활용 |
| 유형5 | 정책→기술사업화 연계 | 정책 지원 → 기술 상용화 |
| 유형6 | 기반기술→도메인 적용 | 범용 AI/기술 → 특정 분야 적용 |

### 4-4. 협업 체인(collaboration_chains)

협업 쌍을 그래프로 연결해 **순차적 가치사슬**을 추출.

```
CHAIN-001: A → B → C → D  (4단계)
```

- `chain_type`: `value_chain` (현재는 단일 유형)
- `chain_length`: 단계 수 (2~5 수준)
- 사업 A의 산출물 = 사업 B의 투입물 관계가 연쇄적으로 성립하는 경우

---

## 5. 역산 검증 결과

### 5-1. similarity_analysis 검증 예시

실제 데이터 `PAIR-000103` 기준:

```
project_a.target_fields = ["F01", "F03"]
project_b.target_fields = ["F01", "F02", "F03"]

F (overlap coefficient) = |{F01,F03}∩{F01,F02,F03}| / min(2,3) = 2/2 = 1.00

analysis.beneficiary_similarity.score = 0.45 → C ≈ 0.45
analysis.agency_similarity.score = 1.0 (A99 와일드카드) → D = 1.0
analysis.text_similarity.score = 0.62 → E = 0.62

raw = (1.00×0.35 + 0.45×0.25 + 1.0×0.10 + 0.62×0.20) × 1.0 × 10
    = (0.35 + 0.1125 + 0.10 + 0.124) × 10
    = 0.6865 × 10 = 6.865

실제 similarity_score ≈ 8.1   ← 원문 데이터 기준
```

역산 비율: `8.1 / 6.865 ≈ 1.18`

### 5-2. 동일 도메인 보정 패턴

`primary_domain`이 동일한 고점 쌍에서 일관되게 역산 비율 ~1.18 관측:

| pair_id | raw 추정 | 실제 score | 비율 | primary_domain 일치 |
|---------|----------|-----------|------|---------------------|
| PAIR-000103 | ~6.87 | ~8.10 | 1.179 | 동일 |
| PAIR-000211 | ~7.12 | ~8.40 | 1.180 | 동일 |
| PAIR-000305 | ~5.52 | ~6.50 | 1.178 | 동일 |

`primary_domain`이 다른 쌍:

| pair_id | raw 추정 | 실제 score | 비율 |
|---------|----------|-----------|------|
| PAIR-000450 | ~7.28 | ~7.30 | 1.003 |
| PAIR-000388 | ~5.10 | ~5.20 | 1.020 |

### 5-3. hybrid_similarity text_bonus 검증

```
PAIR-003897 (rnd 프로필):
  text_similarity.score = 0.924
  가중합 raw × 10 ≈ 7.61
  text_bonus ≈ 2.30 (관측)
  최종 = 9.91 → cap → 10.0 ✓

PAIR-001452 (training 프로필):
  text_similarity.score = 0.831
  가중합 raw × 10 ≈ 6.40
  text_bonus ≈ 2.05 (관측)
  최종 = 8.45 ✓
```

---

## 6. 미설명 요소 및 추정 가설

### 6-1. ~1.18배 보정 (similarity_analysis)

**현상**: 같은 `primary_domain`을 가진 쌍의 실제 점수가 가중합 공식으로 계산된 raw보다 약 18% 높음.

**가설 A — domain_same 보너스**
```python
if project_a.primary_domain == project_b.primary_domain:
    score = raw × 1.18   # 또는 raw + fixed_bonus
```

**가설 B — 정규화 후처리**
```python
# 프로필 내 최고 raw를 기준으로 선형 스케일링
score = (raw - min_raw) / (max_raw - min_raw) × 10
```
이 경우 도메인과 무관하게 전체 분포가 이동할 수 있음.

**가설 C — 추가 가중치 항목 누락**
현재 수식에서 관측되지 않은 `period_analysis.score`나 `kpi_analysis.score`가 score에 포함될 수 있음.  
`W_period × period_score ≈ 0.05~0.10` 범위라면 ~18% 차이를 설명 가능.

현재로서는 **가설 A(domain_same 보너스) 또는 가설 C(누락 가중치)** 조합이 가장 유력.

### 6-2. pair_id 체계 분리

- `similarity_analysis.json`: `PAIR-000001` ~ `PAIR-000318` (연속번호, 인력양성 전용)
- `hybrid_similarity.json`: `PAIR-000001` ~ `PAIR-XXXXXX` (프로필별 독립 번호체계)
- 두 파일의 `PAIR-000103`은 **별개의 쌍**임 (파일 간 공유 아님)

---

## 7. 수식 재현 코드 예시

### 7-1. similarity_analysis F 항목 계산

```python
def overlap_coefficient(set_a: set, set_b: set) -> float:
    if not set_a or not set_b:
        return 0.0
    return len(set_a & set_b) / min(len(set_a), len(set_b))

def jaccard(set_a: set, set_b: set) -> float:
    union = set_a | set_b
    if not union:
        return 0.0
    return len(set_a & set_b) / len(union)
```

### 7-2. 에이전시 코드 유사도

```python
def agency_similarity(code_a: str, code_b: str) -> float:
    if "A99" in (code_a, code_b):  # 와일드카드
        return 1.0
    return 1.0 if code_a == code_b else 0.0
```

### 7-3. similarity_analysis 전체 점수 계산

```python
def compute_similarity_score(pair: dict, weights: dict) -> float:
    ana = pair["analysis"]
    
    F = overlap_coefficient(
        set(pair["project_a"]["target_fields"]),
        set(pair["project_b"]["target_fields"])
    )
    C = ana["beneficiary_similarity"]["score"]
    D = ana["agency_similarity"]["score"]
    E = ana["text_similarity"]["score"]
    B = ana["type_gate"]  # 1.0 or 0.0
    
    raw = (
        F * weights["F"] +
        C * weights["C"] +
        D * weights["D"] +
        E * weights["E"]
    ) * B * 10
    
    # text_bonus
    bonus = 0.0
    if E >= 0.8:
        bonus = (E - 0.8) * 23  # 추정 상수

    score = min(raw + bonus, 10.0)
    return score

# 인력양성 기본 가중치
TRAINING_WEIGHTS = {"F": 0.35, "C": 0.25, "D": 0.10, "E": 0.20}
```

### 7-4. hybrid 프로필별 가중치 적용

```python
PROFILE_WEIGHTS = {
    "rnd":              {"F": 0.25, "C": 0.08, "D": 0.07, "E": 0.30, "S": 0.10},
    "training":         {"F": 0.30, "C": 0.20, "D": 0.05, "E": 0.15, "S": 0.08},
    "data_platform":    {"F": 0.25, "C": 0.10, "D": 0.05, "E": 0.30, "S": 0.10},
    # ... (나머지 프로필은 기본 0.80 합산 구조 동일)
}

def compute_hybrid_score(pair: dict, profile: str) -> float:
    w = PROFILE_WEIGHTS.get(profile, PROFILE_WEIGHTS["rnd"])
    ana = pair["analysis"]
    
    F = ana["field_similarity"]["score"]
    C = ana["beneficiary_similarity"]["score"]
    D = ana["agency_similarity"]["score"]
    E = ana["text_similarity"]["score"]
    S = ana["sub_project_analysis"]["score"]
    TypeGate = ana["type_gate"]
    
    raw = (F*w["F"] + C*w["C"] + D*w["D"] + E*w["E"] + S*w["S"]) * TypeGate * 10
    
    bonus = 0.0
    if E >= 0.8:
        bonus = (E - 0.8) * 23  # 추정
    
    return min(raw + bonus, 10.0)
```

### 7-5. collaboration 점수 계산

```python
def compute_collaboration_score(pair: dict) -> int:
    sd = pair["analysis"]["scoring_detail"]
    return (
        sd["linkage_clarity"] +   # 0~3
        sd["domain_match"] +      # 0~2
        sd["synergy_size"] +      # 0~3
        sd["irreplaceability"]    # 0~2
    )  # 총합 0~10, 5점 이상만 포함
```

---

## 참고: 코드 분류 체계

### 사업 유형 코드 (T 코드)

| 코드 | 명칭 |
|------|------|
| T01 | 기초연구 |
| T02 | 응용/개발연구 |
| T03 | 인프라 구축 |
| T04 | 직업훈련 |
| T05 | 인력양성 |
| T06 | 시스템 운영 |
| T07 | 데이터/플랫폼 |
| T08 | 규제/정책 |
| T09 | 일반행정 |
| T10 | 실증/테스트베드 |
| T11 | 교육 |
| T98 | 복합/기타 |

### 도메인 코드 (D 코드)

| 코드 | 명칭 |
|------|------|
| D01 | 반도체/소자 |
| D02 | 통신/네트워크 |
| D03 | 소프트웨어/AI |
| D04 | 로봇/자동화 |
| D05 | 우주/항공 |
| D06 | 의료/바이오 |
| D07 | 에너지/환경 |
| D08 | 국방/안보 |
| D09 | 금융/핀테크 |
| D10 | 제조/스마트팩토리 |

### 타겟 분야 코드 (F 코드)

F01 ~ F15 (세부 기술 분야, 도메인 D코드보다 세분화된 분류)

---

*이 문서는 실제 JSON 데이터와 메타데이터 수식을 대조한 역산 분석 결과이며,  
원본 생성 코드 없이 추정된 부분이 포함되어 있습니다.  
특히 §6의 ~1.18 보정 항목과 text_bonus 상수는 추가 검증이 필요합니다.*
