---
applyTo: "db/migrations/**"
---
- `docs/standards/db-migration-guide.md` 를 따른다: 확장 → 전환 → 축소, 파괴적 변경 금지, 새 컬럼은 NULL 허용 또는 DEFAULT.
- 파일명은 다음 번호로 `NNN_설명.sql`. 이미 있는 파일은 수정하지 않는다.
- 직전 릴리스(구버전 앱)가 새 스키마에서도 동작해야 한다.
