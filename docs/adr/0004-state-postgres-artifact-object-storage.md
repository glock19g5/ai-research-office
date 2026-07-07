# D-004 — Domain state ใน PostgreSQL; artifact ใน Object Storage

- ADR: 0004
- Decision ID: D-004
- สถานะ: Accepted
- วันที่: 2026-07-04
- อ้างอิง: AIO-1.1-BLUEPRINT-v1.2, AIO-1.1-DECISIONLOG-CONFIRM-2026-07-04

## บริบท (Context)
ต้องแยกที่เก็บ state เชิงสัมพันธ์กับไฟล์ artifact ขนาดใหญ่

## การตัดสินใจ (Decision)
Domain state (projects/tasks/approvals ฯลฯ) เก็บใน PostgreSQL (Supabase); artifact ไฟล์เก็บใน Object Storage พร้อมอ้างอิงใน DB

## ผลที่ตามมา (Consequences)
รองรับ query/RLS/consistency บน state; artifact ต้องมี versioning (D ที่เกี่ยวข้อง WB-B.4); flat-file ของ repo เดิมถูกทิ้ง
