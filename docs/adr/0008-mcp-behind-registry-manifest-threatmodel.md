# D-008 — MCP หลัง Tool Registry, Permission Manifest และ Threat Model

- ADR: 0008
- Decision ID: D-008
- สถานะ: Accepted
- วันที่: 2026-07-04
- อ้างอิง: AIO-1.1-BLUEPRINT-v1.2, AIO-1.1-DECISIONLOG-CONFIRM-2026-07-04

## บริบท (Context)
การต่อเครื่องมือภายนอก (MCP) มีความเสี่ยงด้านสิทธิ์และความปลอดภัย

## การตัดสินใจ (Decision)
MCP ทุกตัวต้องขึ้นทะเบียนใน Tool Registry, มี Permission Manifest และผ่าน Threat Model ก่อนใช้งาน

## ผลที่ตามมา (Consequences)
ควบคุม tool surface ได้; เพิ่มงาน governance ก่อนเปิด integration write (P0 ห้ามข้าม)
