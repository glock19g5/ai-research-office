"""Streamlit UI for AI Research Office."""

import importlib

import streamlit as st

import config
import project_writer
from build_runner import run_build_crew
from crew_runner import run_research_crew
from director import WORK_MODES, create_director_brief
from quick_runner import run_quick_workflow

config = importlib.reload(config)
project_writer = importlib.reload(project_writer)


st.set_page_config(
    page_title="🤖 AI Research Office",
    page_icon="🧠",
    layout="wide",
)


RESEARCH_AGENT_KEYS = [
    ("info_hunter", "🔍 Info Hunter"),
    ("summarizer", "📝 Summarizer"),
    ("comparison_builder", "📊 Comparator"),
    ("decision_advisor", "🎯 Advisor"),
    ("fact_checker", "✅ Fact Checker"),
]

BUILD_AGENT_KEYS = [
    ("product_planner", "📌 Product Planner"),
    ("system_architect", "🏛️ Architect"),
    ("developer", "💻 Developer"),
    ("tester", "🧪 Tester"),
    ("delivery_reporter", "📦 Delivery Reporter"),
]

SESSION_KEY_PREFIX = "session_api_key_"


def provider_index(provider: str) -> int:
    return list(config.MODEL_CATALOG.keys()).index(provider)


def model_index(provider: str, model: str) -> int:
    options = config.MODEL_CATALOG[provider]
    return options.index(model) if model in options else 0


def render_model_picker(key_prefix: str, label: str, default_provider: str, default_model: str):
    provider = st.selectbox(
        f"{label} provider",
        options=list(config.MODEL_CATALOG.keys()),
        index=provider_index(default_provider),
        key=f"{key_prefix}_provider",
    )
    model_options = config.MODEL_CATALOG[provider]
    model = st.selectbox(
        f"{label} model",
        options=model_options,
        index=model_index(provider, default_model),
        key=f"{key_prefix}_model",
    )
    custom_model = st.text_input(
        f"{label} custom model id",
        value="",
        key=f"{key_prefix}_custom_model",
        placeholder="เว้นว่างเพื่อใช้ model จาก dropdown",
    )
    return provider, custom_model.strip() or model


def session_api_key(provider: str) -> str | None:
    value = st.session_state.get(f"{SESSION_KEY_PREFIX}{provider}", "")
    return value.strip() or None


def effective_api_key(provider: str) -> str | None:
    return session_api_key(provider) or config.get_api_key(provider)


def build_llm_map(model_settings: dict[str, tuple[str, str]]):
    llms = {}
    missing_keys = []

    for key, (provider, model) in model_settings.items():
        api_key = effective_api_key(provider)
        if not api_key:
            missing_keys.append((provider, config.PROVIDER_API_KEYS[provider]))
            continue
        llms[key] = config.get_llm(provider, model, api_key=api_key)

    if missing_keys:
        missing_text = "\n".join(
            f"- {provider}: ต้องตั้งค่า `{env_name}`" for provider, env_name in sorted(set(missing_keys))
        )
        raise ValueError(f"ยังขาด API key สำหรับ provider ที่เลือก:\n{missing_text}")

    return llms


def selected_providers(model_settings: dict[str, tuple[str, str]]) -> set[str]:
    return {provider for provider, _model in model_settings.values()}


def missing_provider_keys(providers: set[str]) -> list[tuple[str, str]]:
    return [
        (provider, config.PROVIDER_API_KEYS[provider])
        for provider in sorted(providers)
        if not effective_api_key(provider)
    ]


def require_login() -> None:
    app_password = config.get_app_password()
    if not app_password:
        return

    if st.session_state.get("authenticated"):
        return

    st.title("🔐 AI Research Office")
    password = st.text_input("รหัสเข้าใช้งาน", type="password")
    if st.button("เข้าสู่ระบบ"):
        if password == app_password:
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("รหัสไม่ถูกต้อง")
    st.stop()


require_login()

st.title("🧠 AI Research Office")
st.caption("ทีมเอเจนต์ AI ช่วยวิจัย วางแผน และเตรียมสร้างโปรเจกต์ — เลือกโมเดลแยกตามทีมได้")


