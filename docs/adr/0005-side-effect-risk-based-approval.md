# D-005 — Side effect ผ่าน risk-based approval

- ADR: 0005
- Decision ID: D-005
- สถานะ: Accepted
- วันที่: 2026-07-04
- อ้างอิง: AIO-1.1-BLUEPRINT-v1.2, AIO-1.1-DECISIONLOG-CONFIRM-2026-07-04

## บริบท (Context)
การกระทำที่มีผลข้างเคียงจริง (ส่งอีเมล, เขียนไฟล์, จ่ายเงิน) ต้องมีการอนุมัติตามความเสี่ยง

## การตัดสินใจ (Decision)
ทุก side effect ผ่านชั้น approval แบบ risk-based; action ความเสี่ยงต่ำ auto-approve ได้ตามรายการที่กำหนด, สูงต้องอนุมัติ

## ผลที่ตามมา (Consequences)
ปลอดภัยขึ้น; ต้องมี approval state machine + idempotency (WB-B.4/B.5)
