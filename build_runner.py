"""Build-mode Crew setup and execution."""

from crewai import Crew, LLM, Process, Task

from build_agents import build_build_agents


def run_build_crew(user_request: str, director_brief: str, llm: LLM | dict[str, LLM]):
    planner, architect, developer, tester, reporter = build_build_agents(llm)

    task1 = Task(
        description=(
            f"Director brief:\n{director_brief}\n\n"
            f"คำสั่งผู้ใช้:\n{user_request}\n\n"
            "จงแปลงเป็น Product Requirements Document สำหรับ MVP"
        ),
        expected_output=(
            "PRD ภาษาไทย มี: เป้าหมาย, ผู้ใช้, user stories, feature list, non-goals, acceptance criteria"
        ),
        agent=planner,
    )

    task2 = Task(
        description=(
            "จาก PRD ก่อนหน้า จงออกแบบสถาปัตยกรรมสำหรับโปรเจกต์ MVP "
            "เลือก stack ที่เหมาะสมที่สุดและอธิบายเหตุผลแบบกระชับ"
        ),
        expected_output=(
            "Architecture plan ภาษาไทย มี stack, file tree, data flow, dependencies, commands ที่ต้องใช้"
        ),
        agent=architect,
        context=[task1],
    )

    task3 = Task(
        description=(
            "จาก PRD และ architecture plan จงสร้าง implementation package "
            "โดยให้โค้ดไฟล์สำคัญเป็น Markdown code blocks และระบุชื่อไฟล์เหนือแต่ละบล็อก "
            "เน้น MVP ที่รันได้จริง ไม่ต้องทำฟีเจอร์เกินจำเป็น\n\n"
            "สำคัญมาก: โค้ดแต่ละไฟล์ต้องใช้รูปแบบนี้เท่านั้น เพื่อให้ระบบสร้างไฟล์จริงได้:\n"
            "### path/to/file.ext\n"
            "```language\n"
            "content\n"
            "```"
        ),
        expected_output=(
            "Implementation package ภาษาไทย มี file tree, โค้ดไฟล์หลัก, requirements/package dependencies, วิธีรัน"
        ),
        agent=developer,
        context=[task1, task2],
    )

    task4 = Task(
        description=(
            "ตรวจ implementation package ก่อนหน้าเหมือนกำลังจะส่งมอบให้ผู้ใช้ "
            "หาจุดเสี่ยง สิ่งที่ขาด dependency ที่อาจลืม และคำสั่งทดสอบที่ควรมี"
        ),
        expected_output=(
            "QA review ภาษาไทย มี passed checks, issues, fixes ที่แนะนำ, test commands, residual risks"
        ),
        agent=tester,
        context=[task1, task2, task3],
    )

    task5 = Task(
        description=(
            "เรียบเรียงงานทั้งหมดเป็นเอกสารส่งมอบสุดท้ายสำหรับผู้ใช้ "
            "ให้ชัดว่าต้องสร้างไฟล์อะไร วางโค้ดตรงไหน รันอย่างไร และพัฒนาต่ออะไร"
        ),
        expected_output=(
            "Build Report ภาษาไทยใน Markdown มี Executive Summary, File Tree, Key Code, Run Steps, Test Steps, Next Iteration"
        ),
        agent=reporter,
        context=[task1, task2, task3, task4],
    )

    crew = Crew(
        agents=[planner, architect, developer, tester, reporter],
        tasks=[task1, task2, task3, task4, task5],
        process=Process.sequential,
        verbose=True,
    )

    return crew.kickoff()