with st.sidebar:
    st.header("⚙️ การตั้งค่า")
    default_provider, default_model = render_model_picker(
        "default",
        "โมเดลหลัก",
        config.DEFAULT_PROVIDER,
        config.DEFAULT_MODEL,
    )
    st.caption(
        "ตั้ง API key เป็น environment variable เช่น "
        "`GEMINI_API_KEY`, `OPENAI_API_KEY`, หรือ `ANTHROPIC_API_KEY`"
    )
    with st.expander("🔑 สถานะ API keys", expanded=False):
        for provider, env_name in config.PROVIDER_API_KEYS.items():
            if session_api_key(provider):
                st.success(f"{provider}: ใช้ key ของผู้ใช้นี้")
            elif config.get_api_key(provider):
                st.success(f"{provider}: พบ `{env_name}` จาก server")
            else:
                st.warning(f"{provider}: ยังไม่พบ key")

    with st.expander("🔐 API keys ของผู้ใช้นี้", expanded=False):
        st.caption("key ที่กรอกตรงนี้ใช้เฉพาะ session นี้ ไม่เขียนลงไฟล์ .env")
        for provider in config.PROVIDER_API_KEYS:
            st.text_input(
                provider,
                type="password",
                key=f"{SESSION_KEY_PREFIX}{provider}",
                placeholder="วาง API key ของคุณเอง",
            )
        if st.button("ล้าง API keys ใน session นี้"):
            for provider in config.PROVIDER_API_KEYS:
                st.session_state[f"{SESSION_KEY_PREFIX}{provider}"] = ""
            st.rerun()

    advanced_models = st.checkbox("เลือกโมเดลแยกต่อ agent", value=False)
    economy_mode = st.checkbox(
        "โหมดประหยัด quota",
        value=True,
        help="ใช้ agent เดียวต่อหนึ่งงาน เหมาะกับ free tier หรือช่วงโดน rate limit",
    )
    write_files_mode = st.checkbox(
        "สร้างไฟล์โปรเจกต์จริงจากผลลัพธ์ Build",
        value=False,
        help="เขียนไฟล์จาก Markdown code blocks ลง generated_projects เฉพาะโหมดสร้างโปรเจกต์",
    )

    director_provider = default_provider
    director_model = default_model
    research_model_settings = {"default": (default_provider, default_model)}
    build_model_settings = {"default": (default_provider, default_model)}

    if advanced_models:
        with st.expander("🧭 Director model", expanded=False):
            director_provider, director_model = render_model_picker(
                "director",
                "Director",
                default_provider,
                default_model,
            )
        with st.expander("👥 Research team models", expanded=False):
            for agent_key, agent_label in RESEARCH_AGENT_KEYS:
                provider, model = render_model_picker(
                    f"research_{agent_key}",
                    agent_label,
                    default_provider,
                    default_model,
                )
                research_model_settings[agent_key] = (provider, model)
        with st.expander("🏗️ Build team models", expanded=False):
            for agent_key, agent_label in BUILD_AGENT_KEYS:
                provider, model = render_model_picker(
                    f"build_{agent_key}",
                    agent_label,
                    default_provider,
                    default_model,
                )
                build_model_settings[agent_key] = (provider, model)

    st.divider()
    st.markdown("### 👥 ทีม Research")
    st.markdown(
        "1. 🔍 **Info Hunter** — รวบรวมข้อมูล\n"
        "2. 📝 **Summarizer** — สรุป insight\n"
        "3. 📊 **Comparator** — สร้างตารางเปรียบเทียบ\n"
        "4. 🎯 **Advisor** — ให้คำแนะนำ\n"
        "5. ✅ **Fact Checker** — ตรวจสอบและเรียบเรียง"
    )
    st.divider()
    st.markdown("### 🏗️ ทีม Build")
    st.markdown(
        "1. 🧭 **Director** — รับคำสั่งและจัด brief\n"
        "2. 📌 **Product Planner** — แตก requirement\n"
        "3. 🏛️ **Architect** — วาง stack และโครงสร้าง\n"
        "4. 💻 **Developer** — เตรียม implementation\n"
        "5. 🧪 **Tester** — ตรวจความพร้อมส่งมอบ"
    )


mode_label = st.radio(
    "เลือกประเภทงาน",
    options=list(WORK_MODES.values()),
    horizontal=True,
)
mode_key = next(key for key, value in WORK_MODES.items() if value == mode_label)

input_label = "📝 หัวข้อที่ต้องการวิจัย" if mode_key == "research" else "🛠️ โปรเจกต์ที่อยากให้ AI ช่วยสร้าง"
input_placeholder = (
    "เช่น 'แท็บเล็ตที่เหมาะกับเด็กอายุ 8 ขวบในปี 2026'"
    if mode_key == "research"
    else "เช่น 'สร้างเว็บ landing page สำหรับร้านรถเช่า พร้อมฟอร์มติดต่อ'"
)

