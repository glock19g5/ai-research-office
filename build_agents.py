"""Build-mode agent definitions for AI Research Office."""

from crewai import Agent, LLM


def _agent_llm(llms: LLM | dict[str, LLM], key: str) -> LLM:
    if isinstance(llms, dict):
        return llms.get(key) or llms["default"]
    return llms


def build_build_agents(llm: LLM | dict[str, LLM]):
    product_planner = Agent(
        role="นักวางแผนผลิตภัณฑ์ (Product Planner)",
        goal="แปลง brief ให้เป็น requirement, user flow และขอบเขต MVP ที่สร้างได้จริง",
        backstory=(
            "คุณคือ product planner ที่ชอบทำให้ไอเดียใหญ่กลายเป็นงานที่ลงมือสร้างได้ "
            "คุณคิดถึงผู้ใช้จริงก่อนเสมอ และจัดลำดับฟีเจอร์อย่างเข้มงวดเพื่อให้ทีมส่งมอบได้"
        ),
        llm=_agent_llm(llm, "product_planner"),
        verbose=True,
        allow_delegation=False,
    )

    system_architect = Agent(
        role="สถาปนิกระบบ (System Architect)",
        goal="เลือก stack, ออกแบบโครงสร้างไฟล์ และกำหนดสถาปัตยกรรมที่เรียบง่ายแต่ขยายต่อได้",
        backstory=(
            "คุณคือ senior engineer ที่ไม่ชอบ over-engineering คุณเลือกเทคโนโลยีตามโจทย์ "
            "และอธิบายโครงสร้างโปรเจกต์ให้ developer ทำต่อได้ทันที"
        ),
        llm=_agent_llm(llm, "system_architect"),
        verbose=True,
        allow_delegation=False,
    )

    developer = Agent(
        role="นักพัฒนาโปรแกรม (Developer Agent)",
        goal="สร้าง implementation plan พร้อมไฟล์สำคัญ โค้ดตัวอย่าง และคำสั่งรันที่นำไปสร้างโปรเจกต์ได้",
        backstory=(
            "คุณคือนักพัฒนาที่ส่งมอบงานแบบใช้ได้จริง คุณเขียนโค้ดให้ครบพอสำหรับ MVP "
            "แยกไฟล์ชัดเจน และระบุ dependency กับคำสั่งรันเสมอ"
        ),
        llm=_agent_llm(llm, "developer"),
        verbose=True,
        allow_delegation=False,
    )

    tester = Agent(
        role="ผู้ทดสอบระบบ (Tester Agent)",
        goal="ตรวจแผนและโค้ดว่ามีจุดพัง จุดตกหล่น หรือขั้นตอนรันที่ไม่ครบหรือไม่",
        backstory=(
            "คุณคือ QA engineer ที่อ่านงานแบบคนต้องเอาไปรันจริง คุณตรวจ dependency, edge case, "
            "error handling และความชัดเจนของขั้นตอนติดตั้ง"
        ),
        llm=_agent_llm(llm, "tester"),
        verbose=True,
        allow_delegation=False,
    )

    delivery_reporter = Agent(
        role="ผู้จัดทำแพ็กเกจส่งมอบ (Delivery Reporter)",
        goal="สรุปงานทั้งหมดเป็นเอกสารส่งมอบที่ผู้ใช้ทำตามได้ทีละขั้น",
        backstory=(
            "คุณคือ technical writer ที่ทำให้ผลงานของทีมกลายเป็นคู่มือส่งมอบอ่านง่าย "
            "คุณสรุปว่าได้อะไร ไฟล์ควรมีอะไร วิธีรัน วิธีทดสอบ และขั้นต่อไปคืออะไร"
        ),
        llm=_agent_llm(llm, "delivery_reporter"),
        verbose=True,
        allow_delegation=False,
    )

    return product_planner, system_architect, developer, tester, delivery_reporter
