# Prompthon Baseline Code

프롬프트 해커톤을 위한 고도화된 베이스라인 코드입니다.

## 🎯 프로젝트 개요

**목표**: 고전 한국어(한자·한문·고어 혼용)를 현대 한국어 기사체로 정확하고 자연스럽게 변환

**핵심 전략**:
- 📐 **4단계 계층 프롬프트**: 시스템 메시지 → Core Rules → SELF-DISCOVER Reasoning → Few-shot
- 🧠 **메타인지 기반 추론**: JSON 구조화된 7가지 추론 모듈
- 📊 **평가 지표 정렬**: 각 Core Rule이 4가지 평가 기준과 직접 연결
- 🛡️ **보수적 접근**: 정보 보존 우선, 확신 없으면 변경하지 않음

**평가 방식**: Omission / Restoration / Naturalness / Accuracy 4개 카테고리 자동 평가 (LLM 기반)

## 📋 필수 파일 설명

```
code/
├── baseline_generate.py   # 현대어 변환 문장 생성 스크립트
├── evaluate.py            # 평가 스크립트
├── metrics.py             # Omission/Restoration/Naturalness/Accuracy 기반 평가 메트릭 계산
├── prompts.py             # 프롬프트 템플릿 (이 파일을 수정하세요!)
├── pyproject.toml         # Python 의존성 관리
├── .python-version        # Python 버전 명시
├── .env.example           # 환경 변수 예시
└── data/                  # 데이터셋 디렉토리
    └── train_dataset.csv  # 학습 데이터 (여기에 넣으세요)
```

## 🚀 빠른 시작

### 1. 환경 설정

```bash
# uv 설치 (이미 설치되어 있다면 생략)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 의존성 설치
uv sync
```


### 2. API 키 설정

# .env 파일을 열어서 API 키 입력
# UPSTAGE_API_KEY=your_actual_api_key_here