user_input = st.text_input(
    input_label,
    placeholder=input_placeholder,
)


with st.expander("💡 ตัวอย่างหัวข้อ"):
    if mode_key == "research":
        examples = [
            "ระบบรถเช่าออนไลน์สำหรับร้านขนาดเล็กในไทย",
            "เปรียบเทียบ Next.js vs Astro สำหรับเว็บไซต์ marketing",
            "วิธีโปรโมต TikTok shop สำหรับสินค้าอาหารแช่แข็ง",
            "Local LLM (Ollama) vs Cloud API สำหรับ dev solo",
        ]
    else:
        examples = [
            "สร้างเว็บ landing page สำหรับร้านรถเช่า พร้อมฟอร์มติดต่อ",
            "สร้างแอป Streamlit สำหรับบันทึกรายรับรายจ่ายส่วนตัว",
            "สร้าง dashboard วิเคราะห์ยอดขายจากไฟล์ CSV",
            "สร้างเว็บ portfolio นักออกแบบ พร้อมหน้า project gallery",
        ]
    cols = st.columns(2)
    for i, example in enumerate(examples):
        with cols[i % 2]:
            if st.button(example, key=f"ex_{i}", use_container_width=True):
                st.session_state["user_input"] = example
                st.rerun()

if "user_input" in st.session_state:
    user_input = st.session_state.pop("user_input")
    st.info(f"📌 คำสั่งที่เลือก: **{user_input}**")


run_button_label = "🚀 เริ่มการวิจัย" if mode_key == "research" else "🏗️ เริ่มวางแผนสร้างโปรเจกต์"

