"""Crew setup and execution for AI Research Office."""

from crewai import Crew, LLM, Process, Task

from agents import build_agents


def run_research_crew(topic: str, llm: LLM | dict[str, LLM], director_brief: str | None = None):
    hunter, summarizer, comparator, advisor, checker = build_agents(llm)
    brief_context = f"Director brief:\n{director_brief}\n\n" if director_brief else ""

    task1 = Task(
        description=(
            brief_context
            + f'ค้นหาข้อมูลเชิงลึกเกี่ยวกับ "{topic}" อย่างน้อย 5-8 ประเด็นหลัก '
            "ครอบคลุม: นิยาม/ภาพรวม, ตัวเลขสำคัญ, แนวโน้ม, ทางเลือกที่มี, "
            "และข้อโต้แย้งหรือความเสี่ยง ระบุแหล่งอ้างอิงถ้าทำได้"
        ),
        expected_output=(
            "รายการข้อมูลดิบ 5-8 ประเด็น แต่ละประเด็นมี: หัวข้อย่อย, รายละเอียด 2-4 บรรทัด, "
            "และ source (ถ้ามี) — เขียนเป็นภาษาไทยทั้งหมด"
        ),
        agent=hunter,
    )

    task2 = Task(
        description=(
            f'สรุปข้อมูลจาก task ก่อนหน้าเกี่ยวกับ "{topic}" '
            "โดยเน้นเฉพาะ insight ที่นำไปตัดสินใจหรือใช้งานได้จริง ตัดเนื้อหาที่เป็น 'น่ารู้แต่ไม่จำเป็น' ออก"
        ),
        expected_output=(
            "สรุป 3-5 ย่อหน้าเป็นภาษาไทย ครอบคลุม: ภาพรวม, ประเด็นสำคัญที่สุด 3 ข้อ, "
            "และ implications ที่ผู้ใช้ควรรู้"
        ),
        agent=summarizer,
        context=[task1],
    )

    task3 = Task(
        description=(
            f'สร้างตารางเปรียบเทียบ Markdown เกี่ยวกับ "{topic}" จากข้อมูลที่สรุปมา '
            "เลือกเกณฑ์เปรียบเทียบ 4-6 เกณฑ์ที่สำคัญต่อการตัดสินใจ "
            "(เช่น ราคา, คุณภาพ, ความง่ายในการใช้, ความเสี่ยง, ROI ฯลฯ)"
        ),
        expected_output=(
            "ตาราง Markdown ที่มีอย่างน้อย 3 ทางเลือก × 4-6 เกณฑ์ "
            "ใช้ ✅ ❌ ⚠️ ประกอบ และมีคำอธิบายตารางสั้นๆ ใต้ตาราง — ภาษาไทย"
        ),
        agent=comparator,
        context=[task1, task2],
    )

    task4 = Task(
        description=(
            f'จากข้อมูลและตารางทั้งหมด ให้คำแนะนำสุดท้ายว่า "{topic}" ควรตัดสินใจอย่างไร '
            "ฟันธงให้ชัด พร้อมเหตุผล 3-5 ข้อ และระบุข้อควรระวัง"
        ),
        expected_output=(
            "คำแนะนำเชิงกลยุทธ์ภาษาไทย ประกอบด้วย: 1) คำตอบฟันธง 1 ประโยค "
            "2) เหตุผลสนับสนุน 3-5 ข้อ 3) ความเสี่ยง/ข้อควรระวัง 4) Next steps ที่ทำได้ทันที"
        ),
        agent=advisor,
        context=[task2, task3],
    )

    task5 = Task(
        description=(
            f'ตรวจสอบข้อเท็จจริงในงานก่อนหน้าทั้งหมดเกี่ยวกับ "{topic}" '
            "ใส่ ⚠️ ตรงข้อมูลที่ยังไม่แน่ชัด แล้วเรียบเรียงเป็นรายงานสุดท้ายในรูป Markdown"
        ),
        expected_output=(
            "รายงานฉบับสมบูรณ์ภาษาไทยในรูปแบบ Markdown มีโครงสร้าง:\n"
            "# หัวข้อรายงาน\n"
            "## 📋 สรุปผู้บริหาร (Executive Summary)\n"
            "## 🔍 ข้อมูลเชิงลึก\n"
            "## 📊 ตารางเปรียบเทียบ\n"
            "## 🎯 คำแนะนำ\n"
            "## ⚠️ ข้อควรระวัง\n"
            "## 🚀 ขั้นตอนต่อไป"
        ),
        agent=checker,
        context=[task1, task2, task3, task4],
    )

    crew = Crew(
        agents=[hunter, summarizer, comparator, advisor, checker],
        tasks=[task1, task2, task3, task4, task5],
        process=Process.sequential,
        verbose=True,
    )

    return crew.kickoff()
