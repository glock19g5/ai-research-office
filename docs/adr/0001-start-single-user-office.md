# D-001 — เริ่มจาก AI Research Office สำหรับผู้ใช้หนึ่งคน

- ADR: 0001
- Decision ID: D-001
- สถานะ: Accepted
- วันที่: 2026-07-04
- อ้างอิง: AIO-1.1-BLUEPRINT-v1.2, AIO-1.1-DECISIONLOG-CONFIRM-2026-07-04

## บริบท (Context)
ต้องเลือกขอบเขต MVP ให้เล็กพอจะส่งมอบได้จริง ก่อนขยายเป็น multi-tenant/หลายผู้ใช้

## การตัดสินใจ (Decision)
MVP ตั้งเป้าผู้ใช้คนเดียว (single-user) แต่ออกแบบ schema ให้มี workspace_id ตั้งแต่แรกเพื่อรองรับ multi-tenant ภายหลัง

## ผลที่ตามมา (Consequences)
ลดความซับซ้อนช่วงแรก; ยังต้องบังคับ RLS ผูก workspace_id แม้ผู้ใช้คนเดียว เพื่อกัน leakage ในอนาคต
