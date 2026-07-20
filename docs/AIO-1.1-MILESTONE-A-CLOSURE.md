# AIO-1.1 — Milestone A Closure Record

- รหัส: AIO-1.1-MILESTONE-A-CLOSURE
- วันที่ปิด: 20 กรกฎาคม 2026
- Branch: v1.1-foundation (ยังไม่ merge เข้า main)
- อ้างอิง: Blueprint v1.2 บทที่ 6, 10, 12, 14 | D-001, D-004, D-005, D-012, D-014, D-016

## สถานะ: Milestone 0 + A ปิดครบ

| Milestone | Work Block | SHA |
|---|---|---|
| 0 | WB-0.1/0.2/0.3 audit + ADR + FastAPI/CI | a1b7cce |
| A | WB-A.1 Supabase dev + secret separation | e5c1f51 |
| A | WB-A.2 core schema (4 ตาราง) | 7cc6e6a |
| A | WB-A.3 audit/flow schema (4 ตาราง) | af46b12 |
| A | WB-A.4 agent/ops schema (8 ตาราง) | 8e2ab7e |
| A | WB-A.5 RLS policies + leakage test | 0f2dd05 |

## ผลลัพธ์ที่ตรวจสอบแล้ว

- **16 ตาราง** ใน Supabase dev (project: aio-dev, org: aioffice-newtion, region: Singapore)
- **60 RLS policies** = 14 ตาราง x 4 (select/insert/update/delete) + events/audit_logs x 2 (append-only)
- **Migration 5 ไฟล์** ใน backend/migrations/ (0001-0005) — schema ทั้งหมด reproduce ได้
- **CI เขียว** (backend-ci, pytest ผ่านบน GitHub Actions)
- **ไม่มี secret ใน repo** — .env, .venv, check_connection.py ถูก git ignore ยืนยันด้วย git check-ignore

## Evidence: RLS Leakage Test (AC ของ WB-A.5)

| ทดสอบ | ผล | เกณฑ์ |
|---|---|---|
| Intruder (ไม่ใช่เจ้าของ) มองเห็น workspaces/projects/tasks | 0 / 0 / 0 | ต้อง = 0 |
| Owner (เจ้าของ) มองเห็น workspaces/projects/tasks | 1 / 1 / 1 | ต้อง > 0 |

สรุป: **cross-workspace leakage = 0** -> Phase 1 Exit Criteria ข้อ 2 ผ่าน
(ข้อมูลทดสอบและ user ทดสอบถูกลบหมดหลังทดสอบ; ตรวจแล้วเหลือ 0 แถวทุกตาราง)

## สถาปัตยกรรม RLS

จุดตัดสินใจสิทธิ์เดียว: function `public.is_workspace_member(ws_id uuid)`
- workspaces -> created_by = auth.uid()
- อีก 15 ตาราง -> ผูกผ่าน workspace_id
- events + audit_logs -> SELECT/INSERT เท่านั้น = append-only บังคับที่ระดับ database

เหตุผล: วันหน้าถ้าเปลี่ยนเป็น multi-user แก้ที่ function เดียว ไม่ต้องเขียน 60 policy ใหม่ (anti-lock-in)

## ข้อจำกัดที่รับรู้ (ยกไป Milestone B / บันทึกไว้)

1. **service_role key bypass RLS โดยธรรมชาติ** — RLS ชั้นนี้ป้องกันเส้นทาง anon/client
   ส่วนการคุมสิทธิ์ฝั่ง backend ต้องทำที่ application layer -> WB-B.3
2. **Supabase Free tier พัก project อัตโนมัติเมื่อ idle ~7 วัน** — ต้อง resume ก่อนทำงานทุกครั้ง
   ข้อมูลไม่หาย แต่กระทบจังหวะ Work Block ที่เว้นช่วง (เกี่ยวข้อง D-012)
3. **pgvector embedding บน knowledge_chunks ยังไม่ทำ** — เลื่อนไป RAG phase ตามแผน

## Phase 1 Exit Criteria — สถานะ

| # | เกณฑ์ | สถานะ | WB ที่รับผิดชอบ |
|---|---|---|---|
| 1 | ปิด/เปิดระบบแล้ว state ไม่หาย | รอ | WB-C.3 |
| 2 | RLS tests ผ่าน | **ผ่านแล้ว** | WB-A.5 |
| 3 | Restore test ผ่าน | รอ | WB-C.2 |
| 4 | Duplicate side effect = 0 | รอ | WB-B.5 + WB-C.3 |

## ก้าวต่อไป: Milestone B (Domain + State + API) ~5 WB

- WB-B.1 Domain models + state machine (Task 9 สถานะ, Approval 5 สถานะ) + unit test
- WB-B.2 Event append-only + correlation_id + audit
- WB-B.3 API CRUD Project/Task + permission check (p95 <= 2 วินาที)
- WB-B.4 Artifact versioning + Approval flow
- WB-B.5 Idempotency key -> Exit #4

หมายเหตุ: Milestone B เป็นการเขียนโค้ด Python จริงใน backend/app/ + pytest
(ต่างจาก A ที่เป็น SQL) ทุก WB ต้องมี test evidence ก่อนขึ้น WB ถัดไป
