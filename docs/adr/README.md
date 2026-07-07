# Architecture Decision Records (ADR) — AIO-1.1 baseline

- Baseline: AIO-1.1-BLUEPRINT-v1.2 (Architecture Baseline)
- ที่มา: AIO-1.1-DECISIONLOG-CONFIRM-2026-07-04 (D-001–D-016)
- WB: WB-0.2 (Milestone 0)

| Decision | หัวข้อ | สถานะ |
|----------|--------|-------|
| [D-001](0001-start-single-user-office.md) | เริ่มจาก AI Research Office สำหรับผู้ใช้หนึ่งคน | Accepted |
| [D-002](0002-office-manager-plus-skills.md) | ใช้ Office Manager หนึ่งตัว + Skills ใน MVP | Accepted |
| [D-003](0003-critical-workflow-code-state-machine.md) | Critical workflow ควบคุมด้วย code/state machine | Accepted |
| [D-004](0004-state-postgres-artifact-object-storage.md) | Domain state ใน PostgreSQL; artifact ใน Object Storage | Accepted |
| [D-005](0005-side-effect-risk-based-approval.md) | Side effect ผ่าน risk-based approval | Accepted |
| [D-006](0006-classify-before-model-gateway.md) | ข้อมูลต้อง classification ก่อนเข้า Model Gateway | Accepted |
| [D-007](0007-multi-model-provider-adapter.md) | Multi-model ผ่าน provider adapter/policy | Accepted |
| [D-008](0008-mcp-behind-registry-manifest-threatmodel.md) | MCP หลัง Tool Registry, Permission Manifest และ Threat Model | Accepted |
| [D-009](0009-virtual-office-as-renderer.md) | Virtual Office เป็น Renderer | Accepted |
| [D-010](0010-crewai-provisional.md) | CrewAI ใช้แบบ provisional | Accepted |
| [D-011](0011-golden-dataset-phase2.md) | Golden Dataset เริ่มใน Phase 2 | Accepted |
| [D-012](0012-backup-restore-provider-exit.md) | Backup, restore test และ provider exit plan เป็นข้อกำหนดฐาน | Accepted |
| [D-013](0013-workblock-real-hours.md) | Roadmap ใช้ Work Block/ชั่วโมงทำงานจริง | Accepted |
| [D-014](0014-env-separation.md) | Environment แยก Development/Staging/Production | Accepted |
| [D-015](0015-new-agent-needs-eval-evidence.md) | Agent ใหม่ต้องมีหลักฐานจาก Evaluation | Accepted |
| [D-016](0016-openai-approved-provider.md) | OpenAI เป็น Approved Provider ผ่าน Model Gateway | Accepted (2026-07-03) |

> Blueprint v1.2 (`AI_Office_1_1_Master_Blueprint_TH_v1_2.docx`) ถือเป็น Architecture Baseline
> ควบคู่กับ ADR ชุดนี้ — เป็น source of truth เชิงสถาปัตยกรรมของโครงการ
