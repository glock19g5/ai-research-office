# D-003 — Critical workflow ควบคุมด้วย code/state machine

- ADR: 0003
- Decision ID: D-003
- สถานะ: Accepted
- วันที่: 2026-07-04
- อ้างอิง: AIO-1.1-BLUEPRINT-v1.2, AIO-1.1-DECISIONLOG-CONFIRM-2026-07-04

## บริบท (Context)
workflow สำคัญถ้าปล่อยให้ LLM ตัดสินล้วนจะไม่แน่นอนและตรวจสอบยาก

## การตัดสินใจ (Decision)
workflow วิกฤต (task lifecycle, approval) ควบคุมด้วย code + state machine ที่ transition ผิดกฎถูก reject

## ผลที่ตามมา (Consequences)
ได้ determinism และ audit ที่ชัด; ต้องเขียน state machine + unit test (WB-B.1)
