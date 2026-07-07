# D-016 — OpenAI เป็น Approved Provider ผ่าน Model Gateway

- ADR: 0016
- Decision ID: D-016
- สถานะ: Accepted (2026-07-03)
- วันที่: 2026-07-04
- อ้างอิง: AIO-1.1-BLUEPRINT-v1.2, AIO-1.1-DECISIONLOG-CONFIRM-2026-07-04

## บริบท (Context)
ต้องมี provider ที่อนุมัติใช้งานผ่าน Gateway อย่างเป็นทางการสำหรับ MVP

## การตัดสินใจ (Decision)
OpenAI เป็น Approved Provider โดย: Public/Internal อนุญาต, Confidential ต้อง policy check, Personal block, Secret ห้าม; บังคับ store=false; MVP ไม่ใช้ file/fine-tuning endpoints; มี kill switch ใน tool_connections; ทบทวนทุก 6 เดือน; ยังไม่กำหนด primary/backup (ตัดสิน Phase 2 หลัง eval ภาษาไทย)

## ผลที่ตามมา (Consequences)
ทุก provider เรียกผ่าน Model Gateway เท่านั้น ห้าม business logic เรียก SDK ตรง; Gateway บังคับ policy/logging/redaction/timeout/retry/kill switch; provider config แยกจาก agent config