if st.button(run_button_label, type="primary", use_container_width=True):
    if not user_input.strip():
        st.warning("⚠️ กรุณากรอกคำสั่งก่อนครับ")
    else:
        try:
            active_settings = research_model_settings if mode_key == "research" else build_model_settings
            required_providers = selected_providers(active_settings) | {director_provider}
            missing_keys = missing_provider_keys(required_providers)
            if missing_keys:
                missing_text = "\n".join(
                    f"- {provider}: ต้องตั้งค่า `{env_name}`" for provider, env_name in missing_keys
                )
                raise ValueError(f"ยังขาด API key สำหรับ provider ที่เลือก:\n{missing_text}")

            with st.status("🤖 ทีมเอเจนต์กำลังทำงาน...", expanded=True) as status:
                st.write(f"📌 คำสั่ง: **{user_input}**")
                st.write(f"🧭 โหมด: **{mode_label}**")
                st.write(f"🧠 โมเดลหลัก: `{default_provider} / {default_model}`")
                st.write(f"💸 ประหยัด quota: `{'เปิด' if economy_mode else 'ปิด'}`")
                st.write("---")
                director_llm = build_llm_map({"director": (director_provider, director_model)})["director"]
                team_llms = build_llm_map(active_settings)

                if economy_mode:
                    st.write("⏳ AI Office Lead กำลังทำงานแบบประหยัด quota...")
                    result = run_quick_workflow(user_input, mode_label, director_llm)
                    director_brief = "โหมดประหยัด quota: ข้าม Director brief แยกขั้น เพื่อลดจำนวน API requests"
                    result_title = "⚡ ผลลัพธ์แบบประหยัด quota"
                    download_prefix = "quick"
                    agent_labels = ["⚡ AI Office Lead"]

                elif mode_key == "research":
                    st.write("⏳ Director กำลังอ่านคำสั่งและจัด brief...")
                    director_result = create_director_brief(user_input, mode_label, director_llm)
                    director_brief = getattr(director_result, "raw", str(director_result))
                    st.write("✅ Director brief พร้อมแล้ว")
                    st.write("⏳ Info Hunter กำลังค้นข้อมูล...")
                    st.write("⏳ Summarizer กำลังสรุป...")
                    st.write("⏳ Comparator กำลังสร้างตาราง...")
                    st.write("⏳ Advisor กำลังให้คำแนะนำ...")
                    st.write("⏳ Fact Checker กำลังตรวจสอบและเรียบเรียง...")
                    st.caption("💡 ใช้เวลาประมาณ 30-90 วินาที ขึ้นกับโมเดลและความยาว")
                    result = run_research_crew(user_input, team_llms, director_brief=director_brief)
                    result_title = "📊 รายงานผลการวิจัย"
                    download_prefix = "research"
                    agent_labels = [
                        "🔍 Info Hunter",
                        "📝 Summarizer",
                        "📊 Comparator",
                        "🎯 Advisor",
                        "✅ Fact Checker",
                    ]
                else:
                    st.write("⏳ Director กำลังอ่านคำสั่งและจัด brief...")
                    director_result = create_director_brief(user_input, mode_label, director_llm)
                    director_brief = getattr(director_result, "raw", str(director_result))
                    st.write("✅ Director brief พร้อมแล้ว")
                    st.write("⏳ Product Planner กำลังแตก requirement...")
                    st.write("⏳ Architect กำลังวาง stack และโครงสร้างไฟล์...")
                    st.write("⏳ Developer กำลังเตรียม implementation package...")
                    st.write("⏳ Tester กำลังตรวจความพร้อมส่งมอบ...")
                    st.write("⏳ Delivery Reporter กำลังเรียบเรียงรายงานสุดท้าย...")
                    st.caption("💡 เวอร์ชันนี้ยังเป็น build package ใน Markdown ก่อน ขั้นถัดไปจะให้สร้างไฟล์จริง")
                    result = run_build_crew(user_input, director_brief, team_llms)
                    result_title = "🏗️ แพ็กเกจสร้างโปรเจกต์"
                    download_prefix = "build"
                    agent_labels = [
                        "📌 Product Planner",
                        "🏛️ Architect",
                        "💻 Developer",
                        "🧪 Tester",
                        "📦 Delivery Reporter",
                    ]

                status.update(label="✅ งานเสร็จสมบูรณ์!", state="complete", expanded=False)

            st.success("🎯 งานพร้อมแล้ว!")

            with st.expander("🧭 Director Brief", expanded=False):
                st.markdown(director_brief)

            final_output = getattr(result, "raw", str(result))
            st.markdown(f"## {result_title}")
            st.markdown(final_output)

            if mode_key == "build" and write_files_mode:
                project_dir, generated_files = project_writer.write_project_files(user_input, final_output)
                st.success(f"สร้างไฟล์โปรเจกต์แล้ว: `{project_dir}`")
                if generated_files:
                    st.markdown("### 📁 ไฟล์ที่สร้าง")
                    for generated_file in generated_files:
                        st.code(generated_file.path)
                else:
                    st.warning(
                        "ยังไม่พบ code block ที่มีชื่อไฟล์ชัดเจน จึงบันทึกเฉพาะ AI_BUILD_REPORT.md"
                    )

            tasks_output = getattr(result, "tasks_output", None)
            if tasks_output:
                st.divider()
                st.markdown("### 🔬 เบื้องหลัง: ผลลัพธ์จากแต่ละเอเจนต์")
                for i, task_out in enumerate(tasks_output):
                    label = agent_labels[i] if i < len(agent_labels) else f"Task {i + 1}"
                    with st.expander(label):
                        st.markdown(getattr(task_out, "raw", str(task_out)))

            st.download_button(
                "💾 ดาวน์โหลดผลลัพธ์ (.md)",
                data=str(final_output),
                file_name=f"{download_prefix}_{user_input[:30].replace(' ', '_')}.md",
                mime="text/markdown",
            )

        except Exception as exc:
            st.error(f"❌ เกิดข้อผิดพลาด: {type(exc).__name__}")
            st.error(str(exc))
            with st.expander("รายละเอียด error"):
                st.code(f"{type(exc).__name__}: {exc!s}")
            st.info(
                "💡 ลองตรวจ:\n"
                "1. เลือก provider ให้ตรงกับ API key ที่ตั้งไว้\n"
                "2. API key ยังไม่หมด quota และบัญชีมีสิทธิ์ใช้ model id ที่เลือก\n"
                "3. ถ้าใช้ custom model id ให้สะกดตรงกับเอกสารของ provider"
            )


st.divider()
st.markdown("## 📚 Project Gallery")
projects = project_writer.list_generated_projects()

if not projects:
    st.info("ยังไม่มีโปรเจกต์ที่สร้างไฟล์จริง เปิด `สร้างไฟล์โปรเจกต์จริงจากผลลัพธ์ Build` แล้วรัน Build Mode ก่อนครับ")
