# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# AX-Eval 플러그인 개발 컨텍스트

사업관리본부 직원의 Claude Code AI 활용 수준을 측정하는 플러그인.
**순수 마크다운 기반 아키텍처** — 코드는 `scripts/convert_sessions.py` 하나뿐.

---

## 개발 명령어

```bash
# 전체 프로젝트 일괄 변환 (증분: 이미 변환된 세션은 건너뜀)
python scripts/convert_sessions.py

# 특정 프로젝트만 변환 (--project는 ~/.claude/projects/ 하위 디렉토리명)
python scripts/convert_sessions.py --project -Users-<사용자명>-Desktop-<프로젝트명>

# 여러 프로젝트 지정 (positional 인자)
python scripts/convert_sessions.py -Users-<사용자명>-proj1 -Users-<사용자명>-proj2

# 전체 재변환 (캐시 무시)
python scripts/convert_sessions.py --force

# 도구 결과 전문 포함 (기본: 200자 미리보기)
python scripts/convert_sessions.py --verbose

# 변환 결과 확인
ls ~/ax-eval/conversations/
```

> Python 3.8+ 필요. 외부 패키지 의존성 없음 (표준 라이브러리만 사용).
>
> **증분 변환**: JSONL 파일 수정 시각이 기존 MD보다 최신일 때만 재변환. `--force`로 전체 재변환.
> **프로젝트 이름 매핑**: `~/ax-eval/config/project_names.json`에 `{"디렉토리명": "표시명"}` 형식으로 저장.

---

## 실행 흐름 (컴포넌트 간 연결)

```
사용자: /ax-eval 체크
    └→ commands/ax-eval.md (라우터)
        └→ skills/ax-eval-check/SKILL.md
            ├→ scripts/convert_sessions.py  (최신 로그 변환)
            └→ agents/ax-analyst.md         (4축 스코어 계산)
                ├→ ~/ax-eval/conversations/**/*.md  (변환된 로그 읽기)
                ├→ references/ax-maturity-model.md  (레벨 기준)
                └→ ~/ax-eval/assessments/           (결과 저장)
```

**라우팅 키워드** (commands/ax-eval.md):
- `시작/start/onboard/setup` → ax-eval-onboard
- `체크/check/평가/레벨` → ax-eval-check
- `팁/tip/가이드/guide` → ax-eval-tip

---

## 핵심 설계 원칙

1. **비개발자 우선**: 직원들이 이해할 수 있는 한국어, 별점(⭐), 직관적 용어 사용
2. **3개 명령어만**: `/ax-eval 시작` / `체크` / `팁` — 그 이상 추가 금지
3. **자동 분석 전용**: Claude Code JSONL 로그만 분석 (외부 도구 수집 없음)
4. **vibe-sunsang 기반**: convert_sessions.py와 에이전트 패턴을 재사용

---

## 평가 체계 요약

| 구분 | 내용 |
|------|------|
| 측정 축 | 요청력 / 검증력 / 활용력 / 판단력 |
| 레벨 | ⭐(입문) ~ ⭐⭐⭐⭐⭐(전략) |
| 역할 | 문서 작성 / 데이터 분석 / 소통 조율 / 업무 자동화 |
| 데이터 | `~/.claude/projects/**/*.jsonl` 자동 분석 |

---

## 파일 구조

```
ax-eval/
├── CLAUDE.md                          ← 이 파일
├── .claude-plugin/plugin.json         ← 플러그인 매니페스트
├── commands/ax-eval.md                ← 커맨드 라우터 (시작|체크|팁)
├── agents/ax-analyst.md               ← 4축 스코어링 서브에이전트
├── skills/
│   ├── ax-eval-onboard/SKILL.md      ← 초기 설정 플로우
│   ├── ax-eval-check/SKILL.md        ← 레벨 체크 + 출력
│   └── ax-eval-tip/SKILL.md          ← 레벨별 맞춤 팁
├── scripts/convert_sessions.py        ← JSONL→MD 변환 (vibe-sunsang 기반)
└── references/
    ├── ax-maturity-model.md           ← 4축 × 5레벨 정의 (스코어링 근거)
    ├── antipatterns.md                ← 역할별 흔한 실수
    ├── prompt-templates.md            ← 업무별 프롬프트 템플릿
    └── tips-by-level.md               ← 레벨별 성장 행동 지침
```

### 사용자 데이터 경로 (`~/ax-eval/`)

```
~/ax-eval/
├── config/profile.json               ← 역할, 설정
├── conversations/                    ← 변환된 대화 로그
├── assessments/assessment-*.json     ← 평가 결과
├── exports/growth-report-*.md        ← 성장 리포트
└── growth-log/TIMELINE.md            ← 레벨 변화 기록
```

---

## 스코어링 지표 매핑

convert_sessions.py가 YAML frontmatter에 기록하는 AX 전용 지표:

| frontmatter 키 | 4축 | 설명 |
|----------------|-----|------|
| `avg_user_msg_len` | 요청력 | 평균 메시지 길이 |
| `specific_context_ratio` | 요청력 | 파일명/숫자 포함 비율 |
| `verify_ratio` | 검증력 | 검증 키워드 비율 |
| `tool_diversity` | 활용력 | 사용 도구 종류 수 |
| `orch_tool_count` | 활용력 | Task/Agent 호출 횟수 |
| `tool_error_count` | (참고) | 도구 오류 횟수 |
| `strat_ratio` | 판단력 | 전략 키워드 비율 |
| `thinking_turn_ratio` | 판단력 | 심층 사고 비율 |

**역할별 가중치** (`references/ax-maturity-model.md` 기준):

| 역할 | 요청력 | 검증력 | 활용력 | 판단력 |
|------|--------|--------|--------|--------|
| 문서 작성 | 35% | 30% | 15% | 20% |
| 데이터 분석 | 25% | 35% | 20% | 20% |
| 소통 조율 | 35% | 25% | 15% | 25% |
| 업무 자동화 | 25% | 25% | 35% | 15% |

---

## 개발 규칙

### 허용
- SKILL.md / agent .md 파일 수정 (마크다운 기반 동작 변경)
- `references/` 콘텐츠 추가/수정 (지식베이스 확장)
- `convert_sessions.py` 지표 추가 (새 AX 지표 필요 시)

### 금지
- 명령어 4개 이상 추가 (3개 원칙 유지)
- `~/ax-eval/` 사용자 데이터 직접 수정
- 원본 JSONL 로그 수정
- 비개발자가 이해 못할 용어를 레벨/팁에 사용

---

## 확장 포인트

향후 필요 시 추가 가능한 것들 (지금은 범위 외):
- `skills/ax-eval-growth/` — 시계열 성장 리포트 (현재 체크에 통합)
- 역할별 하위 references 폴더 (antipatterns 세분화)
- TIMELINE.md 자동 초기화 스크립트
