# D-012 — Backup, restore test และ provider exit plan เป็นข้อกำหนดฐาน

- ADR: 0012
- Decision ID: D-012
- สถานะ: Accepted
- วันที่: 2026-07-04
- อ้างอิง: AIO-1.1-BLUEPRINT-v1.2, AIO-1.1-DECISIONLOG-CONFIRM-2026-07-04

## บริบท (Context)
ความน่าเชื่อถือและการไม่ผูกขาด provider เป็นข้อกำหนดพื้นฐาน

## การตัดสินใจ (Decision)
ต้องมี backup, การทดสอบ restore จริง และ provider exit plan เป็นเกณฑ์ฐาน (ไม่ใช่ optional)

## ผลที่ตามมา (Consequences)
รองรับ Exit #3 (restore test), RPO≤24ชม./RTO≤4ชม. (WB-C.*)
