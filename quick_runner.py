"""Single-call workflows for quota-saving runs."""

from crewai import Agent, Crew, LLM, Process, Task


def run_quick_workflow(user_request: str, mode_label: str, llm: LLM):
    quick_agent = Agent(
        role="AI Office Lead แบบประหยัด quota",
        goal="ตอบงานของผู้ใช้ให้ครบที่สุดในครั้งเดียว โดยรวมบทบาท Director, Planner, Developer และ Reviewer",
        backstory=(
            "คุณคือหัวหน้าทีม AI ที่ต้องทำงานในโหมดประหยัด quota จึงต้องคิดให้รอบในคำตอบเดียว "
            "คุณเขียนภาษาไทยชัดเจน ใช้ Markdown และให้ output ที่ผู้ใช้เอาไปทำต่อได้ทันที"
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )

    task = Task(
        description=(
            f'ผู้ใช้เลือกโหมด "{mode_label}" และสั่งว่า:\n\n'
            f"{user_request}\n\n"
            "จงทำงานให้ครบในคำตอบเดียว ถ้าเป็นงานวิจัยให้มีสรุป ข้อมูลสำคัญ ตาราง คำแนะนำ "
            "และข้อควรระวัง ถ้าเป็นงานสร้างโปรเจกต์ให้มี PRD, architecture, file tree, "
            "โค้ด/ไฟล์หลักที่ควรมี, วิธีรัน, วิธีทดสอบ และขั้นต่อไป\n\n"
            "ถ้าเป็นงานสร้างโปรเจกต์ โค้ดแต่ละไฟล์ต้องใช้รูปแบบนี้เท่านั้น:\n"
            "### path/to/file.ext\n"
            "```language\n"
            "content\n"
            "```"
        ),
        expected_output=(
            "รายงาน Markdown ภาษาไทยที่ครบพอสำหรับการตัดสินใจหรือเริ่มสร้างงานต่อ โดยใช้ token อย่างคุ้มค่า"
        ),
        agent=quick_agent,
    )

    crew = Crew(
        agents=[quick_agent],
        tasks=[task],
        process=Process.sequential,
        verbose=True,
    )

    return crew.kickoff()
