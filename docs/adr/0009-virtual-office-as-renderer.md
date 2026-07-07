# D-009 — Virtual Office เป็น Renderer

- ADR: 0009
- Decision ID: D-009
- สถานะ: Accepted
- วันที่: 2026-07-04
- อ้างอิง: AIO-1.1-BLUEPRINT-v1.2, AIO-1.1-DECISIONLOG-CONFIRM-2026-07-04

## บริบท (Context)
ส่วน Virtual Office/3D ไม่ควรถือ business logic

## การตัดสินใจ (Decision)
Virtual Office เป็นเพียง Renderer ของ state ที่ backend ถือ ไม่ใช่แหล่งความจริง

## ผลที่ตามมา (Consequences)
แยก concern ชัด; งาน 3D เป็น P0 ห้ามเริ่มใน Phase 1
