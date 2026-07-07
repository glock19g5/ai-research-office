# D-006 — ข้อมูลต้อง classification ก่อนเข้า Model Gateway

- ADR: 0006
- Decision ID: D-006
- สถานะ: Accepted
- วันที่: 2026-07-04
- อ้างอิง: AIO-1.1-BLUEPRINT-v1.2, AIO-1.1-DECISIONLOG-CONFIRM-2026-07-04

## บริบท (Context)
ข้อมูลต่างระดับความอ่อนไหวไม่ควรถูกส่งเข้าโมเดลอย่างเท่ากัน

## การตัดสินใจ (Decision)
ข้อมูลต้องถูกจัดชั้น (Public/Internal/Confidential/Personal/Secret) ก่อนส่งผ่าน Model Gateway; Secret ห้ามส่ง, Personal block, Confidential ต้อง policy check

## ผลที่ตามมา (Consequences)
ลดความเสี่ยงข้อมูลรั่วสู่ provider; ต้องมี classification + redaction ใน Gateway (เชื่อม D-016)
