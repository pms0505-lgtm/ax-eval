# ax-eval 핸드오프

> 다음 세션 시작 시 이 파일부터 읽을 것.

## Resume Block

- Last session: 2026-04-14 (5축 정리력 도입 + v2.0.0 배포)
- Last commit: `d4aab05` feat: add 5th axis 정리력 (asset-building) — v2.0.0
- Verification: ✅ verify-e2e.sh 31/32 PASS | ✅ ax-eval push | ✅ biz-plugins push | ⏳ 플러그인 재설치 미완 (캐시 1.3.0)
- Next action: `claude plugins update ax-eval@biz-plugins` 실행 → Claude Code 재시작 → `/ax-eval 체크` E2E
- Blockers: 없음

## 프로젝트 상태

| 항목 | 내용 |
|------|------|
| 버전 | v2.0.0 |
| 상태 | 배포 완료 (ax-eval `d4aab05` + biz-plugins `b7d73dd`) |
| 리포 | https://github.com/pms0505-lgtm/ax-eval |
| 마켓플레이스 | https://github.com/pms0505-lgtm/biz-plugins |

## 다음 세션 TODO

1. [ ] **플러그인 재설치**: `claude plugins update ax-eval@biz-plugins` → verify-e2e.sh 32/32 PASS 확인
2. [ ] **5축 E2E**: `/ax-eval 체크` → 정리력 행 + 📚 ASSET_BLOCK 출력 확인
3. [ ] **팁 E2E**: `/ax-eval 팁` → 정리력 낮을 때 자산 쌓기 가이드 출력 확인
4. [ ] **팀원 업데이트**: `claude plugins update ax-eval@biz-plugins` 안내 (major 업데이트)

## 변경 이력 (최근 3건)

| 날짜 | 버전 | 내용 |
|------|------|------|
| 2026-04-14 | v2.0.0 | 5축 정리력 도입 — extract_asset_signals, ASSET_BLOCK, 역할별 5열 가중치, 하네스 보너스 축소, verify-e2e 31항목 |
| 2026-04-14 | v1.5.0 | 하네스 엔지니어링 — PostToolUse skill-sync 훅, verify-e2e.sh(18항목), settings.local.json 정리 |
| 2026-04-10 | v1.5.0 | 하네스 진단 8개 기능 추가 — plan_mode/custom_skill/mcp 신호, harness_count 0~7, HARNESS_UNUSED Tier 필터 |
