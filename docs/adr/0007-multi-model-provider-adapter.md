# D-007 — Multi-model ผ่าน provider adapter/policy

- ADR: 0007
- Decision ID: D-007
- สถานะ: Accepted
- วันที่: 2026-07-04
- อ้างอิง: AIO-1.1-BLUEPRINT-v1.2, AIO-1.1-DECISIONLOG-CONFIRM-2026-07-04

## บริบท (Context)
ต้องรองรับหลาย provider โดยไม่ผูกโค้ดกับ SDK ตัวใดตัวหนึ่ง

## การตัดสินใจ (Decision)
ทุกการเรียกโมเดลผ่าน provider adapter + policy กลาง (Model Gateway) แยก provider config ออกจาก agent config

## ผลที่ตามมา (Consequences)
สลับ provider ได้ยืดหยุ่น; business logic ห้ามเรียก SDK ตรง (บังคับโดย D-016)
