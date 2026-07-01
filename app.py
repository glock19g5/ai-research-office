"""Streamlit UI for AI Research Office."""

import io
import importlib
import re
from html import escape

import streamlit as st

import auth_store
import config
import project_writer
from build_runner import run_build_crew
from crew_runner import run_research_crew
from director import WORK_MODES, create_director_brief
from quick_runner import run_quick_workflow

config = importlib.reload(config)
project_writer = importlib.reload(project_writer)
auth_store = importlib.reload(auth_store)


st.set_page_config(
    page_title="🤖 AI Research Office",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        "About": "AI Research Office",
    },
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

OFFICE_AGENTS = [
    {
        "icon": "🧭",
        "name": "Director",
        "role": "รับคำสั่ง วางแผน และแจกงาน",
        "key": "director",
        "team": "Core",
        "color": "#67e8f9",
        "accent": "#f59e0b",
        "delay": "0s",
    },
    {
        "icon": "🔍",
        "name": "Researcher",
        "role": "ค้นข้อมูล วิเคราะห์ และสรุป insight",
        "key": "info_hunter",
        "team": "Research",
        "color": "#60a5fa",
        "accent": "#a78bfa",
        "delay": "-.8s",
    },
    {
        "icon": "📊",
        "name": "Analyst",
        "role": "เปรียบเทียบทางเลือกและทำตาราง",
        "key": "comparison_builder",
        "team": "Research",
        "color": "#34d399",
        "accent": "#fbbf24",
        "delay": "-1.5s",
    },
    {
        "icon": "🎯",
        "name": "Advisor",
        "role": "ฟันธงคำแนะนำและ next steps",
        "key": "decision_advisor",
        "team": "Research",
        "color": "#fb7185",
        "accent": "#f97316",
        "delay": "-2.2s",
    },
    {
        "icon": "📌",
        "name": "Planner",
        "role": "แตก requirement และ MVP scope",
        "key": "product_planner",
        "team": "Build",
        "color": "#c084fc",
        "accent": "#22d3ee",
        "delay": "-.4s",
    },
    {
        "icon": "🏛️",
        "name": "Architect",
        "role": "เลือก stack และวางโครงสร้างระบบ",
        "key": "system_architect",
        "team": "Build",
        "color": "#facc15",
        "accent": "#38bdf8",
        "delay": "-1.1s",
    },
    {
        "icon": "💻",
        "name": "Developer",
        "role": "เตรียมโค้ด ไฟล์ และวิธีรัน",
        "key": "developer",
        "team": "Build",
        "color": "#4ade80",
        "accent": "#818cf8",
        "delay": "-1.8s",
    },
    {
        "icon": "🧪",
        "name": "Tester",
        "role": "ตรวจความเสี่ยงและวิธีทดสอบ",
        "key": "tester",
        "team": "Build",
        "color": "#f472b6",
        "accent": "#2dd4bf",
        "delay": "-2.6s",
    },
]

SESSION_KEY_PREFIX = "session_api_key_"
MAX_CONTEXT_CHARS = 14000
MAX_FILE_CHARS = 7000


