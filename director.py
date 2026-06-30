"""Director logic for routing user work into the right office workflow."""

from crewai import Agent, Crew, LLM, Process, Task


WORK_MODES = {
    "research": "วิจัยและแนะนำ",
    "build": "สร้างโปรเจกต์ใหม่",
}


def build_director(llm: LLM) -> Agent:
    return Agent(
        role="ผู้อำนวยการออฟฟิศ AI (Director)",
        goal="รับคำสั่งจากผู้ใช้ วิเคราะห์เป้าหมาย และจัด brief ที่ชัดเจนให้ทีมทำงานต่อได้ทันที",
        backstory=(
            "คุณคือหัวหน้าทีม AI ที่เก่งทั้ง product, engineering และการสื่อสารกับผู้ใช้ไทย "
            "คุณไม่รีบตอบยาว แต่แปลงคำสั่งที่คลุมเครือให้เป็น brief ที่ทีมอื่นทำงานต่อได้ "
            "คุณระบุเป้าหมาย ขอบเขต สิ่งที่ต้องส่งมอบ ความเสี่ยง และลำดับงานเป็นภาษาไทยชัดเจน"
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )


def create_director_brief(user_request: str, mode_label: str, llm: LLM):
    director = build_director(llm)
    task = Task(
        description=(
            f'ผู้ใช้ต้องการงานประเภท "{mode_label}" โดยมีคำสั่งว่า:\n\n'
            f"{user_request}\n\n"
            "จงสร้าง brief ให้ทีมทำงานต่อ โดยระบุ:\n"
            "1. เป้าหมายหลัก\n"
            "2. ขอบเขตงาน\n"
            "3. ผู้ใช้ปลายทาง\n"
            "4. deliverables ที่ต้องส่งมอบ\n"
            "5. ความเสี่ยง/ข้อควรระวัง\n"
            "6. ลำดับการทำงานที่แนะนำ"
        ),
        expected_output=(
            "Director Brief ภาษาไทยในรูป Markdown ที่กระชับ ชัดเจน และใช้เป็น context ให้ทีมถัดไปได้ทันที"
        ),
        agent=director,
    )
    crew = Crew(
        agents=[director],
        tasks=[task],
        process=Process.sequential,
        verbose=True,
    )
    return crew.kickoff()
