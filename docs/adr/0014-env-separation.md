# D-014 — Environment แยก Development/Staging/Production

- ADR: 0014
- Decision ID: D-014
- สถานะ: Accepted
- วันที่: 2026-07-04
- อ้างอิง: AIO-1.1-BLUEPRINT-v1.2, AIO-1.1-DECISIONLOG-CONFIRM-2026-07-04

## บริบท (Context)
การพัฒนา ทดสอบ และใช้งานจริงต้องไม่ปนกัน โดยเฉพาะ secret

## การตัดสินใจ (Decision)
แยก 3 environment ชัดเจน; service role key/secret ไม่อยู่ใน repo/log/prompt และจัดเก็บใน Secret Manager/env

## ผลที่ตามมา (Consequences)
ลดความเสี่ยง secret รั่ว; บังคับที่ WB-A.1 (Secret = ห้ามอยู่ใน code)
