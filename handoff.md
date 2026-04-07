# ax-eval 핸드오프

> AI 소비: 다음 세션 시작 시 이 파일을 먼저 읽을 것.

## 프로젝트 상태

| 항목 | 내용 |
|------|------|
| 버전 | v1.3.0 |
| 상태 | 스코어링 로직 대규모 개선 완료, 팀 내 배포 준비 완료 |
| 리포 | https://github.com/pms0505-lgtm/ax-eval |
| 다음 단계 | GitHub 마켓플레이스 레포(`pms0505-lgtm/biz-plugins`) 생성 → 팀 배포 |

## 프로젝트 개요

사업관리본부 직원의 Claude Code AI 활용 수준(AX 레벨)을 측정·추적하는 Claude Code 플러그인.

- **평가 체계**: 4축(요청력/검증력/활용력/판단력) × 5레벨(⭐~⭐⭐⭐⭐⭐) × 4역할
- **명령어**: `/ax-eval 시작` / `체크` / `팁` (3개 고정)
- **아키텍처**: 순수 마크다운 플러그인 + Python 변환 스크립트 1개

## 파일 구조

```
ax-eval/
├── CLAUDE.md                          ← 플러그인 개발 컨텍스트 (이 세션 작성)
├── handoff.md                         ← 이 파일
├── README.md
├── .claude/settings.local.json        ← compact SessionStart 훅 포함
├── .claude-plugin/plugin.json         ← 플러그인 매니페스트
├── commands/ax-eval.md                ← 커맨드 라우터 (시작|체크|팁)
├── agents/ax-analyst.md               ← 4축 스코어링 서브에이전트
├── skills/
│   ├── ax-eval-onboard/SKILL.md      ← 초기 설정 플로우
│   ├── ax-eval-check/SKILL.md        ← 레벨 체크 + 출력 형식
│   └── ax-eval-tip/SKILL.md          ← 레벨별 맞춤 팁
├── scripts/convert_sessions.py        ← JSONL→MD 변환 (vibe-sunsang 기반, AX 지표 추가)
└── references/
    ├── ax-maturity-model.md           ← 4축 × 5레벨 정의 + 역할별 가중치
    ├── antipatterns.md                ← 역할별 흔한 실수와 개선법
    ├── prompt-templates.md            ← 업무별 프롬프트 템플릿
    └── tips-by-level.md               ← 레벨별 성장 행동 지침
```

## 핵심 설계 결정

| 결정 | 내용 | 이유 |
|------|------|------|
| Claude Code 전용 | 외부 도구(ChatGPT 등) 분석 제외 | 단순화 요청, JSONL 자동분석만 |
| 4축으로 축소 | vibe-sunsang 6축 → 4축 | 비개발자 이해도 우선 |
| 5레벨 별점 | 7단계 숫자 → ⭐~⭐⭐⭐⭐⭐ | 비개발자 직관성 |
| 3명령어 원칙 | 시작/체크/팁만 | 사용자 인지 부하 최소화 |
| 순수 마크다운 | 코드는 convert_sessions.py만 | vibe-sunsang 패턴 준수 |

## 스코어링 로직 (ax-analyst.md 참조)

### 지표 추출 (convert_sessions.py)
- **요청력**: `min(avg_len/200,1.0)*0.2 + specific_ratio*0.5 + structure_ratio*0.3`
- **검증력**: `verify_ratio*0.5 + correction_ratio*0.3 + follow_up_ratio*0.2`
- **활용력**: tool_diversity + orch_tool_count 조건 + harness_count 보너스(+0.5~1.0)
- **판단력**: `strat_ratio*0.6 + alt_request_ratio*0.2 + thinking_turn_ratio*0.2` + harness 보너스(+0.3)

### 하네스 엔지니어링 신호 (신규)
- `claude_md_access` / `rules_used` / `memory_used` / `slash_cmd_ratio` → `harness_count(0~4)`
- tool_use input.file_path에서 자동 탐지

### 레벨 판정
- 각 축 1~5점 → 역할별 가중 평균 → ⭐(1.0~1.8미만) ~ ⭐⭐⭐⭐⭐(4.2~5.0)
- 세션 3~5개: 최소 보장 없이 실제 점수 + `(데이터 부족)` 주석 표시

### 역할별 가중치 (5개 직군)
| 역할 | 요청력 | 검증력 | 활용력 | 판단력 |
|------|--------|--------|--------|--------|
| UA마케터 | 35% | 25% | 25% | 15% |
| CRM마케터 | 30% | 30% | 15% | 25% |
| 디자이너 | 40% | 20% | 25% | 15% |
| 데이터분석가 | 20% | 35% | 25% | 20% |
| 개발자 | 20% | 30% | 35% | 15% |
| 미선택 | 25% | 25% | 25% | 25% |