def apply_page_styles() -> None:
    st.markdown(
        """
        <style>
        #MainMenu, footer, [data-testid="stToolbar"], [data-testid="stDecoration"], header[data-testid="stHeader"] {
            display: none;
        }
        .block-container {
            padding-top: 2.2rem;
            padding-bottom: 2rem;
        }
        .app-header {
            padding: .4rem 0 1rem;
        }
        .app-title {
            margin: 0;
            font-size: clamp(2.2rem, 6vw, 3.6rem);
            line-height: 1.02;
            font-weight: 850;
            letter-spacing: 0;
        }
        .app-subtitle {
            max-width: 860px;
            margin-top: .65rem;
            color: rgba(250, 250, 250, .72);
            font-size: 1.05rem;
            line-height: 1.55;
        }
        .mobile-tip {
            display: none;
            margin: .75rem 0 1rem;
            border: 1px solid rgba(255, 255, 255, .12);
            border-radius: 8px;
            padding: .8rem;
            background: rgba(255, 255, 255, .04);
            color: rgba(250, 250, 250, .78);
            font-size: .95rem;
            line-height: 1.45;
        }
        .hero-wrap {
            padding: 2.5rem 0 1.5rem;
        }
        .hero-title {
            font-size: 3.1rem;
            line-height: 1.05;
            font-weight: 800;
            margin: 0 0 .7rem;
        }
        .hero-subtitle {
            max-width: 860px;
            font-size: 1.1rem;
            color: rgba(250, 250, 250, .72);
            margin-bottom: 1.3rem;
        }
        .login-hero {
            padding: 1.15rem 0 .8rem;
        }
        .login-hero .hero-title {
            font-size: clamp(2rem, 7vw, 3rem);
            margin-bottom: .45rem;
        }
        .login-hero .hero-subtitle {
            max-width: 680px;
            font-size: 1rem;
            line-height: 1.45;
            margin-bottom: .4rem;
        }
        .feature-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: .8rem;
            margin: 1.2rem 0 1.5rem;
        }
        .feature-card {
            border: 1px solid rgba(250, 250, 250, .12);
            border-radius: 8px;
            padding: 1rem;
            background: rgba(255, 255, 255, .035);
        }
        .feature-card strong {
            display: block;
            margin-bottom: .35rem;
        }
        .feature-card span {
            color: rgba(250, 250, 250, .68);
            font-size: .95rem;
        }
        .step-box {
            border-left: 3px solid #ff4b4b;
            padding: .65rem 0 .65rem 1rem;
            margin: .5rem 0;
            background: rgba(255, 75, 75, .06);
        }
        @media (max-width: 900px) {
            .block-container {
                padding: 1.1rem 1rem 1.5rem;
            }
            .app-header {
                padding-top: .15rem;
            }
            .app-title {
                font-size: clamp(2.05rem, 12vw, 3rem);
                line-height: 1.04;
            }
            .app-subtitle {
                font-size: 1rem;
                line-height: 1.45;
            }
            .mobile-tip {
                display: block;
            }
            div[data-testid="stExpander"] details summary p {
                font-size: 1rem;
            }
            div[data-testid="column"] {
                width: 100% !important;
                flex: 1 1 100% !important;
            }
            button[kind="primary"], button[kind="secondary"] {
                min-height: 3rem;
            }
            .feature-grid { grid-template-columns: 1fr; }
            .hero-wrap {
                padding: .7rem 0 .55rem;
            }
            .hero-title {
                font-size: clamp(1.7rem, 9vw, 2.35rem);
                line-height: 1.05;
                margin-bottom: .45rem;
            }
            .hero-subtitle {
                font-size: .96rem;
                line-height: 1.38;
                margin-bottom: .75rem;
            }
            .login-hero {
                padding: .35rem 0 .45rem;
            }
            .login-hero .hero-title {
                font-size: clamp(1.8rem, 10vw, 2.35rem);
                line-height: 1.03;
            }
            .login-hero .hero-subtitle {
                font-size: .95rem;
                line-height: 1.35;
            }
            .login-steps {
                display: none;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_landing(show_login: bool = False) -> None:
    hero_class = "hero-wrap login-hero" if show_login else "hero-wrap"
    subtitle = (
        "เข้าสู่ระบบหรือสมัครสมาชิก แล้วใส่ API key ของคุณเพื่อเริ่มใช้งาน"
        if show_login
        else (
            "พื้นที่ทำงาน AI สำหรับวิจัย วางแผน สร้างโปรเจกต์ และแปลงผลลัพธ์เป็นไฟล์จริง "
            "โดยผู้ใช้แต่ละคนสามารถใช้ API key ของตัวเองได้"
        )
    )
    st.markdown(
        f"""
        <div class="{hero_class}">
            <div class="hero-title">🧠 AI Research Office</div>
            <div class="hero-subtitle">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if show_login:
        st.markdown("### เข้าสู่ระบบ")
        return

    st.markdown(
        """
        <div class="feature-grid">
            <div class="feature-card"><strong>🔍 Research</strong><span>ช่วยสรุป วิเคราะห์ เปรียบเทียบ และให้คำแนะนำเป็นภาษาไทย</span></div>
            <div class="feature-card"><strong>🏗️ Build</strong><span>ช่วยวาง PRD, architecture, code package และสร้างไฟล์โปรเจกต์จริง</span></div>
            <div class="feature-card"><strong>🔐 Bring your key</strong><span>กรอก Gemini, OpenAI หรือ Claude key ของคุณเองใน session ส่วนตัว</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### วิธีเริ่มใช้งาน")
    st.markdown(
        """
        <div class="login-steps">
        <div class="step-box"><b>1.</b> สมัครสมาชิกหรือเข้าสู่ระบบด้วยบัญชีของคุณ</div>
        <div class="step-box"><b>2.</b> เปิด sidebar แล้วกรอก API key ของคุณใน <code>API keys ของผู้ใช้นี้</code></div>
        <div class="step-box"><b>3.</b> เลือกโหมด <code>วิจัยและแนะนำ</code> หรือ <code>สร้างโปรเจกต์ใหม่</code></div>
        <div class="step-box"><b>4.</b> เปิดโหมดประหยัด quota สำหรับการทดลอง หรือเลือกโมเดลแยกต่อ agent เมื่อพร้อม</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_app_header() -> None:
    st.markdown(
        """
        <div class="app-header">
            <div class="app-title">🧠 AI Research Office</div>
            <div class="app-subtitle">
                ทีมเอเจนต์ AI ช่วยวิจัย วางแผน และเตรียมสร้างโปรเจกต์ เลือกโมเดลแยกตามทีมได้
            </div>
        </div>
        <div class="mobile-tip">
            ใช้มือถือได้ง่ายขึ้น: กรอก API key ใน “ตั้งค่าด่วนสำหรับมือถือ” ด้านล่าง
            แล้วเลือกโหมดงานก่อนกดเริ่ม
        </div>
        """,
        unsafe_allow_html=True,
    )


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


def model_label_for_agent(
    agent_key: str,
    default_provider: str,
    default_model: str,
    research_model_settings: dict[str, tuple[str, str]],
    build_model_settings: dict[str, tuple[str, str]],
    director_provider: str,
    director_model: str,
) -> str:
    if agent_key == "director":
        return f"{director_provider} / {director_model}"
    if agent_key in research_model_settings:
        provider, model = research_model_settings[agent_key]
        return f"{provider} / {model}"
    if agent_key in build_model_settings:
        provider, model = build_model_settings[agent_key]
        return f"{provider} / {model}"
    return f"{default_provider} / {default_model}"


def render_agent_character(agent: dict[str, str], model_label: str) -> None:
    name = escape(agent["name"])
    role = escape(agent["role"])
    team = escape(agent["team"])
    icon = escape(agent["icon"])
    color = escape(agent["color"])
    accent = escape(agent["accent"])
    delay = escape(agent["delay"])
    model = escape(model_label)

    st.components.v1.html(
        f"""
        <!doctype html>
        <html>
        <head>
        <meta charset="utf-8" />
        <style>
            * {{
                box-sizing: border-box;
            }}
            body {{
                margin: 0;
                font-family: "Inter", "Segoe UI", sans-serif;
                background: transparent;
                color: #f8fafc;
            }}
            .agent-room {{
                height: 218px;
                overflow: hidden;
                border: 1px solid rgba(255, 255, 255, .14);
                border-radius: 8px;
                background:
                    linear-gradient(180deg, rgba(255,255,255,.06), rgba(255,255,255,.025)),
                    radial-gradient(circle at 12% 12%, {color}22, transparent 35%),
                    #111827;
                padding: 12px;
                position: relative;
            }}
            .stage {{
                height: 96px;
                overflow: hidden;
                border-radius: 7px;
                background:
                    linear-gradient(180deg, rgba(15, 23, 42, .12) 0%, rgba(15, 23, 42, .35) 58%, rgba(15, 23, 42, .72) 58%),
                    repeating-linear-gradient(90deg, rgba(255,255,255,.045) 0 1px, transparent 1px 22px);
                border: 1px solid rgba(255,255,255,.08);
                position: relative;
            }}
            .walker {{
                width: 72px;
                height: 82px;
                position: absolute;
                left: 7px;
                bottom: 7px;
                transform-origin: center bottom;
                animation: stroll 4.8s ease-in-out infinite alternate;
                animation-delay: {delay};
            }}
            .bot {{
                width: 54px;
                height: 78px;
                margin: 0 auto;
                position: relative;
                filter: drop-shadow(0 8px 8px rgba(0,0,0,.26));
                animation: bounce .58s ease-in-out infinite alternate;
            }}
            .head {{
                width: 38px;
                height: 34px;
                left: 8px;
                top: 0;
                border-radius: 8px;
                background: #f8d6ad;
                border: 3px solid rgba(15,23,42,.72);
                position: absolute;
            }}
            .hair {{
                position: absolute;
                width: 44px;
                height: 14px;
                left: 5px;
                top: -2px;
                border-radius: 7px 7px 3px 3px;
                background: {accent};
                border: 2px solid rgba(15,23,42,.72);
            }}
            .eye {{
                position: absolute;
                top: 14px;
                width: 5px;
                height: 5px;
                border-radius: 50%;
                background: #0f172a;
            }}
            .eye.left {{ left: 11px; }}
            .eye.right {{ right: 11px; }}
            .smile {{
                position: absolute;
                left: 14px;
                top: 22px;
                width: 10px;
                height: 5px;
                border-bottom: 2px solid #0f172a;
                border-radius: 0 0 8px 8px;
            }}
            .body {{
                width: 42px;
                height: 36px;
                left: 6px;
                top: 34px;
                border-radius: 6px;
                background: {color};
                border: 3px solid rgba(15,23,42,.72);
                position: absolute;
            }}
            .badge {{
                position: absolute;
                top: 8px;
                left: 13px;
                width: 16px;
                height: 16px;
                border-radius: 5px;
                display: grid;
                place-items: center;
                font-size: 10px;
                background: rgba(255,255,255,.82);
            }}
            .arm, .leg {{
                position: absolute;
                border: 3px solid rgba(15,23,42,.72);
                background: {accent};
                border-radius: 6px;
            }}
            .arm {{
                width: 12px;
                height: 31px;
                top: 38px;
                transform-origin: center top;
                animation: armSwing .58s ease-in-out infinite alternate;
            }}
            .arm.left {{ left: -2px; }}
            .arm.right {{
                right: -2px;
                animation-direction: alternate-reverse;
            }}
            .leg {{
                width: 15px;
                height: 22px;
                top: 64px;
                transform-origin: center top;
                animation: legSwing .58s ease-in-out infinite alternate;
            }}
            .leg.left {{ left: 10px; }}
            .leg.right {{
                right: 10px;
                animation-direction: alternate-reverse;
            }}
            .floor-dot {{
                position: absolute;
                bottom: 10px;
                width: 5px;
                height: 5px;
                border-radius: 50%;
                background: rgba(255,255,255,.22);
            }}
            .agent-name {{
                margin: 10px 0 2px;
                font-size: 18px;
                font-weight: 800;
                line-height: 1.1;
            }}
            .agent-role {{
                color: rgba(248,250,252,.72);
                font-size: 13px;
                min-height: 20px;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }}
            .meta {{
                color: rgba(248,250,252,.62);
                font-size: 12px;
                margin-top: 7px;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }}
            .status {{
                position: absolute;
                right: 12px;
                bottom: 12px;
                color: #86efac;
                border: 1px solid rgba(34,197,94,.4);
                background: rgba(34,197,94,.11);
                border-radius: 999px;
                padding: 4px 9px;
                font-size: 12px;
                font-weight: 700;
            }}
            @keyframes stroll {{
                0% {{ left: 7px; transform: scaleX(1); }}
                48% {{ left: calc(100% - 79px); transform: scaleX(1); }}
                52% {{ left: calc(100% - 79px); transform: scaleX(-1); }}
                100% {{ left: 7px; transform: scaleX(-1); }}
            }}
            @keyframes bounce {{
                from {{ transform: translateY(0); }}
                to {{ transform: translateY(-3px); }}
            }}
            @keyframes armSwing {{
                from {{ transform: rotate(18deg); }}
                to {{ transform: rotate(-18deg); }}
            }}
            @keyframes legSwing {{
                from {{ transform: rotate(-12deg); }}
                to {{ transform: rotate(12deg); }}
            }}
        </style>
        </head>
        <body>
            <div class="agent-room">
                <div class="stage">
                    <span class="floor-dot" style="left: 18%;"></span>
                    <span class="floor-dot" style="left: 48%;"></span>
                    <span class="floor-dot" style="left: 78%;"></span>
                    <div class="walker">
                        <div class="bot">
                            <div class="hair"></div>
                            <div class="head">
                                <span class="eye left"></span>
                                <span class="eye right"></span>
                                <span class="smile"></span>
                            </div>
                            <div class="arm left"></div>
                            <div class="arm right"></div>
                            <div class="body"><span class="badge">{icon}</span></div>
                            <div class="leg left"></div>
                            <div class="leg right"></div>
                        </div>
                    </div>
                </div>
                <div class="agent-name">{name}</div>
                <div class="agent-role">{role}</div>
                <div class="meta">ทีม: {team} | โมเดล: {model}</div>
                <div class="status">พร้อมรับงาน</div>
            </div>
        </body>
        </html>
        """,
        height=228,
        scrolling=False,
    )


def render_virtual_agent_office(
    default_provider: str,
    default_model: str,
    research_model_settings: dict[str, tuple[str, str]],
    build_model_settings: dict[str, tuple[str, str]],
    director_provider: str,
    director_model: str,
) -> None:
    desk_layout = [
        ("8%", "12%", "36vw", "140px", "ขอ brief"),
        ("34%", "9%", "12vw", "155px", "มีข้อมูลใหม่"),
        ("60%", "12%", "-8vw", "138px", "เทียบตัวเลือก"),
        ("79%", "30%", "-24vw", "40px", "ฟันธงได้"),
        ("8%", "55%", "36vw", "-70px", "แตก scope"),
        ("31%", "66%", "12vw", "-125px", "วางระบบ"),
        ("56%", "66%", "-8vw", "-126px", "เริ่ม build"),
        ("78%", "55%", "-24vw", "-72px", "ตรวจให้"),
    ]
    hair_shapes = [
        "spiky",
        "side",
        "cap",
        "wave",
        "bun",
        "flat",
        "visor",
        "curl",
    ]
    desks_html: list[str] = []
    agents_html: list[str] = []

    for index, agent in enumerate(OFFICE_AGENTS):
        x, y, mx, my, speech = desk_layout[index]
        model_label = model_label_for_agent(
            agent["key"],
            default_provider,
            default_model,
            research_model_settings,
            build_model_settings,
            director_provider,
            director_model,
        )
        name = escape(agent["name"])
        role = escape(agent["role"])
        team = escape(agent["team"])
        icon = escape(agent["icon"])
        color = escape(agent["color"])
        accent = escape(agent["accent"])
        model = escape(model_label)
        delay = f"-{index * 0.75:.2f}s"
        hair_shape = hair_shapes[index % len(hair_shapes)]
        desk_style = f"--x:{x};--y:{y};--c:{color};--a:{accent};"
        agent_style = f"--x:{x};--y:{y};--mx:{mx};--my:{my};--c:{color};--a:{accent};--delay:{delay};"

        desks_html.append(
            f"""
            <div class="desk desk-{index}" style="{desk_style}">
                <div class="chair"></div>
                <div class="desk-top"><span>{icon}</span></div>
                <div class="desk-label">{name}</div>
            </div>
            """
        )
        agents_html.append(
            f"""
            <div class="office-agent agent-{index}" style="{agent_style}" title="{name} | {team} | {model}">
                <div class="talk">{escape(speech)}</div>
                <div class="person">
                    <div class="hair {hair_shape}"></div>
                    <div class="head">
                        <span class="eye left"></span>
                        <span class="eye right"></span>
                        <span class="mouth"></span>
                    </div>
                    <div class="neck"></div>
                    <div class="arm left"></div>
                    <div class="arm right"></div>
                    <div class="torso"><span>{icon}</span></div>
                    <div class="leg left"></div>
                    <div class="leg right"></div>
                </div>
                <div class="name-tag">
                    <b>{name}</b>
                    <span>{role}</span>
                </div>
            </div>
            """
        )

    st.components.v1.html(
        f"""
        <!doctype html>
        <html>
        <head>
        <meta charset="utf-8" />
        <style>
            * {{
                box-sizing: border-box;
            }}
            body {{
                margin: 0;
                font-family: "Inter", "Segoe UI", sans-serif;
                color: #f8fafc;
                background: transparent;
            }}
            .office-shell {{
                min-height: 620px;
                border: 1px solid rgba(255,255,255,.45);
                border-radius: 8px;
                overflow: hidden;
                background:
                    radial-gradient(circle at 15% 12%, rgba(255,255,255,.72), transparent 24%),
                    radial-gradient(circle at 78% 18%, rgba(196,181,253,.38), transparent 22%),
                    linear-gradient(180deg, #ffd8e6, #f6bfd3);
                position: relative;
                box-shadow: inset 0 1px 0 rgba(255,255,255,.7);
            }}
            .office-title {{
                position: absolute;
                left: 16px;
                top: 14px;
                z-index: 8;
                font-weight: 850;
                font-size: 20px;
                color: #334155;
                text-shadow: 0 1px 0 rgba(255,255,255,.75);
            }}
            .office-subtitle {{
                position: absolute;
                left: 16px;
                top: 42px;
                z-index: 8;
                color: rgba(71,85,105,.72);
                font-size: 13px;
            }}
            .floor {{
                position: absolute;
                inset: 68px 16px 16px;
                border-radius: 8px;
                border: 1px solid rgba(255,255,255,.1);
                background:
                    linear-gradient(90deg, rgba(255,255,255,.3) 1px, transparent 1px),
                    linear-gradient(rgba(255,255,255,.3) 1px, transparent 1px),
                    linear-gradient(180deg, #fbe7ef, #efb9cd);
                background-size: 36px 36px;
                overflow: hidden;
            }}
            .meeting-room {{
                position: absolute;
                left: 34%;
                top: 28%;
                width: 32%;
                height: 26%;
                min-width: 190px;
                border: 1px solid rgba(255,255,255,.16);
                border-radius: 8px;
                background: rgba(255,255,255,.38);
                box-shadow: inset 0 1px 0 rgba(255,255,255,.72), 0 18px 26px rgba(148,63,101,.16);
            }}
            .meeting-room::before {{
                content: "ห้องประชุม";
                position: absolute;
                top: 8px;
                left: 12px;
                color: rgba(71,85,105,.74);
                font-size: 12px;
                font-weight: 700;
            }}
            .meeting-table {{
                position: absolute;
                left: 20%;
                top: 34%;
                width: 60%;
                height: 34%;
                border-radius: 999px;
                background: linear-gradient(180deg, #fff7fb, #f4a9c2);
                border: 3px solid rgba(255,255,255,.66);
                box-shadow: 0 14px 20px rgba(148,63,101,.18);
            }}
            .meeting-chair {{
                position: absolute;
                width: 24px;
                height: 18px;
                border-radius: 6px;
                background: rgba(255,255,255,.66);
            }}
            .chair-a {{ left: 23%; top: 22%; }}
            .chair-b {{ right: 23%; top: 22%; }}
            .chair-c {{ left: 23%; bottom: 18%; }}
            .chair-d {{ right: 23%; bottom: 18%; }}
            .path {{
                position: absolute;
                left: 16%;
                top: 48%;
                width: 68%;
                height: 2px;
                border-top: 2px dashed rgba(148,63,101,.26);
            }}
            .desk {{
                position: absolute;
                left: var(--x);
                top: var(--y);
                width: 118px;
                height: 88px;
                z-index: 2;
            }}
            .desk-top {{
                position: absolute;
                left: 18px;
                top: 18px;
                width: 78px;
                height: 42px;
                border-radius: 8px;
                display: grid;
                place-items: center;
                background: linear-gradient(180deg, #ffffff, var(--c));
                border: 3px solid rgba(255,255,255,.7);
                box-shadow: 0 10px 16px rgba(148,63,101,.18);
                font-size: 19px;
            }}
            .chair {{
                position: absolute;
                left: 42px;
                top: 56px;
                width: 32px;
                height: 24px;
                border-radius: 7px 7px 12px 12px;
                background: var(--a);
                border: 3px solid rgba(255,255,255,.7);
                box-shadow: inset 0 2px 0 rgba(255,255,255,.55), 0 8px 14px rgba(148,63,101,.14);
            }}
            .desk-label {{
                position: absolute;
                left: 0;
                top: 2px;
                max-width: 118px;
                padding: 2px 7px;
                border-radius: 999px;
                background: rgba(255,255,255,.72);
                color: rgba(71,85,105,.9);
                font-size: 11px;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }}
            .office-agent {{
                position: absolute;
                left: var(--x);
                top: var(--y);
                width: 96px;
                height: 142px;
                z-index: 6;
                animation: consult 9.5s ease-in-out infinite;
                animation-delay: var(--delay);
            }}
            .person {{
                position: absolute;
                left: 16px;
                top: 18px;
                width: 64px;
                height: 104px;
                filter: drop-shadow(0 12px 10px rgba(148,63,101,.24));
                animation: human-bob .62s ease-in-out infinite alternate;
            }}
            .head {{
                position: absolute;
                left: 4px;
                top: 0;
                width: 56px;
                height: 52px;
                border-radius: 22px 22px 20px 20px;
                background:
                    radial-gradient(circle at 32% 24%, rgba(255,255,255,.82), transparent 16%),
                    radial-gradient(circle at 70% 65%, #f1a983, transparent 32%),
                    linear-gradient(145deg, #ffe0c6, #f0b38d);
                border: 3px solid rgba(255,255,255,.86);
                box-shadow: inset -7px -9px 14px rgba(150,72,56,.18), inset 5px 6px 10px rgba(255,255,255,.42);
            }}
            .head::after {{
                content: "";
                position: absolute;
                left: 9px;
                top: 8px;
                width: 14px;
                height: 9px;
                border-radius: 50%;
                background: rgba(255,255,255,.68);
                transform: rotate(-25deg);
            }}
            .hair {{
                position: absolute;
                z-index: 2;
                background: linear-gradient(145deg, #7c3f22, var(--a));
                border: 2px solid rgba(255,255,255,.76);
                box-shadow: inset 0 3px 0 rgba(255,255,255,.25), 0 3px 8px rgba(95,43,23,.22);
            }}
            .hair.spiky {{
                left: 4px; top: -8px; width: 56px; height: 26px; border-radius: 20px 18px 9px 9px;
                clip-path: polygon(0 65%, 11% 18%, 23% 55%, 37% 0, 48% 56%, 63% 10%, 73% 58%, 90% 18%, 100% 66%, 100% 100%, 0 100%);
            }}
            .hair.round {{
                left: 5px; top: -4px; width: 54px; height: 23px; border-radius: 18px 18px 8px 8px;
            }}
            .hair.side {{
                left: 4px; top: -4px; width: 54px; height: 27px; border-radius: 18px 6px 18px 7px;
            }}
            .hair.cap {{
                left: 1px; top: -6px; width: 60px; height: 24px; border-radius: 20px 20px 6px 6px;
            }}
            .hair.wave {{
                left: 3px; top: -6px; width: 58px; height: 27px; border-radius: 50% 45% 20% 30%;
            }}
            .hair.bun {{
                left: 7px; top: -5px; width: 48px; height: 22px; border-radius: 16px;
            }}
            .hair.bun::after {{
                content: ""; position: absolute; right: -8px; top: 1px; width: 16px; height: 16px; border-radius: 50%; background: var(--a); border: 2px solid rgba(255,255,255,.76);
            }}
            .hair.flat {{
                left: 4px; top: -1px; width: 55px; height: 17px; border-radius: 7px 7px 12px 12px;
            }}
            .hair.visor {{
                left: 2px; top: -5px; width: 59px; height: 22px; border-radius: 19px 19px 5px 5px;
            }}
            .hair.visor::after {{
                content: ""; position: absolute; right: -12px; top: 8px; width: 18px; height: 6px; border-radius: 8px; background: var(--a); border: 2px solid rgba(255,255,255,.76);
            }}
            .hair.curl {{
                left: 4px; top: -7px; width: 55px; height: 27px; border-radius: 18px 18px 12px 12px;
            }}
            .eye {{
                position: absolute;
                top: 23px;
                width: 8px;
                height: 10px;
                border-radius: 50%;
                background: radial-gradient(circle at 33% 25%, #ffffff 0 18%, #111827 20% 100%);
            }}
            .eye.left {{ left: 15px; }}
            .eye.right {{ right: 15px; }}
            .mouth {{
                position: absolute;
                left: 22px;
                top: 36px;
                width: 12px;
                height: 6px;
                border-bottom: 2px solid #0f172a;
                border-radius: 0 0 10px 10px;
            }}
            .neck {{
                position: absolute;
                left: 27px;
                top: 50px;
                width: 10px;
                height: 7px;
                background: #f3c79f;
                border-left: 2px solid rgba(255,255,255,.45);
                border-right: 2px solid rgba(255,255,255,.45);
            }}
            .torso {{
                position: absolute;
                left: 13px;
                top: 56px;
                width: 38px;
                height: 31px;
                border-radius: 14px 14px 10px 10px;
                background:
                    radial-gradient(circle at 30% 25%, rgba(255,255,255,.95), transparent 18%),
                    linear-gradient(145deg, #ffffff, #f4f7fb);
                border: 3px solid rgba(255,255,255,.82);
                box-shadow: inset -5px -6px 10px rgba(71,85,105,.12), 0 8px 11px rgba(148,63,101,.16);
                display: grid;
                place-items: center;
                font-size: 14px;
            }}
            .torso span {{
                width: 20px;
                height: 20px;
                border-radius: 50%;
                display: grid;
                place-items: center;
                background: linear-gradient(145deg, var(--a), var(--c));
                box-shadow: inset 0 2px 0 rgba(255,255,255,.45);
            }}
            .arm, .leg {{
                position: absolute;
                background:
                    radial-gradient(circle at 35% 25%, rgba(255,255,255,.75), transparent 18%),
                    linear-gradient(145deg, #ffe0c6, #efad86);
                border: 3px solid rgba(255,255,255,.78);
                border-radius: 10px;
                transform-origin: center top;
            }}
            .arm {{
                top: 60px;
                width: 12px;
                height: 26px;
                animation: human-arm .62s ease-in-out infinite alternate;
            }}
            .arm.left {{ left: 7px; }}
            .arm.right {{ right: 7px; animation-direction: alternate-reverse; }}
            .leg {{
                top: 83px;
                width: 13px;
                height: 22px;
                animation: human-leg .62s ease-in-out infinite alternate;
            }}
            .leg.left {{ left: 18px; }}
            .leg.right {{ right: 18px; animation-direction: alternate-reverse; }}
            .name-tag {{
                position: absolute;
                left: -2px;
                top: 112px;
                width: 100px;
                border-radius: 8px;
                padding: 3px 5px;
                background: rgba(255,255,255,.78);
                border: 1px solid rgba(255,255,255,.62);
                text-align: center;
                box-shadow: 0 8px 12px rgba(148,63,101,.12);
            }}
            .name-tag b {{
                display: block;
                font-size: 11px;
                line-height: 1.15;
                color: #334155;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }}
            .name-tag span {{
                display: block;
                color: rgba(71,85,105,.7);
                font-size: 9px;
                line-height: 1.2;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }}
            .talk {{
                position: absolute;
                left: 10px;
                top: -4px;
                min-width: 60px;
                max-width: 104px;
                padding: 4px 7px;
                border-radius: 9px 9px 9px 2px;
                background: rgba(255,255,255,.94);
                color: #334155;
                font-size: 10px;
                font-weight: 750;
                opacity: 0;
                transform: translateY(6px);
                animation: speak 9.5s ease-in-out infinite;
                animation-delay: var(--delay);
                box-shadow: 0 8px 14px rgba(148,63,101,.16);
            }}
            @keyframes consult {{
                0%, 24% {{ transform: translate(0,0) scaleX(1); }}
                38%, 64% {{ transform: translate(var(--mx), var(--my)) scaleX(1); }}
                72% {{ transform: translate(var(--mx), var(--my)) scaleX(-1); }}
                100% {{ transform: translate(0,0) scaleX(-1); }}
            }}
            @keyframes speak {{
                0%, 34%, 70%, 100% {{ opacity: 0; transform: translateY(6px); }}
                42%, 60% {{ opacity: 1; transform: translateY(0); }}
            }}
            @keyframes human-bob {{
                from {{ transform: translateY(0) rotate(-1deg); }}
                to {{ transform: translateY(-4px) rotate(1deg); }}
            }}
            @keyframes human-arm {{
                from {{ transform: rotate(18deg); }}
                to {{ transform: rotate(-18deg); }}
            }}
            @keyframes human-leg {{
                from {{ transform: rotate(-11deg); }}
                to {{ transform: rotate(12deg); }}
            }}
            @media (max-width: 620px) {{
                .office-shell {{ min-height: 720px; }}
                .floor {{ inset: 64px 8px 10px; }}
                .office-title {{ font-size: 17px; left: 12px; }}
                .office-subtitle {{ font-size: 11px; left: 12px; }}
                .meeting-room {{ left: 22%; top: 34%; width: 56%; height: 22%; min-width: 0; }}
                .desk {{ transform: scale(.82); transform-origin: left top; }}
                .office-agent {{ transform-origin: left top; }}
                .name-tag span {{ display: none; }}
            }}
        </style>
        </head>
        <body>
            <div class="office-shell">
                <div class="office-title">AI Agent Virtual Office</div>
                <div class="office-subtitle">ทุกคนมีโต๊ะทำงาน และเดินเข้าห้องประชุมเพื่อปรึกษากัน</div>
                <div class="floor">
                    <div class="path"></div>
                    <div class="meeting-room">
                        <div class="meeting-table"></div>
                        <div class="meeting-chair chair-a"></div>
                        <div class="meeting-chair chair-b"></div>
                        <div class="meeting-chair chair-c"></div>
                        <div class="meeting-chair chair-d"></div>
                    </div>
                    {''.join(desks_html)}
                    {''.join(agents_html)}
                </div>
            </div>
        </body>
        </html>
        """,
        height=650,
        scrolling=False,
    )


def render_office_dashboard(
    default_provider: str,
    default_model: str,
    research_model_settings: dict[str, tuple[str, str]],
    build_model_settings: dict[str, tuple[str, str]],
    director_provider: str,
    director_model: str,
) -> None:
    projects = project_writer.list_generated_projects()
    generated_file_count = sum(len(project.files) for project in projects)
    ready_provider_count = sum(1 for provider in config.PROVIDER_API_KEYS if effective_api_key(provider))

    st.markdown("## 🏢 Office Dashboard")
    metric_cols = st.columns(4)
    metric_cols[0].metric("Agents", len(OFFICE_AGENTS))
    metric_cols[1].metric("Projects", len(projects))
    metric_cols[2].metric("Files", generated_file_count)
    metric_cols[3].metric("Providers", ready_provider_count)

    st.markdown("### ทีม Agent")
    render_virtual_agent_office(
        default_provider,
        default_model,
        research_model_settings,
        build_model_settings,
        director_provider,
        director_model,
    )

    with st.expander("รายชื่อ Agent และโมเดลที่ใช้", expanded=False):
        for agent in OFFICE_AGENTS:
            model_label = model_label_for_agent(
                agent["key"],
                default_provider,
                default_model,
                research_model_settings,
                build_model_settings,
                director_provider,
                director_model,
            )
            st.markdown(f"- {agent['icon']} **{agent['name']}** ({agent['team']}) — `{model_label}`")


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


def truncate_text(text: str, limit: int = MAX_FILE_CHARS) -> str:
    clean_text = text.strip()
    if len(clean_text) <= limit:
        return clean_text
    return clean_text[:limit].rstrip() + "\n\n...[ตัดข้อความบางส่วนเพื่อไม่ให้ prompt ยาวเกินไป]"


def extract_uploaded_text(uploaded_file) -> tuple[str, str]:
    name = uploaded_file.name
    suffix = name.rsplit(".", 1)[-1].lower() if "." in name else ""
    data = uploaded_file.getvalue()

    if suffix in {"txt", "md", "csv", "json", "py", "html", "css", "js", "xml", "yaml", "yml"}:
        text = data.decode("utf-8", errors="replace")
        return name, truncate_text(text)

    if suffix == "pdf":
        try:
            from pypdf import PdfReader

            reader = PdfReader(io.BytesIO(data))
            pages = [page.extract_text() or "" for page in reader.pages[:12]]
            text = "\n\n".join(page.strip() for page in pages if page.strip())
            return name, truncate_text(text or "อ่าน PDF แล้ว แต่ไม่พบข้อความที่ extract ได้")
        except Exception as exc:
            return name, f"อ่าน PDF ไม่สำเร็จ: {type(exc).__name__}: {exc}"

    if suffix == "docx":
        try:
            from docx import Document

            document = Document(io.BytesIO(data))
            text = "\n".join(paragraph.text for paragraph in document.paragraphs if paragraph.text.strip())
            return name, truncate_text(text or "อ่าน DOCX แล้ว แต่ไม่พบข้อความ")
        except Exception as exc:
            return name, f"อ่าน DOCX ไม่สำเร็จ: {type(exc).__name__}: {exc}"

    return name, f"แนบไฟล์แล้ว แต่ยังอ่านเนื้อหาไฟล์ชนิด .{suffix or 'unknown'} ไม่ได้โดยตรง"


def transcribe_audio(audio_file) -> str:
    api_key = effective_api_key("OpenAI / ChatGPT")
    if not api_key:
        return "แนบเสียงแล้ว แต่ยังไม่ได้ถอดเสียง เพราะยังไม่มี OpenAI API key"

    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        audio_bytes = audio_file.getvalue()
        file_name = getattr(audio_file, "name", "voice_input.wav") or "voice_input.wav"
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=(file_name, audio_bytes),
        )
        text = getattr(transcript, "text", str(transcript))
        return truncate_text(text, limit=4000)
    except Exception as exc:
        return f"ถอดเสียงไม่สำเร็จ: {type(exc).__name__}: {exc}"


def render_attachment_tools() -> str:
    context_blocks: list[str] = []

    with st.expander("📎 แนบไฟล์ / รูปภาพ / เสียงพูด", expanded=False):
        st.caption("ไฟล์ข้อความ, PDF, DOCX จะถูกอ่านเข้า prompt ส่วนรูปภาพจะแสดง preview และแนบข้อมูลไฟล์")

        uploaded_files = st.file_uploader(
            "แนบไฟล์ประกอบคำสั่ง",
            type=["txt", "md", "csv", "json", "py", "html", "css", "js", "pdf", "docx"],
            accept_multiple_files=True,
            key="context_files",
        )
        if uploaded_files:
            st.markdown("**ไฟล์ที่แนบ**")
            for uploaded_file in uploaded_files:
                file_name, file_text = extract_uploaded_text(uploaded_file)
                st.write(f"- {file_name}")
                context_blocks.append(f"## ไฟล์แนบ: {file_name}\n{file_text}")

        uploaded_images = st.file_uploader(
            "แนบรูปภาพ",
            type=["png", "jpg", "jpeg", "webp"],
            accept_multiple_files=True,
            key="context_images",
        )
        if uploaded_images:
            image_cols = st.columns(2)
            for index, image in enumerate(uploaded_images):
                with image_cols[index % 2]:
                    st.image(image, caption=image.name, use_container_width=True)
                context_blocks.append(
                    f"## รูปภาพแนบ: {image.name}\n"
                    f"- ชนิดไฟล์: {image.type or 'unknown'}\n"
                    f"- ขนาดไฟล์: {len(image.getvalue())} bytes\n"
                    "- หมายเหตุ: หากต้องการให้ AI วิเคราะห์รายละเอียดในภาพ ให้พิมพ์คำอธิบายภาพเพิ่มในคำสั่งหลัก"
                )

        audio_file = None
        if hasattr(st, "audio_input"):
            audio_file = st.audio_input("พูดแทนการพิมพ์", key="voice_input")
        else:
            audio_file = st.file_uploader(
                "อัปโหลดไฟล์เสียงแทนการพูด",
                type=["wav", "mp3", "m4a", "webm", "ogg"],
                key="voice_file",
            )

        if audio_file is not None:
            st.audio(audio_file)
            if st.button("ถอดเสียงเป็นคำสั่ง", use_container_width=True):
                st.session_state["voice_transcript"] = transcribe_audio(audio_file)
                st.rerun()

        voice_text = st.session_state.get("voice_transcript", "").strip()
        if voice_text:
            st.text_area("ข้อความจากเสียง", value=voice_text, height=120, key="voice_transcript_preview")
            context_blocks.append(f"## ข้อความจากเสียงพูด\n{voice_text}")

        if context_blocks:
            st.success(f"แนบข้อมูลแล้ว {len(context_blocks)} รายการ")

    combined_context = "\n\n".join(context_blocks)
    return truncate_text(combined_context, limit=MAX_CONTEXT_CHARS)


def combine_user_input(user_input: str, attachment_context: str) -> str:
    base_input = user_input.strip()
    if not attachment_context:
        return base_input

    return (
        f"{base_input}\n\n"
        "ข้อมูลประกอบจากไฟล์/รูปภาพ/เสียงที่ผู้ใช้แนบ:\n"
        f"{attachment_context}"
    )


def split_markdown_sections(markdown_text: str) -> list[tuple[str, str]]:
    sections: list[tuple[str, list[str]]] = []
    current_title = "ภาพรวม"
    current_lines: list[str] = []
    in_code_block = False

    for line in markdown_text.splitlines():
        if line.strip().startswith("```"):
            in_code_block = not in_code_block

        heading_match = None if in_code_block else re.match(r"^(#{1,3})\s+(.+?)\s*$", line)
        if heading_match:
            if current_lines:
                sections.append((current_title, current_lines))
            current_title = re.sub(r"[#*_`]", "", heading_match.group(2)).strip()[:90] or "หัวข้อ"
            current_lines = [line]
        else:
            current_lines.append(line)

    if current_lines:
        sections.append((current_title, current_lines))

    return [(title, "\n".join(lines).strip()) for title, lines in sections if "\n".join(lines).strip()]


def render_compact_markdown(title: str, markdown_text: str) -> None:
    st.markdown(f"## {title}")
    sections = split_markdown_sections(markdown_text)

    if len(sections) <= 1:
        with st.expander("เปิดอ่านผลลัพธ์ทั้งหมด", expanded=False):
            st.markdown(markdown_text)
        return

    st.caption("กดเปิดอ่านทีละหัวข้อ เพื่อลดความแน่นของหน้าแอป")
    for index, (section_title, section_body) in enumerate(sections, start=1):
        label = f"{index}. {section_title}"
        with st.expander(label, expanded=False):
            st.markdown(section_body)


def require_login() -> None:
    if st.session_state.get("authenticated_user"):
        return

    render_landing(show_login=True)
    login_tab, register_tab = st.tabs(["เข้าสู่ระบบ", "สมัครสมาชิก"])

    with login_tab:
        username = st.text_input("ชื่อผู้ใช้", key="login_username")
        password = st.text_input("รหัสผ่าน", type="password", key="login_password")
        if st.button("เข้าสู่ระบบ", key="login_button"):
            result = auth_store.authenticate(username, password)
            if result.ok:
                st.session_state["authenticated_user"] = result.message
                st.success("เข้าสู่ระบบสำเร็จ")
                st.rerun()
            else:
                st.error(result.message)

    with register_tab:
        invite_password = config.get_app_password()
        if auth_store.user_count() == 0:
            st.info("ยังไม่มีผู้ใช้ในระบบ บัญชีแรกที่สมัครจะเป็นบัญชีแรกของแอปนี้")
        if invite_password:
            invite_code = st.text_input("รหัสเชิญสมัครสมาชิก", type="password", key="invite_code")
        else:
            invite_code = ""
            st.caption("ระบบนี้เปิดให้สมัครสมาชิกได้โดยไม่ต้องใช้รหัสเชิญ")

        new_username = st.text_input("ชื่อผู้ใช้ใหม่", key="register_username")
        new_password = st.text_input("รหัสผ่านใหม่", type="password", key="register_password")
        confirm_password = st.text_input("ยืนยันรหัสผ่าน", type="password", key="register_confirm_password")

        if st.button("สมัครสมาชิก", key="register_button"):
            if invite_password and invite_code != invite_password:
                st.error("รหัสเชิญสมัครสมาชิกไม่ถูกต้อง")
            elif new_password != confirm_password:
                st.error("รหัสผ่านยืนยันไม่ตรงกัน")
            else:
                result = auth_store.create_user(new_username, new_password)
                if result.ok:
                    st.session_state["authenticated_user"] = new_username.strip().lower()
                    st.success(result.message)
                    st.rerun()
                else:
                    st.error(result.message)
    st.stop()


def render_account_panel() -> None:
    user = st.session_state.get("authenticated_user")
    if not user:
        return

    st.sidebar.markdown("### 👤 บัญชี")
    st.sidebar.caption(f"เข้าสู่ระบบเป็น `{user}`")
    if st.sidebar.button("ออกจากระบบ"):
        for key in list(st.session_state.keys()):
            if key.startswith(SESSION_KEY_PREFIX):
                st.session_state[key] = ""
        st.session_state.pop("authenticated_user", None)
        st.rerun()


def render_quick_mobile_settings() -> None:
    with st.expander("📱 ตั้งค่าด่วนสำหรับมือถือ", expanded=False):
        st.caption("กรอก API key ตรงนี้ได้เลย ไม่ต้องเปิด sidebar ค่าใช้เฉพาะ session นี้")
        status_cols = st.columns(3)
        for index, (provider, env_name) in enumerate(config.PROVIDER_API_KEYS.items()):
            main_key = f"{SESSION_KEY_PREFIX}{provider}"
            mobile_key = f"mobile_{main_key}"
            if mobile_key not in st.session_state:
                st.session_state[mobile_key] = st.session_state.get(main_key, "")

            value = st.text_input(
                provider,
                type="password",
                key=mobile_key,
                placeholder=f"วาง {env_name}",
            )
            if value.strip():
                st.session_state[main_key] = value.strip()

            status_label = "พร้อม" if effective_api_key(provider) else "ยังไม่มี"
            status_cols[index % 3].metric(provider, status_label)

        action_cols = st.columns(2)
        if action_cols[0].button("ใช้โหมดประหยัด quota", use_container_width=True):
            st.session_state["economy_mode"] = True
            st.rerun()
        if action_cols[1].button("เปิดสร้างไฟล์ Build", use_container_width=True):
            st.session_state["write_files_mode"] = True
            st.rerun()

        if st.button("ล้าง API keys ใน session นี้", use_container_width=True, key="mobile_clear_api_keys"):
            for provider in config.PROVIDER_API_KEYS:
                st.session_state[f"{SESSION_KEY_PREFIX}{provider}"] = ""
                st.session_state[f"mobile_{SESSION_KEY_PREFIX}{provider}"] = ""
            st.rerun()


apply_page_styles()
require_login()

render_app_header()
with st.expander("👋 เริ่มต้นใช้งาน", expanded=False):
    render_landing(show_login=False)


render_quick_mobile_settings()


with st.sidebar:
    render_account_panel()
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

    advanced_models = st.checkbox("เลือกโมเดลแยกต่อ agent", value=False, key="advanced_models")
    economy_mode = st.checkbox(
        "โหมดประหยัด quota",
        value=True,
        key="economy_mode",
        help="ใช้ agent เดียวต่อหนึ่งงาน เหมาะกับ free tier หรือช่วงโดน rate limit",
    )
    write_files_mode = st.checkbox(
        "สร้างไฟล์โปรเจกต์จริงจากผลลัพธ์ Build",
        value=False,
        key="write_files_mode",
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

render_office_dashboard(
    default_provider,
    default_model,
    research_model_settings,
    build_model_settings,
    director_provider,
    director_model,
)

st.divider()

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


attachment_context = render_attachment_tools()
prompt_for_agents = combine_user_input(user_input, attachment_context)
display_command = user_input.strip() or "คำสั่งจากไฟล์/รูปภาพ/เสียงที่แนบ"


run_button_label = "🚀 เริ่มการวิจัย" if mode_key == "research" else "🏗️ เริ่มวางแผนสร้างโปรเจกต์"

if st.button(run_button_label, type="primary", use_container_width=True):
    if not prompt_for_agents.strip():
        st.warning("⚠️ กรุณากรอกคำสั่ง หรือแนบไฟล์/เสียงก่อนครับ")
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
                st.write(f"📌 คำสั่ง: **{display_command}**")
                st.write(f"🧭 โหมด: **{mode_label}**")
                st.write(f"🧠 โมเดลหลัก: `{default_provider} / {default_model}`")
                st.write(f"💸 ประหยัด quota: `{'เปิด' if economy_mode else 'ปิด'}`")
                st.write("---")
                director_llm = build_llm_map({"director": (director_provider, director_model)})["director"]
                team_llms = build_llm_map(active_settings)

                if economy_mode:
                    st.write("⏳ AI Office Lead กำลังทำงานแบบประหยัด quota...")
                    result = run_quick_workflow(prompt_for_agents, mode_label, director_llm)
                    director_brief = "โหมดประหยัด quota: ข้าม Director brief แยกขั้น เพื่อลดจำนวน API requests"
                    result_title = "⚡ ผลลัพธ์แบบประหยัด quota"
                    download_prefix = "quick"
                    agent_labels = ["⚡ AI Office Lead"]

                elif mode_key == "research":
                    st.write("⏳ Director กำลังอ่านคำสั่งและจัด brief...")
                    director_result = create_director_brief(prompt_for_agents, mode_label, director_llm)
                    director_brief = getattr(director_result, "raw", str(director_result))
                    st.write("✅ Director brief พร้อมแล้ว")
                    st.write("⏳ Info Hunter กำลังค้นข้อมูล...")
                    st.write("⏳ Summarizer กำลังสรุป...")
                    st.write("⏳ Comparator กำลังสร้างตาราง...")
                    st.write("⏳ Advisor กำลังให้คำแนะนำ...")
                    st.write("⏳ Fact Checker กำลังตรวจสอบและเรียบเรียง...")
                    st.caption("💡 ใช้เวลาประมาณ 30-90 วินาที ขึ้นกับโมเดลและความยาว")
                    result = run_research_crew(prompt_for_agents, team_llms, director_brief=director_brief)
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
                    director_result = create_director_brief(prompt_for_agents, mode_label, director_llm)
                    director_brief = getattr(director_result, "raw", str(director_result))
                    st.write("✅ Director brief พร้อมแล้ว")
                    st.write("⏳ Product Planner กำลังแตก requirement...")
                    st.write("⏳ Architect กำลังวาง stack และโครงสร้างไฟล์...")
                    st.write("⏳ Developer กำลังเตรียม implementation package...")
                    st.write("⏳ Tester กำลังตรวจความพร้อมส่งมอบ...")
                    st.write("⏳ Delivery Reporter กำลังเรียบเรียงรายงานสุดท้าย...")
                    st.caption("💡 เวอร์ชันนี้ยังเป็น build package ใน Markdown ก่อน ขั้นถัดไปจะให้สร้างไฟล์จริง")
                    result = run_build_crew(prompt_for_agents, director_brief, team_llms)
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
            render_compact_markdown(result_title, final_output)

            if mode_key == "build" and write_files_mode:
                project_dir, generated_files = project_writer.write_project_files(display_command, final_output)
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
                file_name=f"{download_prefix}_{display_command[:30].replace(' ', '_')}.md",
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
projects = project_writer.list_generated_projects()
gallery_title = f"📚 Project Gallery ({len(projects)} โปรเจกต์)"

show_gallery = st.toggle(gallery_title, value=False, key="show_project_gallery")
if show_gallery:
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

        preview_html = project_writer.find_preview_html(selected_project)
        with st.expander("🖥️ Preview", expanded=False):
            if preview_html:
                preview_url = project_writer.html_data_url(preview_html)
                st.caption(f"ไฟล์ preview: `{project_writer.relative_project_file(selected_project, preview_html)}`")
                st.link_button("เปิด preview ในแท็บใหม่", preview_url)
                st.components.v1.iframe(preview_url, height=520, scrolling=True)
            else:
                st.info("โปรเจกต์นี้ยังไม่มีไฟล์ HTML สำหรับ preview")

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

        with st.expander("📁 ไฟล์ในโปรเจกต์", expanded=False):
            for path in selected_project.files:
                st.code(project_writer.relative_project_file(selected_project, path))

        with st.expander("🔎 อ่านไฟล์", expanded=False):
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