else:
    project_names = [
        f"{project.name} — {project.modified_at.strftime('%Y-%m-%d %H:%M')} — {len(project.files)} files"
        for project in projects
    ]
    selected_project_label = st.selectbox("เลือกโปรเจกต์", options=project_names)
    selected_project = projects[project_names.index(selected_project_label)]

    st.caption(f"โฟลเดอร์: `{selected_project.path}`")

    with st.expander("✏️ แก้ข้อมูลโปรเจกต์", expanded=False):
        edit_tab_team, edit_tab_site = st.tabs(["ทีมงาน", "ข้อความเว็บ"])
        with edit_tab_team:
            team_name = st.text_input(
                "เปลี่ยนชื่อทีมงานทั้งหมด",
                value="นาย ชลธิศ จริยะสุนทรดี",
                key=f"team_name_{selected_project.name}",
            )
            if st.button("บันทึกชื่อทีมงานทั้งหมด", key=f"save_team_{selected_project.name}"):
                changed_count = project_writer.update_team_member_names(selected_project, team_name.strip())
                if changed_count:
                    st.success(f"เปลี่ยนชื่อทีมงานแล้ว {changed_count} จุด")
                    st.rerun()
                else:
                    st.warning("ไม่พบข้อมูล teamMembers ใน script.js ของโปรเจกต์นี้")

        with edit_tab_site:
            site_content = project_writer.read_site_content(selected_project)
            page_title = st.text_input("Page title", value=site_content.page_title, key=f"title_{selected_project.name}")
            brand_name = st.text_input("Brand / Header", value=site_content.brand_name, key=f"brand_{selected_project.name}")
            hero_title = st.text_input("Hero title", value=site_content.hero_title, key=f"hero_title_{selected_project.name}")
            hero_text_1 = st.text_area("Hero paragraph 1", value=site_content.hero_text_1, key=f"hero_p1_{selected_project.name}")
            hero_text_2 = st.text_area("Hero paragraph 2", value=site_content.hero_text_2, key=f"hero_p2_{selected_project.name}")
            contact_email = st.text_input("Contact email", value=site_content.contact_email, key=f"email_{selected_project.name}")
            contact_phone = st.text_input("Contact phone", value=site_content.contact_phone, key=f"phone_{selected_project.name}")
            contact_address = st.text_area("Contact address", value=site_content.contact_address, key=f"addr_{selected_project.name}")

            if st.button("บันทึกข้อความเว็บ", key=f"save_site_{selected_project.name}"):
                ok = project_writer.update_site_content(
                    selected_project,
                    project_writer.SiteContent(
                        page_title=page_title.strip(),
                        brand_name=brand_name.strip(),
                        hero_title=hero_title.strip(),
                        hero_text_1=hero_text_1.strip(),
                        hero_text_2=hero_text_2.strip(),
                        contact_email=contact_email.strip(),
                        contact_phone=contact_phone.strip(),
                        contact_address=contact_address.strip(),
                    ),
                )
                if ok:
                    st.success("บันทึกข้อความเว็บแล้ว")
                    st.rerun()
                else:
                    st.warning("ไม่พบ index.html สำหรับโปรเจกต์นี้")

    preview_html = project_writer.find_preview_html(selected_project)

    if preview_html:
        preview_url = project_writer.html_data_url(preview_html)
        st.markdown("### 🖥️ Preview")
        st.caption(f"ไฟล์ preview: `{project_writer.relative_project_file(selected_project, preview_html)}`")
        st.link_button("เปิด preview ในแท็บใหม่", preview_url)
        st.components.v1.iframe(preview_url, height=520, scrolling=True)
    else:
        st.info("โปรเจกต์นี้ยังไม่มีไฟล์ HTML สำหรับ preview")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### ไฟล์ในโปรเจกต์")
        for path in selected_project.files:
            st.code(project_writer.relative_project_file(selected_project, path))

    with col2:
        preview_options = [
            project_writer.relative_project_file(selected_project, path)
            for path in selected_project.files
            if path.suffix.lower() in {".md", ".html", ".css", ".js", ".py", ".txt", ".json"}
        ]
        if preview_options:
            selected_file_name = st.selectbox("ดูตัวอย่างไฟล์", options=preview_options)
            selected_file = selected_project.path / selected_file_name
            content = selected_file.read_text(encoding="utf-8", errors="replace")
            suffix = selected_file.suffix.lower().lstrip(".") or "text"
            st.download_button(
                "ดาวน์โหลดไฟล์นี้",
                data=content,
                file_name=selected_file.name,
                mime="text/plain",
            )
            if suffix == "md":
                st.markdown(content)
            else:
                st.code(content, language=suffix)
        else:
            st.info("โปรเจกต์นี้ยังไม่มีไฟล์ที่ preview ได้")