## 사용자 데이터 경로

```
~/ax-eval/
├── config/profile.json           ← 역할, 생성일
├── config/project_names.json     ← CC 프로젝트 이름 매핑
├── conversations/                ← 변환된 대화 로그 (convert_sessions.py 출력)
├── assessments/                  ← assessment-YYYY-MM-DD.json
├── exports/                      ← growth-report-*.md
└── growth-log/
    ├── TIMELINE.md
    └── weekly/
```

## 변경 이력

| 날짜 | 버전 | 내용 |
|------|------|------|
| 2026-04-07 | v1.3.0 | Opus 딥리서치 기반 스코어링 개선 — 버그 3건 수정(역할 체계 불일치, 확인 오탐, specificity 과대), 개선 4건(follow_up 통합, avg_len 200, 활용력 5점 완화, 최소보장 제거), 하네스 엔지니어링 신호 5개 추가, .gitignore 갱신 |
| 2026-04-07 | v1.2.0 | `enabledPlugins`에 `ax-eval@local` 등록 (Unknown skill 해결), CLAUDE.md에 레벨 점수 범위/집계 방식/Auto-Nudge 훅/엣지 케이스 섹션 추가 |
| 2026-04-07 | v1.2.0 | git init + GitHub push (pms0505-lgtm/ax-eval), plugin.json 스키마 수정, 로컬 플러그인 등록 (~/.claude/plugins/cache/local/ax-eval/1.2.0), CLAUDE.md 개발 명령어 버그 수정 |
| 2026-04-07 | v1.2.0 | 하네스 엔지니어링 — ax-analyst 자기검증 체크리스트, 행동 앵커, 엣지케이스 규칙, 중앙값 집계, 구조 점검 버그 4건 수정 |
| 2026-04-07 | v1.1.0 | Auto-Nudge — SessionStart/Stop 훅으로 약한 축 자동 피드백 추가 |
| 2026-04-07 | v1.0.1 | CLAUDE.md 개선 — /init 헤더, 개발 명령어, 실행 흐름 다이어그램 추가 |
| 2026-04-06 | v1.0.0 | 초기 구현 — 전체 플러그인 구조 생성 |

## 자동 피드백 시스템 (Auto-Nudge) — v1.1.0 추가

### 파일

| 파일 | 역할 |
|------|------|
| `~/.claude/scripts/ax-nudge.sh` | SessionStart 훅 — 약한 축 자동 피드백 (주 1회) |
| `~/.claude/scripts/ax-eval-log-sync.sh` | Stop 훅 — 세션 종료 시 JSONL→MD 자동 변환 |
| `~/.claude/settings.json` | 글로벌 훅 2개 추가 |

### 동작 로직

- **세션 시작 시**: `~/ax-eval/assessments/` 최신 파일에서 약한 축 추출 → `systemMessage`로 Claude 컨텍스트 주입
- **쿨다운**: `~/ax-eval/.nudge-stamp` 파일로 7일 제어 (stamp 삭제 시 즉시 재표시)
- **staleness**: assessment가 14일 이상 지났으면 `/ax-eval 체크` 권유 문구 자동 추가
- **세션 종료 시**: `convert_sessions.py` 백그라운드 실행으로 최신 로그 변환

### 검증 완료

| 케이스 | 결과 |
|--------|------|
| 정상 피드백 | systemMessage JSON 출력 확인 |
| 7일 쿨다운 | 출력 없음 (정상) |
| 14일+ 경과 | 체크 권유 문구 추가 확인 |
| assessment 없음 | 조용히 종료 확인 |

---

## 다음 세션 TODO (우선순위 순)

1. [ ] **팀 배포**: `pms0505-lgtm/biz-plugins` GitHub 마켓플레이스 레포 생성 → ax-eval 등록 → 팀원 설치 테스트 ← 최우선
2. [ ] GitHub push (현재 로컬 커밋 5개 미push 상태)
3. [ ] E2E 실테스트: `/ax-eval 시작` → `체크` → `팁` 전체 플로우 확인
4. [ ] ax-eval-log-sync.sh Stop 훅 실환경 검증
5. [x] ~~스코어링 로직 Opus 딥리서치 기반 개선~~ (완료 — v1.3.0)
6. [x] ~~하네스 엔지니어링 신호 추가~~ (완료)
7. [x] ~~enabledPlugins에 ax-eval@local 등록~~ (완료)
8. [x] ~~git init + GitHub push~~ (완료: pms0505-lgtm/ax-eval)
