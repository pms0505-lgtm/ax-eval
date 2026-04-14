# ax-eval 핸드오프

> 다음 세션 시작 시 이 파일부터 읽을 것.

## 프로젝트 상태

| 항목 | 내용 |
|------|------|
| 버전 | v1.5.0 |
| 상태 | v1.5.0 하네스 진단 구현 완료 (미커밋) |
| 리포 | https://github.com/pms0505-lgtm/ax-eval |
| 마켓플레이스 | https://github.com/pms0505-lgtm/biz-plugins |

## 다음 세션 TODO

1. [ ] **v1.5.0 커밋+push**: `scripts/convert_sessions.py`, `agents/ax-analyst.md`, `skills/ax-eval-check/SKILL.md`, `scripts/skill-sync.sh`, `.claude/settings.local.json` 커밋 후 ax-eval + biz-plugins 양쪽 push
2. [ ] **하네스 진단 E2E**: `/ax-eval 체크` → 🔧 진단 블록이 레벨별 Tier 기능을 올바르게 표시하는지 확인
3. [x] **H2 구현**: `scripts/verify-e2e.sh` — 18/18 PASS 확인
4. [ ] **역할별 팁 E2E**: `/ax-eval 팁` → UA마케터/CRM마케터 역할별 Before→After 출력 확인

## 변경 이력 (최근 3건)

| 날짜 | 버전 | 내용 |
|------|------|------|
| 2026-04-14 | v1.5.0 | 하네스 엔지니어링 세팅 — PostToolUse skill-sync 훅 추가, settings.local.json permissions 정리, handoff.md 경량화 |
| 2026-04-10 | v1.5.0 | 하네스 진단 8개 기능 추가 — plan_mode/custom_skill/mcp 신호, harness_count 0~7, HARNESS_UNUSED Tier 필터, 🔧 진단 블록 |
| 2026-04-09 | v1.4.0 | 역할별 맞춤 팁 팀 배포, biz-plugins v1.4.0 push, `/ax-eval 체크` 종합 4.15점(⭐⭐⭐⭐ 주도) 확인 |