Upstage API 키는 [https://console.upstage.ai/](https://console.upstage.ai/)에서 발급받을 수 있습니다.

> 💡 **팁**: `.env` 파일은 API 키 같은 민감한 정보를 저장하는 파일이므로 Git에 커밋되지 않도록 `.gitignore`에 포함되어 있습니다.

### 3. 데이터 준비

`data/train_dataset.csv` 파일을 준비합니다. 파일은 다음 컬럼을 포함해야 합니다:
- `original_sentence`: 변환이 필요한 원문
- `answer_sentence`: 변환된 현대어 문장 (평가 시 사용)

### 4. 변환 문장 생성

```bash
# 기본 실행
uv run python baseline_generate.py

# 옵션 지정
uv run python baseline_generate.py --input data/train_dataset.csv --output submission.csv --model solar-pro2
```

생성된 `submission.csv` 파일은 다음 컬럼을 포함합니다:
- `original_sentence`: 원문
- `answer_sentence`: AI가 변환한 문장

### 5. 평가

```bash
# 기본 실행
uv run python evaluate.py

# 옵션 지정
uv run python evaluate.py --true_df data/train_dataset.csv --pred_df submission.csv --output analysis.csv
```

평가 결과:
- 콘솔에는 Omission / Restoration / Naturalness / Accuracy 4개 카테고리의 평균 점수와 전체 평균 점수가 출력됩니다.
- 각 샘플별 상세 평가 결과는 analysis.csv 파일로 저장됩니다.
- 전체 평가 요약은 analysis_summary.txt 파일로 저장됩니다.

## 🎯 프롬프트 핵심 전략

현재 베이스라인은 **4단계 계층 구조**의 고도화된 프롬프트 전략을 사용합니다:

### 📐 프롬프트 구조

```
1. 시스템 메시지 (Role 정의)
   ↓
2. Core Rules (7가지 핵심 제약)
   ↓
3. SELF-DISCOVER Reasoning (JSON 기반 추론 구조)
   ↓
4. Few-shot Example (구체적 변환 예시)
   ↓
5. 원문 입력
```

### 🎭 1단계: 시스템 메시지

```python
system_message = """
# Role
당신은 한자·한문·고어·외래어가 혼용된 문장을 현대 한국어 기사체로 
자연스럽고 정확하게 재작성하는 전문 에디터입니다.
"""
```

**전략**: 전문가 역할 부여 + 입출력 특성 명시

### 📜 2단계: Core Rules (7가지 제약)

| 규칙 | 내용 | 목표 평가 지표 |
|------|------|---------------|
| **Rule 1** | 정보 삭제/요약 금지 | **Omission ⬆️** |
| **Rule 2** | 새로운 정보 추가 금지 | **Accuracy ⬆️** |
| **Rule 3** | 논리 구조 보존 | **Accuracy ⬆️** |
| **Rule 4** | 보수적 □ 복원 | **Restoration ⬆️** |
| **Rule 5** | 수치/고유명사 정확성 | **Accuracy ⬆️** |
| **Rule 6** | 현대 기사체 한 문장 출력 | **Naturalness ⬆️** |
| **Rule 7** | 메타 정보 배제 | 출력 품질 |

**핵심 철학**: 
- 📌 **보수적 접근**: 확신할 수 없으면 하지 않는다
- 📌 **정보 보존 우선**: 모든 원문 정보 유지
- 📌 **평가 기준 정렬**: 각 규칙이 평가 지표와 직접 연결

### 🧠 3단계: SELF-DISCOVER Reasoning

Google DeepMind의 SELF-DISCOVER 논문 기반 메타인지 전략:

**7가지 추론 모듈**:
1. **의미 단위 분해**: 원문을 주체·행위·대상·수치로 분해
2. **정보 보존 검사**: 모든 정보 단위 반영 확인
3. **논리 관계 추출**: 원인·결과·배경·조건·대조 파악
4. **고어/한문 의미 분석**: 의미 등가 현대어 치환
5. **문장 재구성**: 현대 기사체 한 문장으로 연결
6. **스타일 제약 점검**: 기사체 톤&매너 확인
7. **누락/추가 금지 검증**: 최종 품질 검증

**7단계 절차**:
```
분해 → 식별 → 파악 → 치환 → 재배열 → 재검증 → 출력
```

**효과**: 
- ✅ 구조화된 사고로 일관성 향상
- ✅ 이중 검증으로 오류 감소
- ✅ 단계별 명확성

### 📚 4단계: Few-shot Example

**선택 기준**:
- ✅ 띄어쓰기 없음
- ✅ 한자 병기
- ✅ 결손 문자 (□)
- ✅ 고유명사 + 수치 정보
- ✅ 복잡한 문장 구조

**변환 포인트**:
- 띄어쓰기 정규화: `12만환` → `12만 환`
- 고어 현대화: `전기한` → `이들에게`
- 문장 구조 개선: `~인데` → `~했으며`, `~있어`
- 정보 100% 보존
- 한 문장 통합

## 🎯 성능 개선 방법

### 프롬프트 수정 가이드

`prompts.py` 파일의 `baseline_prompt`를 수정하여 성능을 개선할 수 있습니다.

#### 1️⃣ Core Rules 강화
```python
# Rule 4 예시: □ 복원 기준 구체화
□ 기호는 문맥상 100% 확신할 수 있고 단어 1-2개로 명확히 추론되는 경우에만 복원
```

#### 2️⃣ Few-shot 예시 추가
```python
# 다양한 난이도와 패턴의 예시 2-3개 추가
# 제목 있는 예시, 수치 많은 예시, □ 많은 예시 등
```

#### 3️⃣ 추론 모듈 커스터마이징
```python
# 특정 카테고리 약점 보완용 모듈 추가
"수치_정확성_검증": {
    "목표": "모든 숫자가 원문과 동일한지 재확인",
    "규칙": "단위 변환이나 계산 절대 금지"
}
```

#### 4️⃣ 체인-오브-쏘트 명시화
```python
# 단계별 출력 요구
[분석] 원문의 의미 단위
[변환] 현대어 치환
[검증] 누락/추가 확인
[최종] 완성된 문장
```

### 실험 전략

1. **카테고리별 집중 개선**
   - `analysis.csv`에서 낮은 점수 카테고리 파악
   - 해당 카테고리 관련 Rule 강화

2. **Few-shot 다양화**
   - 에러 패턴별 예시 추가
   - 네거티브 예시 (잘못된 변환) 포함

3. **시스템 메시지 최적화**
   - `baseline_generate.py` 129-135번 줄 수정
   - 더 구체적인 역할 정의

4. **모델 및 하이퍼파라미터**
   - `--model solar-pro2` (기본값)
   - `temperature=0.0` (결정적 출력)
   - `reasoning_effort="low"` (빠른 추론)

## 📊 평가 메트릭

평가는 총 4개 품질 기준에 대해 모델이 생성한 문장을 LLM(GPT-4o-mini)이 자동 평가합니다:

### 1️⃣ Omission (누락)
**평가 내용**: 원문 정보가 변환 문장에서 누락된 정도

**체크 항목**:
- ❌ 문장 전체 누락
- ❌ 제목 누락
- ❌ 세부 정보/수식어 누락

**연결된 Core Rule**: Rule 1 (정보 삭제/요약 금지)

### 2️⃣ Restoration (복원)
**평가 내용**: □ (결손 문자) 복원 정확도

**체크 항목**:
- ❌ 미복원 □ (복원하지 않은 채 남김)
- ❌ 부적절한 복원 (문맥에 맞지 않음)
- ❌ 과도한 복원 (1-2개 □를 여러 단어로 확장)

**연결된 Core Rule**: Rule 4 (보수적 □ 복원)

### 3️⃣ Naturalness (자연스러움)
**평가 내용**: 현대 한국어로서의 자연스러움

**체크 항목**:
- ❌ 존댓말 불일치 (합니다/하다 혼용)
- ❌ 고어 표현 잔존 (~할지라도, ~하도다)
- ❌ 직역체 (어색한 어순)
- ❌ 부자연스러운 어휘 선택

**연결된 Core Rule**: Rule 6 (현대 기사체 한 문장 출력)

### 4️⃣ Accuracy (정확성)
**평가 내용**: 의미 왜곡 및 불필요한 추가 정보

**체크 항목**:
- ❌ 핵심 정보 왜곡 (고유명사, 지명 변경)
- ❌ 수치 오류 (숫자, 날짜, 단위 변경)
- ❌ 의미 반전 (긍정↔부정, 원인↔결과)
- ❌ 부적절한 추가 (원문에 없는 정보)

**연결된 Core Rules**: Rule 2, 3, 5 (추가 금지, 논리 보존, 수치 정확성)

### 점수 변환 기준

| 오류 개수 | 점수 | 평가 |
|-----------|------|------|
| 0개 | 1.0 | ✅ 완벽 |
| 1개 | 0.9 | ✅ 매우 우수 |
| 2개 | 0.7 | 🟡 양호 |
| 3개 | 0.5 | 🟡 보통 |
| 4개 | 0.3 | 🔴 미흡 |
| 5개 | 0.1 | 🔴 불량 |
| 6개+ | 0.0 | 🔴 심각 |

**최종 점수**: 4개 카테고리 점수의 산술 평균

```
최종 점수 = (Omission + Restoration + Naturalness + Accuracy) / 4
```

## 💡 프롬프트 최적화 팁

### 1. 데이터 기반 개선 🔍

```bash
# 1단계: 평가 실행
uv run python evaluate.py

# 2단계: analysis.csv 분석
# - 어떤 카테고리 점수가 낮은가?
# - 어떤 유형의 원문에서 실패하는가?
# - 공통 오류 패턴이 있는가?
```

**예시**:
- Omission 점수가 낮다면? → Rule 1 강화, 정보 보존 체크리스트 추가
- Restoration 점수가 낮다면? → Rule 4 강화, □ 복원 예시 추가
- Naturalness 점수가 낮다면? → Rule 6 강화, 기사체 스타일 가이드 추가
- Accuracy 점수가 낮다면? → Rule 2,3,5 강화, 네거티브 예시 추가

### 2. Few-shot 예시 전략 📚

**다양성 확보**:
```python
# 현재: 1개 예시
# 권장: 2-3개 예시 (다양한 패턴)

예시 1: 긴 문장 + 많은 수치
예시 2: 제목 있는 문장 + □ 많음
예시 3: 복잡한 한자 + 논리 구조
```

**네거티브 예시 추가**:
```python
# ❌ 잘못된 변환 예시도 포함
[잘못된 예시]
원문: "농촌이 인재를 잃는 상황"
❌ 틀린 변환: "농촌이 인재를 얻는 상황" (의미 반전)
✅ 올바른 변환: "농촌이 인재를 잃는 상황"
```

### 3. Rule 커스터마이징 🎯

**카테고리별 Rule 강화**:

```python
# Omission 개선
Rule 1+: "제목, 고유명사, 수치, 날짜는 반드시 포함해야 합니다"

# Restoration 개선  
Rule 4+: "□는 주변 2-3단어 문맥으로 100% 확신할 때만 복원"

# Naturalness 개선
Rule 6+: "고어 표현(~할지라, ~하도다) 완전 제거, 존댓말 통일"

# Accuracy 개선
Rule 5+: "숫자는 절대 변경 금지, 계산 금지, 단위 변환 금지"
```

### 4. 추론 절차 확장 🧠

```python
# 현재: 7단계
# 확장: 8-9단계 (검증 강화)

procedure: [
    # ... 기존 7단계 ...
    "8. 수치·고유명사·날짜가 원문과 100% 일치하는지 재확인",
    "9. 고어·한자 표현이 완전히 제거되었는지 최종 확인"
]
```

### 5. 시스템 메시지 최적화 💬

**현재** (`baseline_generate.py` 129-135번 줄):
```python
"당신은 한자·한문·고어·외래어가 혼용된 문장을 현대 한국어 기사체로 
자연스럽고 정확하게 재작성하는 전문 에디터입니다."
```

**개선 예시**:
```python
"당신은 고전 한국어를 현대 한국어 기사체로 변환하는 전문가입니다.
원문의 모든 정보를 누락 없이 보존하고, 추가 해석 없이 
정확하게 변환하는 것이 최우선 목표입니다."
```

### 6. 반복 실험 전략 🔄

```bash
# A/B 테스트 프로세스
1. 베이스라인 평가 (현재 점수 기록)
2. 프롬프트 수정 (Rule 1개씩 변경)
3. 재평가 (점수 변화 확인)
4. 개선되면 유지, 악화되면 롤백
5. 반복
```

### 7. 모델 및 파라미터 조정 ⚙️

```bash
# 모델 변경
--model solar-pro2  # 기본값 (균형)
--model solar-pro   # 더 강력
--model solar-mini  # 더 빠름

# 병렬 처리 최적화
--max_workers 2      # 배치 간 병렬도
--max_parallel 5     # 배치 내 병렬도

# Temperature (baseline_generate.py 54번 줄)
temperature=0.0  # 결정적 (기본값, 권장)
temperature=0.1  # 약간의 다양성
```

### 8. 디버깅 모드 활용 🐛

```bash
# 상세 로그 출력
uv run python baseline_generate.py --debug --log_file debug.log

# 로그에서 확인할 내용:
# - API 요청/응답 시간
# - Rate limit 재시도 횟수
# - 병렬 처리 통계
# - 에러 패턴
```

## 🔧 문제 해결

### API 키 오류
```
ValueError: UPSTAGE_API_KEY not found in environment variables
```
→ `.env.example` 파일을 `.env`로 **이름을 변경**했는지 확인하세요!  
→ `.env` 파일에 실제 API 키가 입력되어 있는지 확인하세요.

### 컬럼 오류
```
ValueError: Input CSV must contain 'original_sentence' column
```
→ 데이터셋에 `original_sentence` 컬럼이 있는지 확인하세요.

### 길이 불일치 오류
```
ValueError: Length mismatch: truth=100 vs pred=99
```
→ 생성 과정에서 일부 샘플이 누락되었습니다. 에러 로그를 확인하세요.

## 📚 참고 자료

- **Upstage API 문서**: https://console.upstage.ai/docs/getting-started
- **uv 문서**: https://docs.astral.sh/uv/
- **SELF-DISCOVER 논문**: Google DeepMind (2024) - "Self-Discover: Large Language Models Self-Compose Reasoning Structures"
- **프롬프트 엔지니어링 가이드**: https://platform.openai.com/docs/guides/prompt-engineering

## 🎓 프롬프트 전략 요약

```
✅ 4단계 계층 구조
   └─ 시스템 메시지 + 7가지 Core Rules + SELF-DISCOVER + Few-shot

✅ 평가 기준 정렬
   └─ 각 Rule이 Omission/Restoration/Naturalness/Accuracy와 직접 연결

✅ 메타인지 추론
   └─ 7개 모듈 + 7단계 절차로 구조화된 사고

✅ 보수적 접근
   └─ 정보 보존 우선, 확신 없으면 변경하지 않음
```

**핵심 성공 요소**:
1. 📊 **데이터 분석**: `analysis.csv`로 약점 파악
2. 🔄 **반복 실험**: A/B 테스트로 점진적 개선
3. 🎯 **타겟 최적화**: 낮은 점수 카테고리 집중 공략
4. 📚 **예시 강화**: 다양한 패턴의 Few-shot 추가

---

**Good luck with your prompt engineering!** 🚀

*"The right prompt is 80% of the solution."*

