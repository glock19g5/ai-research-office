"""Streamlit UI for AI Research Office."""

import hashlib
import io
import importlib
import json
import mimetypes
import os
import re
import urllib.error
import urllib.request
import uuid
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

AGENT_SKILL_CATALOG = {
    "research": [
        ("Info Hunter", "วาง search plan, แตก query, ตรวจความใหม่ของข้อมูล, ให้คะแนนความน่าเชื่อถือแหล่งข้อมูล"),
        ("Summarizer", "สกัด insight ที่ใช้ตัดสินใจได้จริง แยกข้อเท็จจริง/ข้อสันนิษฐาน/ช่องว่างข้อมูล"),
        ("Comparator", "ทำตารางเปรียบเทียบแบบมีเกณฑ์ถ่วงน้ำหนัก และชี้ trade-off ที่สำคัญ"),
        ("Advisor", "ฟันธงเชิงกลยุทธ์ พร้อมเหตุผล ความเสี่ยง และเงื่อนไขที่ทำให้คำแนะนำเปลี่ยน"),
        ("Fact Checker", "ตรวจ claim สำคัญ ติดป้าย ⚠️ จุดไม่แน่ชัด และเสนอคำค้น/แหล่งข้อมูลที่ควรตรวจต่อ"),
    ],
    "build": [
        ("Director", "แตกโจทย์เป็น brief, scope, deliverables, risk และลำดับงานที่ทีมทำต่อได้ทันที"),
        ("Product Planner", "ทำ user stories, acceptance criteria, non-goals และ MVP cutline"),
        ("Architect", "เลือก stack พร้อมเหตุผล อธิบาย data flow, integration points และข้อจำกัด"),
        ("Developer", "ออกแบบไฟล์ โค้ดหลัก dependency และคำสั่งรันแบบนำไปสร้างต่อได้"),
        ("Tester", "หา edge cases, failure modes, test commands และ residual risks"),
        ("Delivery Reporter", "แปลงผลลัพธ์เป็นคู่มือส่งมอบ พร้อม next iteration และคำแนะนำเพิ่มสกิลทีม"),
    ],
}

AGENT_PROFILE_CATALOG = [
    {
        "key": "director",
        "icon": "🧭",
        "name": "Director",
        "team": "Core",
        "role": "รับคำสั่ง คุยถามให้ brief ชัด และแจกงานให้ทีมที่เหมาะสม",
        "capabilities": [
            "แปลงคำสั่งกว้าง ๆ เป็น brief ที่ทำงานต่อได้",
            "แยกเป้าหมาย ขอบเขต deliverables และความเสี่ยง",
            "เลือกว่าจะใช้ทีม Research หรือ Build และจัดลำดับงาน",
        ],
        "outputs": "Director brief, scope, task routing, risk notes",
        "best_for": "เริ่มงานใหม่ งานที่ยังไม่ชัด หรือ brief จากการโทรสั่งงาน",
    },
    {
        "key": "info_hunter",
        "icon": "🔍",
        "name": "Info Hunter",
        "team": "Research",
        "role": "ค้นคว้าข้อมูล วางแผนการค้นหา และรวบรวมหลักฐาน",
        "capabilities": [
            "แตก keyword/search query ตามประเด็น",
            "ค้นข้อมูลล่าสุดเมื่อเปิด Google Grounding",
            "ให้คะแนนความน่าเชื่อถือและความใหม่ของแหล่งข้อมูล",
        ],
        "outputs": "source notes, evidence list, research leads",
        "best_for": "ข่าว ราคา กฎระเบียบ คู่แข่ง สินค้า หรือข้อมูลที่เปลี่ยนเร็ว",
    },
    {
        "key": "summarizer",
        "icon": "📝",
        "name": "Summarizer",
        "team": "Research",
        "role": "ย่อยข้อมูลยาวให้เป็น insight ที่อ่านเร็วและใช้ตัดสินใจได้",
        "capabilities": [
            "สรุปประเด็นสำคัญจากข้อมูลจำนวนมาก",
            "แยกข้อเท็จจริง assumption และช่องว่างข้อมูล",
            "จัดลำดับ insight ตามความสำคัญของผู้ใช้",
        ],
        "outputs": "executive summary, key insights, assumptions",
        "best_for": "รายงานยาว บทความหลายแหล่ง transcript หรือข้อมูลแนบจำนวนมาก",
    },
    {
        "key": "comparison_builder",
        "icon": "📊",
        "name": "Comparator",
        "team": "Research",
        "role": "เปรียบเทียบทางเลือกด้วยเกณฑ์ที่ชัดเจน",
        "capabilities": [
            "สร้างตารางเปรียบเทียบแบบอ่านง่าย",
            "กำหนด criteria และ trade-off ของแต่ละทางเลือก",
            "ช่วยชี้ข้อดี ข้อเสีย และข้อจำกัดที่ควรระวัง",
        ],
        "outputs": "comparison table, scoring criteria, trade-off notes",
        "best_for": "เลือกเครื่องมือ เลือกสินค้า เทียบแพ็กเกจ เทียบ stack หรือเทียบกลยุทธ์",
    },
    {
        "key": "decision_advisor",
        "icon": "🎯",
        "name": "Advisor",
        "team": "Research",
        "role": "ฟันธงคำแนะนำและวาง next steps",
        "capabilities": [
            "สังเคราะห์ข้อมูลจากทีม Research เป็นข้อแนะนำ",
            "อธิบายเหตุผล เงื่อนไข และความเสี่ยงของคำแนะนำ",
            "เสนอ next steps ที่ทำต่อได้ทันที",
        ],
        "outputs": "recommendation, decision rationale, next steps",
        "best_for": "ต้องการคำตอบว่าเลือกอะไร ทำอะไรก่อน หรือควรเดินแผนไหน",
    },
    {
        "key": "fact_checker",
        "icon": "✅",
        "name": "Fact Checker",
        "team": "Research",
        "role": "ตรวจ claim สำคัญและลดความเสี่ยงจากข้อมูลผิด",
        "capabilities": [
            "ตรวจจุดที่อาจคลาดเคลื่อนหรือไม่มีหลักฐานพอ",
            "ติดป้าย ⚠️ ให้ข้อมูลที่ยังไม่แน่ชัด",
            "เสนอคำค้นหรือแหล่งข้อมูลที่ควรตรวจเพิ่ม",
        ],
        "outputs": "fact-check notes, uncertainty flags, verification checklist",
        "best_for": "ข้อมูลที่มีผลต่อเงิน กฎหมาย สุขภาพ ข่าวล่าสุด หรือการตัดสินใจสำคัญ",
    },
    {
        "key": "product_planner",
        "icon": "📌",
        "name": "Product Planner",
        "team": "Build",
        "role": "แตก requirement และกำหนด MVP scope",
        "capabilities": [
            "แปลงไอเดียเป็น PRD/user stories",
            "กำหนด acceptance criteria และ non-goals",
            "ตัด scope ให้เหมาะกับ MVP และเวลาที่มี",
        ],
        "outputs": "PRD, user stories, acceptance criteria, MVP scope",
        "best_for": "เริ่มโปรเจกต์ใหม่ ฟีเจอร์ใหม่ หรือจัด requirement ให้ทีม dev",
    },
    {
        "key": "system_architect",
        "icon": "🏛️",
        "name": "Architect",
        "team": "Build",
        "role": "เลือก stack และออกแบบโครงสร้างระบบ",
        "capabilities": [
            "ออกแบบ architecture, data flow และ integration points",
            "เลือก framework/library ให้เหมาะกับข้อจำกัด",
            "ระบุ scalability, security และ maintainability risks",
        ],
        "outputs": "architecture plan, file structure, data flow, stack rationale",
        "best_for": "ระบบหลายหน้า API integration database auth หรือโปรเจกต์ที่ต้องวางโครงก่อนเขียน",
    },
    {
        "key": "developer",
        "icon": "💻",
        "name": "Developer",
        "team": "Build",
        "role": "ออกแบบ implementation และเตรียมโค้ด/ไฟล์หลัก",
        "capabilities": [
            "เขียนโครงไฟล์และ code blocks ที่นำไปสร้างต่อได้",
            "ระบุ dependencies, commands และวิธีรัน",
            "ออกแบบ component/function ตาม requirement",
        ],
        "outputs": "code plan, file tree, code snippets, run commands",
        "best_for": "สร้างแอป หน้าเว็บ dashboard automation script หรือ prototype",
    },
    {
        "key": "tester",
        "icon": "🧪",
        "name": "Tester",
        "team": "Build",
        "role": "ตรวจคุณภาพ ความเสี่ยง และวิธีทดสอบก่อนส่งมอบ",
        "capabilities": [
            "หา edge cases และ failure modes",
            "เสนอ manual/automated test cases",
            "ตรวจความพร้อมก่อน deploy หรือส่งงาน",
        ],
        "outputs": "test plan, QA checklist, edge cases, residual risks",
        "best_for": "งานที่ต้องลด bug ก่อนใช้งานจริง หรือเตรียม checklist ส่งมอบ",
    },
    {
        "key": "delivery_reporter",
        "icon": "📦",
        "name": "Delivery Reporter",
        "team": "Build",
        "role": "สรุปงานส่งมอบและแปลงผลลัพธ์ให้ผู้ใช้เอาไปทำต่อได้",
        "capabilities": [
            "จัดระเบียบผลลัพธ์สุดท้ายให้อ่านง่าย",
            "ทำคู่มือใช้งาน วิธีรัน และขั้นตอน deploy",
            "เสนอ next iteration และสิ่งที่ควรพัฒนาต่อ",
        ],
        "outputs": "handoff report, usage guide, changelog, next iteration plan",
        "best_for": "ปิดงาน Build ให้พร้อมส่งต่อหรือใช้เป็นเอกสารประกอบโปรเจกต์",
    },
]

SESSION_KEY_PREFIX = "session_api_key_"
MAX_CONTEXT_CHARS = 14000
MAX_FILE_CHARS = 7000
LINE_TOKEN_ENV = "LINE_CHANNEL_ACCESS_TOKEN"
LINE_RECIPIENT_ENV = "LINE_RECIPIENT_ID"
LINE_TOKEN_SESSION_KEY = "line_channel_access_token"
LINE_RECIPIENT_SESSION_KEY = "line_recipient_id"
LINE_PUSH_ENDPOINT = "https://api.line.me/v2/bot/message/push"
LINE_TEXT_LIMIT = 4900
LINE_MAX_MESSAGES = 5
AUDIO_UPLOAD_TYPES = ["wav", "mp3", "m4a", "ogg", "webm"]
CALL_QUICK_TURNS = [
    (
        "สรุปที่คุย",
        "ช่วยทวนที่ผมสั่งงานเมื่อกี้เป็นภาษาง่าย ๆ ว่าเข้าใจว่าให้ทำอะไรบ้าง",
    ),
    (
        "ถามต่อ",
        "ถ้ายังมีข้อมูลที่จำเป็นต้องรู้ ช่วยถามผมทีละข้อด้วยภาษาง่าย ๆ",
    ),
    (
        "พร้อมส่งงาน",
        "ถ้าข้อมูลพอแล้ว ช่วยสรุป brief สั้น ๆ เพื่อส่งให้ทีม Agent ทำงานต่อ",
    ),
]


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


def render_html_component(html: str, height: int, scrolling: bool = False) -> None:
    st.iframe(html, height=height, width="stretch")


def render_model_picker(key_prefix: str, label: str, default_provider: str, default_model: str):
    provider_key = f"{key_prefix}_provider"
    model_key = f"{key_prefix}_model"
    custom_key = f"{key_prefix}_custom_model"
    if st.session_state.get(provider_key) not in config.MODEL_CATALOG:
        st.session_state[provider_key] = default_provider

    provider = st.selectbox(
        f"{label} provider",
        options=list(config.MODEL_CATALOG.keys()),
        index=provider_index(st.session_state.get(provider_key, default_provider)),
        key=provider_key,
    )
    model_options = config.MODEL_CATALOG[provider]
    if st.session_state.get(model_key) not in model_options:
        fallback_model = default_model if default_model in model_options else model_options[0]
        st.session_state[model_key] = fallback_model

    model = st.selectbox(
        f"{label} model",
        options=model_options,
        index=model_index(provider, st.session_state.get(model_key, default_model)),
        key=model_key,
    )
    custom_model = st.text_input(
        f"{label} custom model id",
        key=custom_key,
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


def model_for_agent(
    agent_key: str,
    default_provider: str,
    default_model: str,
    research_model_settings: dict[str, tuple[str, str]],
    build_model_settings: dict[str, tuple[str, str]],
    director_provider: str,
    director_model: str,
) -> tuple[str, str]:
    if agent_key == "director":
        return director_provider, director_model
    if agent_key in research_model_settings:
        return research_model_settings[agent_key]
    if agent_key in build_model_settings:
        return build_model_settings[agent_key]
    return default_provider, default_model


def render_agent_character(agent: dict[str, str], model_label: str) -> None:
    name = escape(agent["name"])
    role = escape(agent["role"])
    team = escape(agent["team"])
    icon = escape(agent["icon"])
    color = escape(agent["color"])
    accent = escape(agent["accent"])
    delay = escape(agent["delay"])
    model = escape(model_label)

    render_html_component(
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

    render_html_component(
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


def render_three_agent_office(
    default_provider: str,
    default_model: str,
    research_model_settings: dict[str, tuple[str, str]],
    build_model_settings: dict[str, tuple[str, str]],
    director_provider: str,
    director_model: str,
    office_display_height: int,
    reduce_motion: bool,
) -> None:
    office_display_height = max(480, min(1040, int(office_display_height)))
    desk_positions = [
        [-5.8, 0.0, -3.05],
        [-3.45, 0.0, -3.2],
        [-1.1, 0.0, -3.05],
        [-5.8, 0.0, -0.45],
        [-3.45, 0.0, -0.25],
        [-1.1, 0.0, -0.45],
        [-5.8, 0.0, 2.55],
        [-3.15, 0.0, 2.65],
    ]
    meeting_positions = [
        [3.05, 0.0, -2.85],
        [3.75, 0.0, -3.1],
        [4.45, 0.0, -2.85],
        [4.85, 0.0, -2.2],
        [4.45, 0.0, -1.55],
        [3.75, 0.0, -1.3],
        [3.05, 0.0, -1.55],
        [2.65, 0.0, -2.2],
    ]
    speech_lines = [
        "ขอ brief",
        "มี insight",
        "เทียบข้อมูล",
        "ฟันธง",
        "แตก scope",
        "วางระบบ",
        "เริ่ม build",
        "ตรวจให้",
    ]
    work_styles = [
        "research",
        "write",
        "compare",
        "advise",
        "plan",
        "architect",
        "code",
        "test",
    ]

    scene_agents = []
    for index, agent in enumerate(OFFICE_AGENTS):
        model_label = model_label_for_agent(
            agent["key"],
            default_provider,
            default_model,
            research_model_settings,
            build_model_settings,
            director_provider,
            director_model,
        )
        scene_agents.append(
            {
                "name": agent["name"],
                "role": agent["role"],
                "team": agent["team"],
                "icon": agent["icon"],
                "color": agent["color"],
                "accent": agent["accent"],
                "model": model_label,
                "home": desk_positions[index],
                "meet": meeting_positions[index],
                "speech": speech_lines[index],
                "work_style": work_styles[index],
                "phase": index * 0.7,
            }
        )

    scene_json = json.dumps(scene_agents, ensure_ascii=False)
    reduce_motion_json = json.dumps(bool(reduce_motion))
    html = """
    <!doctype html>
    <html>
    <head>
      <meta charset="utf-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1" />
      <style>
        * { box-sizing: border-box; }
        html,
        body {
          height: 100%;
        }
        body {
          margin: 0;
          overflow: hidden;
          font-family: Inter, Segoe UI, sans-serif;
          background: transparent;
        }
        #wrap {
          position: relative;
          width: 100%;
          height: 100%;
          border-radius: 8px;
          overflow: hidden;
          background: linear-gradient(180deg, #dbeafe, #d8f3dc 54%, #d9c7aa);
          border: 1px solid rgba(255,255,255,.65);
        }
        #stage {
          position: absolute;
          inset: 0;
        }
        #stage canvas {
          display: block;
          width: 100% !important;
          height: 100% !important;
        }
        .hud {
          position: absolute;
          left: 16px;
          top: 14px;
          z-index: 3;
          color: #334155;
          text-shadow: 0 1px 0 rgba(255,255,255,.75);
          pointer-events: none;
        }
        .hud b {
          display: block;
          font-size: 20px;
          line-height: 1.2;
        }
        .hud span {
          display: block;
          margin-top: 3px;
          color: rgba(51,65,85,.72);
          font-size: 13px;
        }
        .loading {
          position: absolute;
          inset: 0;
          display: grid;
          place-items: center;
          color: #334155;
          font-weight: 800;
          z-index: 2;
          background: linear-gradient(180deg, #dbeafe, #d8f3dc 54%, #d9c7aa);
        }
        .scene-controls {
          position: absolute;
          right: 14px;
          top: 14px;
          z-index: 4;
          display: flex;
          flex-wrap: wrap;
          justify-content: flex-end;
          gap: 6px;
          max-width: min(420px, calc(100% - 28px));
        }
        .scene-controls.view {
          top: 52px;
        }
        .scene-controls.zoom {
          top: 90px;
        }
        .scene-controls button {
          appearance: none;
          border: 1px solid rgba(51,65,85,.2);
          border-radius: 7px;
          padding: 6px 10px;
          background: rgba(255,255,255,.72);
          color: #334155;
          font: 800 12px/1 Inter, Segoe UI, sans-serif;
          box-shadow: 0 8px 18px rgba(30,41,59,.08);
          cursor: pointer;
        }
        .scene-controls button.active {
          color: #0f172a;
          background: rgba(255,255,255,.95);
          border-color: rgba(14,165,233,.45);
          box-shadow: 0 0 0 2px rgba(14,165,233,.14), 0 8px 18px rgba(30,41,59,.08);
        }
        @media (max-width: 620px) {
          .hud b { font-size: 17px; }
          .hud span { font-size: 11px; max-width: 250px; }
          .scene-controls {
            left: 12px;
            right: 12px;
            top: auto;
            bottom: 12px;
            justify-content: flex-start;
          }
          .scene-controls.view {
            top: auto;
            bottom: 48px;
          }
          .scene-controls.zoom {
            top: auto;
            bottom: 84px;
          }
          .scene-controls button {
            padding: 6px 8px;
            font-size: 11px;
          }
        }
      </style>
    </head>
    <body>
      <div id="wrap">
        <div id="stage"></div>
        <div class="hud">
          <b>3D Pixel Agent Office</b>
          <span>พื้นที่ทำงานจริง ห้องประชุม และบรรยากาศหลายช่วงเวลา</span>
        </div>
        <div class="scene-controls" aria-label="Office atmosphere">
          <button type="button" data-mode="morning" class="active">เช้า</button>
          <button type="button" data-mode="late">สาย</button>
          <button type="button" data-mode="bright">สว่าง</button>
          <button type="button" data-mode="dark">มืด</button>
        </div>
        <div class="scene-controls view" aria-label="Office view">
          <button type="button" data-view="overview" class="active">รวม</button>
          <button type="button" data-view="meeting">ประชุม</button>
          <button type="button" data-view="workspaces">โต๊ะงาน</button>
        </div>
        <div class="scene-controls zoom" aria-label="Office zoom">
          <button type="button" data-zoom="0.84">ย่อ</button>
          <button type="button" data-zoom="1" class="active">100%</button>
          <button type="button" data-zoom="1.24">ขยาย</button>
        </div>
        <div class="loading" id="loading">กำลังโหลดออฟฟิศ 3D...</div>
      </div>

      <script type="module">
        import * as THREE from "https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js";

        const AGENTS = __AGENTS_JSON__;
        const REDUCE_MOTION = __REDUCE_MOTION__;
        const mount = document.getElementById("stage");
        const loading = document.getElementById("loading");
        const scene = new THREE.Scene();
        scene.background = new THREE.Color(0xdbeafe);
        scene.fog = new THREE.Fog(0xdbeafe, 16, 34);

        const camera = new THREE.PerspectiveCamera(42, 1, 0.1, 100);
        camera.position.set(8.6, 6.8, 10.2);
        camera.lookAt(0, 0.75, -0.35);

        const renderer = new THREE.WebGLRenderer({
          antialias: true,
          alpha: false,
          powerPreference: "high-performance",
        });
        renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.5));
        renderer.setClearColor(0xdbeafe, 1);
        renderer.outputColorSpace = THREE.SRGBColorSpace;
        renderer.toneMapping = THREE.ACESFilmicToneMapping;
        renderer.toneMappingExposure = 1.05;
        renderer.shadowMap.enabled = true;
        renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        mount.appendChild(renderer.domElement);

        const hemi = new THREE.HemisphereLight(0xfff4d6, 0x9cb3c5, 1.75);
        scene.add(hemi);
        const key = new THREE.DirectionalLight(0xffc978, 2.2);
        key.position.set(-6, 8, 4);
        key.castShadow = true;
        key.shadow.mapSize.set(1536, 1536);
        key.shadow.bias = -0.00008;
        key.shadow.normalBias = .02;
        key.shadow.camera.left = -8;
        key.shadow.camera.right = 8;
        key.shadow.camera.top = 7;
        key.shadow.camera.bottom = -7;
        scene.add(key);
        const fill = new THREE.PointLight(0xb7d9ff, .9, 22);
        fill.position.set(2.8, 4.4, 3.8);
        scene.add(fill);
        const practicalLights = [];
        const windowPanels = [];

        const mat = {
          floor: new THREE.MeshStandardMaterial({ color: 0xcab991, roughness: .82 }),
          floorLine: new THREE.MeshStandardMaterial({ color: 0x8a7962, roughness: .88 }),
          wall: new THREE.MeshStandardMaterial({ color: 0xe7edf0, roughness: .72 }),
          accentWall: new THREE.MeshStandardMaterial({ color: 0xdbeafe, roughness: .76 }),
          white: new THREE.MeshStandardMaterial({ color: 0xf8fafc, roughness: .62 }),
          skin: new THREE.MeshStandardMaterial({ color: 0xffc9a3, roughness: .72 }),
          skinShade: new THREE.MeshStandardMaterial({ color: 0xd99673, roughness: .78 }),
          dark: new THREE.MeshStandardMaterial({ color: 0x172033, roughness: .68 }),
          shoe: new THREE.MeshStandardMaterial({ color: 0x263244, roughness: .78 }),
          glass: new THREE.MeshPhysicalMaterial({
            color: 0xc7e9ff,
            roughness: .06,
            transmission: .12,
            transparent: true,
            opacity: .34,
            clearcoat: .7,
            clearcoatRoughness: .08,
          }),
          window: new THREE.MeshStandardMaterial({
            color: 0xffd28b,
            roughness: .34,
            emissive: 0xffb86b,
            emissiveIntensity: .45,
          }),
        };

        const dayModes = {
          morning: {
            bg: 0xdbeafe, fog: 0xdbeafe, floor: 0xcab991, wall: 0xe7edf0,
            hemiSky: 0xfff4d6, hemiGround: 0x9cb3c5, hemi: 1.75,
            key: 0xffc978, keyPower: 2.2, keyPos: [-6, 8, 4],
            fill: 0xb7d9ff, fillPower: .9,
            window: 0xffd28b, emissive: 0xffb86b, windowGlow: .45,
            practical: .18, exposure: 1.05,
          },
          late: {
            bg: 0xe0f2fe, fog: 0xe0f2fe, floor: 0xd3c5a3, wall: 0xedf3f4,
            hemiSky: 0xffffff, hemiGround: 0xb4c6d1, hemi: 1.95,
            key: 0xfff2bc, keyPower: 2.55, keyPos: [-2, 8.6, 5.2],
            fill: 0xcffafe, fillPower: 1.05,
            window: 0xffefb0, emissive: 0xffd47b, windowGlow: .56,
            practical: .12, exposure: 1.08,
          },
          bright: {
            bg: 0xf8fafc, fog: 0xf8fafc, floor: 0xd4c3a2, wall: 0xf2f6f7,
            hemiSky: 0xffffff, hemiGround: 0xc6d3d9, hemi: 2.2,
            key: 0xffffff, keyPower: 2.85, keyPos: [2.8, 9.2, 4.4],
            fill: 0xdbeafe, fillPower: 1.2,
            window: 0xfef9c3, emissive: 0xfff08a, windowGlow: .7,
            practical: .08, exposure: 1.12,
          },
          dark: {
            bg: 0x101827, fog: 0x101827, floor: 0x4d4338, wall: 0x263142,
            hemiSky: 0x6c8db8, hemiGround: 0x111827, hemi: .78,
            key: 0x79b8ff, keyPower: .7, keyPos: [-4, 6.8, 2],
            fill: 0x22d3ee, fillPower: .62,
            window: 0x1e3a5f, emissive: 0x3b82f6, windowGlow: .74,
            practical: 1.45, exposure: .92,
          },
        };

        function shadeColor(hex, amount) {
          const color = new THREE.Color(hex);
          color.r = Math.min(1, Math.max(0, color.r + amount));
          color.g = Math.min(1, Math.max(0, color.g + amount));
          color.b = Math.min(1, Math.max(0, color.b + amount));
          return color;
        }

        function pixelMat(hex, roughness = .74, options = {}) {
          return new THREE.MeshStandardMaterial({
            color: new THREE.Color(hex),
            roughness,
            metalness: options.metalness || 0,
            emissive: options.emissive ? new THREE.Color(options.emissive) : new THREE.Color(0x000000),
            emissiveIntensity: options.emissiveIntensity || 0,
            transparent: options.opacity !== undefined,
            opacity: options.opacity === undefined ? 1 : options.opacity,
          });
        }

        function addVoxel(parent, size, pos, material, cast = true, receive = true) {
          const mesh = new THREE.Mesh(new THREE.BoxGeometry(...size), material);
          mesh.position.set(...pos);
          mesh.castShadow = cast;
          mesh.receiveShadow = receive;
          parent.add(mesh);
          return mesh;
        }

        function setAtmosphere(modeName) {
          const mode = dayModes[modeName] || dayModes.morning;
          scene.background.set(mode.bg);
          scene.fog.color.set(mode.fog);
          mat.floor.color.set(mode.floor);
          mat.wall.color.set(mode.wall);
          hemi.color.set(mode.hemiSky);
          hemi.groundColor.set(mode.hemiGround);
          hemi.intensity = mode.hemi;
          key.color.set(mode.key);
          key.intensity = mode.keyPower;
          key.position.set(...mode.keyPos);
          fill.color.set(mode.fill);
          fill.intensity = mode.fillPower;
          mat.window.color.set(mode.window);
          mat.window.emissive.set(mode.emissive);
          mat.window.emissiveIntensity = mode.windowGlow;
          renderer.toneMappingExposure = mode.exposure;
          practicalLights.forEach((light) => { light.intensity = mode.practical; });
          document.querySelectorAll("[data-mode]").forEach((button) => {
            button.classList.toggle("active", button.dataset.mode === modeName);
          });
          if (REDUCE_MOTION && window.__officeStaticReady) renderStaticFrame();
        }

        function addBox(size, pos, material, radius = false) {
          const mesh = new THREE.Mesh(new THREE.BoxGeometry(...size), material);
          mesh.position.set(...pos);
          mesh.castShadow = true;
          mesh.receiveShadow = true;
          scene.add(mesh);
          return mesh;
        }

        function makeCanvasLabel(text, bg = "rgba(255,255,255,.90)", color = "#334155") {
          const canvas = document.createElement("canvas");
          canvas.width = 420;
          canvas.height = 128;
          const ctx = canvas.getContext("2d");
          ctx.clearRect(0, 0, canvas.width, canvas.height);
          ctx.fillStyle = bg;
          roundRect(ctx, 12, 18, 396, 82, 24);
          ctx.fill();
          ctx.fillStyle = color;
          ctx.font = "700 34px Segoe UI, sans-serif";
          ctx.textAlign = "center";
          ctx.textBaseline = "middle";
          ctx.fillText(text, 210, 59, 360);
          const texture = new THREE.CanvasTexture(canvas);
          const sprite = new THREE.Sprite(new THREE.SpriteMaterial({ map: texture, transparent: true }));
          sprite.scale.set(1.85, .56, 1);
          return sprite;
        }

        function roundRect(ctx, x, y, w, h, r) {
          ctx.beginPath();
          ctx.moveTo(x + r, y);
          ctx.arcTo(x + w, y, x + w, y + h, r);
          ctx.arcTo(x + w, y + h, x, y + h, r);
          ctx.arcTo(x, y + h, x, y, r);
          ctx.arcTo(x, y, x + w, y, r);
          ctx.closePath();
        }

        function hexMat(hex, clearcoat = .5) {
          return new THREE.MeshPhysicalMaterial({
            color: new THREE.Color(hex),
            roughness: .34,
            clearcoat,
            clearcoatRoughness: .16,
          });
        }

        function makeIconBadge(icon, bg) {
          const canvas = document.createElement("canvas");
          canvas.width = 96;
          canvas.height = 96;
          const ctx = canvas.getContext("2d");
          ctx.fillStyle = bg;
          ctx.fillRect(8, 8, 80, 80);
          ctx.strokeStyle = "rgba(15,23,42,.32)";
          ctx.lineWidth = 6;
          ctx.strokeRect(8, 8, 80, 80);
          ctx.font = "46px Segoe UI Emoji, Apple Color Emoji, sans-serif";
          ctx.textAlign = "center";
          ctx.textBaseline = "middle";
          ctx.fillText(icon, 48, 51);
          const texture = new THREE.CanvasTexture(canvas);
          texture.colorSpace = THREE.SRGBColorSpace;
          texture.magFilter = THREE.NearestFilter;
          texture.minFilter = THREE.NearestFilter;
          const sprite = new THREE.Sprite(new THREE.SpriteMaterial({ map: texture, transparent: true }));
          sprite.scale.set(.34, .34, 1);
          return sprite;
        }

        const workspaceTypes = [
          { label: "Strategy", screen: 0x0f766e, prop: "map" },
          { label: "Search", screen: 0x2563eb, prop: "radar" },
          { label: "Data", screen: 0x16a34a, prop: "chart" },
          { label: "Decision", screen: 0xbe123c, prop: "target" },
          { label: "Product", screen: 0x7c3aed, prop: "sticky" },
          { label: "System", screen: 0x0284c7, prop: "blueprint" },
          { label: "Code", screen: 0x15803d, prop: "terminal" },
          { label: "QA", screen: 0x0f766e, prop: "checklist" },
        ];

        function addWorkspaceProp(group, style, accentMat, screenMat) {
          if (style.prop === "chart") {
            for (let b = 0; b < 4; b++) {
              addVoxel(group, [.08, .1 + b * .055, .045], [.38 + b * .1, .78 + b * .027, -.11], accentMat);
            }
            return;
          }
          if (style.prop === "plant") {
            addVoxel(group, [.13, .16, .13], [.45, .72, -.16], pixelMat(0x7c4a2d, .82));
            addVoxel(group, [.2, .18, .06], [.45, .88, -.16], pixelMat(0x16a34a, .8));
            return;
          }
          if (style.prop === "terminal") {
            addVoxel(group, [.46, .04, .08], [.02, .76, -.12], pixelMat(0x111827, .76, { emissive: 0x22c55e, emissiveIntensity: .08 }));
            for (let row = 0; row < 3; row++) {
              addVoxel(group, [.05 + row * .04, .015, .012], [-.16 + row * .12, .795 + row * .035, -.075], pixelMat(0x86efac, .6, { emissive: 0x22c55e, emissiveIntensity: .25 }));
            }
            return;
          }
          if (style.prop === "blueprint") {
            addVoxel(group, [.42, .04, .32], [.38, .72, .09], pixelMat(0xdbeafe, .74));
            addVoxel(group, [.34, .015, .02], [.38, .755, .24], screenMat);
            addVoxel(group, [.02, .015, .24], [.22, .755, .1], screenMat);
            return;
          }
          if (style.prop === "checklist") {
            addVoxel(group, [.28, .035, .34], [.42, .72, .08], pixelMat(0xffffff, .7));
            for (let row = 0; row < 3; row++) {
              addVoxel(group, [.04, .015, .02], [.32, .755 + row * .055, .22 - row * .07], accentMat);
              addVoxel(group, [.16, .012, .018], [.43, .755 + row * .055, .22 - row * .07], mat.dark);
            }
            return;
          }
          if (style.prop === "radar") {
            const radar = new THREE.Mesh(new THREE.CylinderGeometry(.16, .16, .035, 8), screenMat);
            radar.position.set(.43, .73, .07);
            radar.rotation.x = Math.PI / 2;
            radar.castShadow = true;
            group.add(radar);
            addVoxel(group, [.02, .18, .02], [.43, .77, .07], accentMat);
            return;
          }
          addVoxel(group, [.28, .035, .26], [.42, .72, .08], accentMat);
          addVoxel(group, [.17, .04, .04], [.42, .78, .2], mat.white);
        }

        function addDesk(agent, i) {
          const group = new THREE.Group();
          const x = agent.home[0];
          const z = agent.home[2];
          const style = workspaceTypes[i % workspaceTypes.length];
          const topMat = pixelMat(agent.color, .68);
          const accentMat = pixelMat(agent.accent, .72);
          const edgeMat = pixelMat(shadeColor(agent.color, -.22), .82);
          const screenMat = pixelMat(style.screen, .58, { emissive: style.screen, emissiveIntensity: .18 });
          const zoneMat = pixelMat(agent.color, .88, { opacity: .18 });

          addVoxel(group, [1.72, .035, 1.36], [0, .02, .04], zoneMat, false, true);
          addVoxel(group, [1.72, .035, .06], [0, .045, -.66], edgeMat, false, true);
          addVoxel(group, [1.72, .035, .06], [0, .045, .74], edgeMat, false, true);
          addVoxel(group, [.06, .035, 1.36], [-.86, .045, .04], edgeMat, false, true);
          addVoxel(group, [.06, .035, 1.36], [.86, .045, .04], edgeMat, false, true);

          addVoxel(group, [1.18, .16, .72], [0, .58, 0], topMat);
          addVoxel(group, [1.22, .09, .08], [0, .68, -.36], edgeMat);
          for (const dx of [-.48, .48]) {
            for (const dz of [-.26, .26]) {
              addVoxel(group, [.09, .55, .09], [dx, .28, dz], edgeMat);
            }
          }

          addVoxel(group, [.5, .28, .44], [0, .27, .78], accentMat);
          addVoxel(group, [.5, .58, .1], [0, .55, .99], accentMat);
          addVoxel(group, [.54, .06, .2], [0, .52, .63], mat.dark);

          addVoxel(group, [.66, .42, .08], [0, .96, -.28], mat.dark);
          addVoxel(group, [.56, .32, .045], [0, .97, -.225], screenMat);
          addVoxel(group, [.14, .18, .08], [0, .72, -.24], mat.dark);
          addVoxel(group, [.46, .04, .18], [0, .71, .08], mat.dark);

          addWorkspaceProp(group, style, accentMat, screenMat);

          const label = makeCanvasLabel(agent.name);
          label.position.set(0, 1.28, .2);
          label.scale.set(1.38, .42, 1);
          group.add(label);

          const zone = makeCanvasLabel(style.label, "rgba(255,255,255,.72)", "#334155");
          zone.position.set(0, .1, -.7);
          zone.scale.set(.95, .28, 1);
          group.add(zone);

          group.position.set(x, 0, z);
          scene.add(group);
        }

        function createPixelAgent(agent, i) {
          const group = new THREE.Group();
          const hairMat = pixelMat(agent.accent, .76);
          const hairDark = pixelMat(shadeColor(agent.accent, -.18), .82);
          const jacketMat = pixelMat(agent.color, .72);
          const jacketDark = pixelMat(shadeColor(agent.color, -.24), .8);
          const accentMat = pixelMat(agent.accent, .68);
          const skinHi = pixelMat(0xffd7b8, .72);

          addVoxel(group, [.22, .14, .18], [0, 1.22, 0], mat.skin);
          addVoxel(group, [.58, .58, .48], [0, 1.58, 0], mat.skin);
          addVoxel(group, [.12, .12, .03], [-.16, 1.59, .255], mat.dark);
          addVoxel(group, [.12, .12, .03], [.16, 1.59, .255], mat.dark);
          addVoxel(group, [.06, .1, .035], [0, 1.48, .262], mat.skinShade);
          addVoxel(group, [.18, .035, .035], [0, 1.36, .265], pixelMat(0x7f1d1d, .74));
          addVoxel(group, [.08, .035, .035], [-.27, 1.47, .258], pixelMat(0xf4a6a6, .8));
          addVoxel(group, [.08, .035, .035], [.27, 1.47, .258], pixelMat(0xf4a6a6, .8));

          addVoxel(group, [.64, .16, .5], [0, 1.92, -.01], hairMat);
          addVoxel(group, [.68, .16, .13], [0, 1.78, .22], hairMat);
          addVoxel(group, [.12, .38, .46], [-.35, 1.6, -.01], hairDark);
          addVoxel(group, [.12, .34, .44], [.35, 1.61, -.01], hairDark);
          for (let p = 0; p < 3; p++) {
            addVoxel(group, [.14, .16, .13], [(-.18 + p * .18), 1.69 - p * .025, .28], p === 1 ? hairDark : hairMat);
          }

          addVoxel(group, [.54, .74, .36], [0, .88, 0], jacketMat);
          addVoxel(group, [.24, .76, .39], [0, .89, .02], mat.white);
          addVoxel(group, [.12, .68, .04], [-.2, .9, .23], jacketDark);
          addVoxel(group, [.12, .68, .04], [.2, .9, .23], jacketDark);
          addVoxel(group, [.42, .08, .42], [0, .5, 0], jacketDark);

          const badge = makeIconBadge(agent.icon, agent.color);
          badge.position.set(0, .98, .28);
          group.add(badge);

          const limbs = [];
          for (const side of [-1, 1]) {
            const armGroup = new THREE.Group();
            armGroup.position.set(side * .39, 1.12, .02);
            addVoxel(armGroup, [.14, .42, .18], [0, -.2, 0], jacketMat);
            addVoxel(armGroup, [.13, .16, .16], [0, -.48, .01], skinHi);
            armGroup.rotation.z = side * .12;
            group.add(armGroup);
            limbs.push({ mesh: armGroup, side, type: "arm" });

            const legGroup = new THREE.Group();
            legGroup.position.set(side * .17, .48, 0);
            addVoxel(legGroup, [.16, .48, .2], [0, -.23, 0], accentMat);
            addVoxel(legGroup, [.2, .11, .32], [side * .025, -.52, .07], mat.shoe);
            group.add(legGroup);
            limbs.push({ mesh: legGroup, side, type: "leg" });
          }

          const speech = makeCanvasLabel(agent.speech, "rgba(255,255,255,.94)");
          speech.position.set(0, 2.28, 0);
          speech.visible = false;
          group.add(speech);

          const name = makeCanvasLabel(agent.name, "rgba(255,255,255,.82)");
          name.position.set(0, .08, 0);
          name.scale.set(1.14, .35, 1);
          group.add(name);

          const workSpot = new THREE.Vector3(agent.home[0], .02, agent.home[2] + .72);
          const standSpot = new THREE.Vector3(agent.home[0], .02, agent.home[2] + .18);
          group.position.copy(workSpot);
          group.userData = {
            home: new THREE.Vector3(...agent.home),
            work: workSpot,
            stand: standSpot,
            meet: new THREE.Vector3(...agent.meet),
            workStyle: agent.work_style || "focus",
            phase: agent.phase,
            limbs,
            speech,
          };
          scene.add(group);
          return group;
        }

        const floor = new THREE.Mesh(new THREE.BoxGeometry(14.8, .18, 9.6), mat.floor);
        floor.position.y = -.1;
        floor.receiveShadow = true;
        scene.add(floor);

        for (let gx = -6.8; gx <= 6.8; gx += 1.2) {
          addVoxel(scene, [.025, .012, 9.2], [gx, .02, 0], mat.floorLine, false, true);
        }
        for (let gz = -4.2; gz <= 4.2; gz += 1.2) {
          addVoxel(scene, [14.2, .012, .025], [0, .021, gz], mat.floorLine, false, true);
        }

        const backWall = new THREE.Mesh(new THREE.BoxGeometry(14.8, 3.8, .18), mat.wall);
        backWall.position.set(0, 1.75, -4.88);
        backWall.receiveShadow = true;
        scene.add(backWall);

        const leftWall = new THREE.Mesh(new THREE.BoxGeometry(.18, 3.8, 9.6), mat.wall);
        leftWall.position.set(-7.4, 1.75, 0);
        leftWall.receiveShadow = true;
        scene.add(leftWall);

        const accentWall = new THREE.Mesh(new THREE.BoxGeometry(5.1, 2.3, .08), mat.accentWall);
        accentWall.position.set(3.75, 1.72, -4.76);
        accentWall.receiveShadow = true;
        scene.add(accentWall);

        for (const wx of [-5.8, -4.2, -2.6, -.8, 1.0]) {
          const pane = new THREE.Mesh(new THREE.BoxGeometry(1.0, 1.25, .04), mat.window);
          pane.position.set(wx, 2.1, -4.76);
          pane.castShadow = false;
          pane.receiveShadow = false;
          scene.add(pane);
          windowPanels.push(pane);
          addVoxel(scene, [1.08, .06, .05], [wx, 1.43, -4.72], mat.white, false, false);
          addVoxel(scene, [.06, 1.32, .05], [wx - .54, 2.1, -4.72], mat.white, false, false);
          addVoxel(scene, [.06, 1.32, .05], [wx + .54, 2.1, -4.72], mat.white, false, false);
        }

        for (const lx of [-4.8, -.8, 3.2]) {
          const panel = addVoxel(scene, [1.55, .045, .58], [lx, 3.62, .6], mat.white, false, false);
          const light = new THREE.PointLight(0xfff4d6, .18, 4.8);
          light.position.set(lx, 3.38, .6);
          scene.add(light);
          practicalLights.push(light);
          panel.material = pixelMat(0xfff7d6, .5, { emissive: 0xfff0b2, emissiveIntensity: .22 });
        }

        const loungeRug = new THREE.Mesh(new THREE.BoxGeometry(2.6, .04, 1.8), pixelMat(0xd8f3dc, .8));
        loungeRug.position.set(.15, .025, 1.55);
        loungeRug.receiveShadow = true;
        scene.add(loungeRug);
        addVoxel(scene, [1.1, .34, .42], [-.55, .2, 1.5], pixelMat(0xf8fafc, .66));
        addVoxel(scene, [1.1, .54, .16], [-.55, .42, 1.78], pixelMat(0xe2e8f0, .72));
        addVoxel(scene, [.64, .34, .42], [.78, .2, 1.5], pixelMat(0xf8fafc, .66));

        const meetingFloor = new THREE.Mesh(new THREE.BoxGeometry(4.8, .055, 3.55), pixelMat(0xe0f2fe, .78));
        meetingFloor.position.set(3.75, .025, -2.2);
        meetingFloor.receiveShadow = true;
        scene.add(meetingFloor);

        const glassPieces = [
          [[4.85, 1.86, .055], [3.75, 1.03, -3.98]],
          [[.055, 1.86, 3.5], [1.32, 1.03, -2.2]],
          [[.055, 1.86, 3.5], [6.18, 1.03, -2.2]],
          [[1.55, 1.86, .055], [2.15, 1.03, -.43]],
          [[1.55, 1.86, .055], [5.35, 1.03, -.43]],
        ];
        for (const [size, pos] of glassPieces) {
          const pane = new THREE.Mesh(new THREE.BoxGeometry(...size), mat.glass);
          pane.position.set(...pos);
          pane.castShadow = false;
          pane.receiveShadow = true;
          scene.add(pane);
        }
        addVoxel(scene, [.08, 1.95, .08], [1.32, 1.02, -3.98], mat.dark, false, true);
        addVoxel(scene, [.08, 1.95, .08], [6.18, 1.02, -3.98], mat.dark, false, true);
        addVoxel(scene, [.08, 1.95, .08], [1.32, 1.02, -.43], mat.dark, false, true);
        addVoxel(scene, [.08, 1.95, .08], [6.18, 1.02, -.43], mat.dark, false, true);

        const roomLabel = makeCanvasLabel("Meeting Room", "rgba(255,255,255,.78)", "#334155");
        roomLabel.position.set(3.75, 2.15, -.5);
        roomLabel.scale.set(1.25, .38, 1);
        scene.add(roomLabel);

        const meetingTable = new THREE.Mesh(new THREE.CylinderGeometry(1.05, 1.18, .32, 12), pixelMat(0x94a3b8, .66));
        meetingTable.position.set(3.75, .34, -2.2);
        meetingTable.castShadow = true;
        meetingTable.receiveShadow = true;
        scene.add(meetingTable);

        for (let a = 0; a < Math.PI * 2; a += Math.PI / 4) {
          const chair = new THREE.Mesh(new THREE.BoxGeometry(.34, .26, .34), mat.white);
          chair.position.set(3.75 + Math.cos(a) * 1.35, .18, -2.2 + Math.sin(a) * .98);
          chair.rotation.y = -a;
          chair.castShadow = true;
          chair.receiveShadow = true;
          scene.add(chair);
        }

        addVoxel(scene, [.09, 1.35, .09], [6.75, .68, 3.65], pixelMat(0x7c4a2d, .78));
        addVoxel(scene, [.58, .2, .58], [6.75, .22, 3.65], pixelMat(0x92400e, .78));
        addVoxel(scene, [.72, .48, .22], [6.75, 1.28, 3.65], pixelMat(0x16a34a, .82));
        addVoxel(scene, [.22, .58, .72], [6.75, 1.22, 3.65], pixelMat(0x22c55e, .8));

        AGENTS.forEach(addDesk);
        const pixelAgents = AGENTS.map(createPixelAgent);

        setAtmosphere("morning");

        const cameraViews = {
          overview: {
            pos: new THREE.Vector3(8.6, 6.8, 10.2),
            look: new THREE.Vector3(-.25, .78, -.35),
          },
          meeting: {
            pos: new THREE.Vector3(8.7, 6.4, 3.25),
            look: new THREE.Vector3(3.75, .9, -2.2),
          },
          workspaces: {
            pos: new THREE.Vector3(-6.75, 4.25, 4.35),
            look: new THREE.Vector3(-3.55, .82, -.45),
          },
        };
        let activeView = "overview";
        const targetCamera = cameraViews.overview.pos.clone();
        const targetLook = cameraViews.overview.look.clone();
        const currentLook = targetLook.clone();
        let zoomLevel = 1;

        function setView(viewName) {
          const view = cameraViews[viewName] || cameraViews.overview;
          activeView = viewName in cameraViews ? viewName : "overview";
          targetCamera.copy(view.pos);
          targetLook.copy(view.look);
          document.querySelectorAll("[data-view]").forEach((button) => {
            button.classList.toggle("active", button.dataset.view === activeView);
          });
          if (REDUCE_MOTION) renderStaticFrame();
        }

        function setZoom(nextZoom) {
          zoomLevel = Number(nextZoom) || 1;
          document.querySelectorAll("[data-zoom]").forEach((button) => {
            button.classList.toggle("active", Number(button.dataset.zoom) === zoomLevel);
          });
          if (REDUCE_MOTION) renderStaticFrame();
        }

        document.querySelectorAll("[data-mode]").forEach((button) => {
          button.addEventListener("click", () => setAtmosphere(button.dataset.mode));
        });
        document.querySelectorAll("[data-view]").forEach((button) => {
          button.addEventListener("click", () => setView(button.dataset.view));
        });
        document.querySelectorAll("[data-zoom]").forEach((button) => {
          button.addEventListener("click", () => setZoom(button.dataset.zoom));
        });

        function resize() {
          const rect = mount.getBoundingClientRect();
          renderer.setSize(rect.width, rect.height, true);
          camera.aspect = rect.width / Math.max(rect.height, 1);
          camera.updateProjectionMatrix();
        }
        window.addEventListener("resize", resize);
        resize();
        loading.style.display = "none";

        const meetingCenter = new THREE.Vector3(3.75, .55, -2.25);

        function smooth01(value) {
          const v = THREE.MathUtils.clamp(value, 0, 1);
          return v * v * (3 - 2 * v);
        }

        function faceAgent(agentGroup, target, ease = .18) {
          const dx = target.x - agentGroup.position.x;
          const dz = target.z - agentGroup.position.z;
          if (Math.abs(dx) + Math.abs(dz) < .001) return;
          const targetAngle = Math.atan2(dx, dz);
          const delta = Math.atan2(Math.sin(targetAngle - agentGroup.rotation.y), Math.cos(targetAngle - agentGroup.rotation.y));
          agentGroup.rotation.y += delta * ease;
        }

        function applyAgentPosture(agentGroup, mode, time) {
          const data = agentGroup.userData;
          const walkSwing = Math.sin(time * 8.2 + data.phase * 2.1);
          const typing = Math.sin(time * 11.5 + data.phase * 3.4);
          const gesture = Math.sin(time * 2.8 + data.phase * 1.3);
          const activeGesture = Math.max(0, gesture);
          const workStyle = data.workStyle || "focus";
          const sitLike = mode === "work" || mode === "sit";
          const targetScaleY = sitLike ? .8 : mode === "meeting" ? .9 : 1;

          agentGroup.scale.y = THREE.MathUtils.lerp(agentGroup.scale.y, targetScaleY, .14);
          agentGroup.rotation.z = THREE.MathUtils.lerp(agentGroup.rotation.z, sitLike ? Math.sin(time * 1.3 + data.phase) * .012 : 0, .12);

          for (const limb of data.limbs) {
            let targetX = 0;
            let targetZ = 0;

            if (mode === "walk") {
              if (limb.type === "arm") {
                targetX = -walkSwing * .46;
                targetZ = limb.side * .12;
              } else {
                targetX = walkSwing * .34;
                targetZ = limb.side * walkSwing * .26;
              }
            } else if (mode === "meeting") {
              if (limb.type === "arm") {
                targetX = -.34 + activeGesture * .16;
                targetZ = limb.side * (.2 + activeGesture * .12);
              } else {
                targetX = -.66;
                targetZ = limb.side * .1;
              }
            } else if (sitLike) {
              if (limb.type === "arm") {
                if (workStyle === "code" || workStyle === "write") {
                  targetX = -.8 + typing * .06;
                  targetZ = limb.side * (.08 + Math.abs(typing) * .08);
                } else if (workStyle === "research" || workStyle === "compare") {
                  targetX = limb.side < 0 ? -.62 + typing * .025 : -.42 + activeGesture * .05;
                  targetZ = limb.side < 0 ? -.06 : .22 + activeGesture * .06;
                } else if (workStyle === "advise" || workStyle === "plan" || workStyle === "architect") {
                  targetX = limb.side > 0 ? -.28 + activeGesture * .12 : -.68;
                  targetZ = limb.side > 0 ? .32 + activeGesture * .08 : -.07;
                } else if (workStyle === "test") {
                  targetX = limb.side > 0 ? -.82 + typing * .035 : -.58;
                  targetZ = limb.side > 0 ? .16 + Math.abs(typing) * .05 : -.04;
                } else {
                  targetX = -.76 + typing * .035;
                  targetZ = limb.side * (.08 + Math.abs(typing) * .05);
                }
              } else {
                targetX = workStyle === "advise" || workStyle === "architect" ? -.88 : -1.02;
                targetZ = limb.side * (workStyle === "code" ? .16 : .13);
              }
            } else {
              if (limb.type === "arm") {
                targetX = -.14;
                targetZ = limb.side * .13;
              } else {
                targetX = -.05;
                targetZ = limb.side * .04;
              }
            }

            limb.mesh.rotation.x = THREE.MathUtils.lerp(limb.mesh.rotation.x, targetX, .22);
            limb.mesh.rotation.y = THREE.MathUtils.lerp(limb.mesh.rotation.y, 0, .22);
            limb.mesh.rotation.z = THREE.MathUtils.lerp(limb.mesh.rotation.z, targetZ, .22);
          }
        }

        function updateAgentRoutine(pixelAgent, time) {
          const data = pixelAgent.userData;
          const cycleSeconds = 34;
          const t = ((time + data.phase * 4.2) % cycleSeconds) / cycleSeconds;
          let mode = "work";
          let pos = data.work.clone();
          let bob = 0;

          if (t < .48) {
            mode = "work";
          } else if (t < .54) {
            const k = smooth01((t - .48) / .06);
            mode = k < .7 ? "sit" : "stand";
            pos = data.work.clone().lerp(data.stand, k);
          } else if (t < .66) {
            const k = smooth01((t - .54) / .12);
            mode = "walk";
            pos = data.stand.clone().lerp(data.meet, k);
            bob = Math.abs(Math.sin(time * 8.2 + data.phase)) * .045;
          } else if (t < .81) {
            mode = "meeting";
            pos = data.meet.clone();
          } else if (t < .93) {
            const k = smooth01((t - .81) / .12);
            mode = "walk";
            pos = data.meet.clone().lerp(data.stand, k);
            bob = Math.abs(Math.sin(time * 8.2 + data.phase)) * .045;
          } else {
            const k = smooth01((t - .93) / .07);
            mode = k < .35 ? "stand" : "sit";
            pos = data.stand.clone().lerp(data.work, k);
          }

          pixelAgent.position.set(pos.x, .02 + bob, pos.z);

          if (mode === "walk") {
            const target = t < .72 ? data.meet : data.stand;
            faceAgent(pixelAgent, target, .26);
          } else if (mode === "meeting") {
            faceAgent(pixelAgent, meetingCenter, .18);
          } else {
            faceAgent(pixelAgent, new THREE.Vector3(data.home.x, .55, data.home.z - .72), .16);
          }

          data.speech.visible = mode === "meeting";
          applyAgentPosture(pixelAgent, mode, time);
        }

        const clock = new THREE.Clock();
        function renderStaticFrame() {
          currentLook.copy(targetLook);
          const zoomedCamera = currentLook.clone().add(targetCamera.clone().sub(currentLook).multiplyScalar(1 / zoomLevel));
          camera.position.copy(zoomedCamera);
          camera.lookAt(currentLook);
          for (const pixelAgent of pixelAgents) updateAgentRoutine(pixelAgent, 0);
          renderer.render(scene, camera);
        }

        function animate() {
          const time = clock.getElapsedTime();
          currentLook.lerp(targetLook, .055);
          const zoomedCamera = currentLook.clone().add(targetCamera.clone().sub(currentLook).multiplyScalar(1 / zoomLevel));
          camera.position.lerp(zoomedCamera, .045);
          camera.lookAt(currentLook);

          for (const pixelAgent of pixelAgents) updateAgentRoutine(pixelAgent, time);
          renderer.render(scene, camera);
          requestAnimationFrame(animate);
        }
        window.__officeStaticReady = true;
        if (REDUCE_MOTION) {
          renderStaticFrame();
        } else {
          animate();
        }
      </script>
    </body>
    </html>
    """.replace("__AGENTS_JSON__", scene_json).replace("__REDUCE_MOTION__", reduce_motion_json)

    render_html_component(html, height=office_display_height, scrolling=False)


def render_agent_directory(
    default_provider: str,
    default_model: str,
    research_model_settings: dict[str, tuple[str, str]],
    build_model_settings: dict[str, tuple[str, str]],
    director_provider: str,
    director_model: str,
) -> None:
    with st.expander("ข้อมูล Agent: บทบาท ความสามารถ และโมเดลที่ใช้", expanded=False):
        st.caption("ดูว่า Agent แต่ละตัวเหมาะกับงานแบบไหน ทำอะไรได้ และจะส่งมอบอะไรให้ทีม")
        tabs = st.tabs(["Core", "Research", "Build"])
        teams = ["Core", "Research", "Build"]

        for tab, team in zip(tabs, teams):
            with tab:
                team_profiles = [profile for profile in AGENT_PROFILE_CATALOG if profile["team"] == team]
                for index, profile in enumerate(team_profiles):
                    model_label = model_label_for_agent(
                        profile["key"],
                        default_provider,
                        default_model,
                        research_model_settings,
                        build_model_settings,
                        director_provider,
                        director_model,
                    )
                    st.markdown(f"#### {profile['icon']} {profile['name']}")
                    st.markdown(f"**บทบาท:** {profile['role']}")
                    st.markdown(f"**AI ที่ใช้:** `{model_label}`")
                    st.markdown("**ทำอะไรได้:**")
                    for capability in profile["capabilities"]:
                        st.markdown(f"- {capability}")
                    st.markdown(f"**ผลลัพธ์ที่ส่งมอบ:** `{profile['outputs']}`")
                    st.markdown(f"**เหมาะกับ:** {profile['best_for']}")
                    if index < len(team_profiles) - 1:
                        st.divider()


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
    metric_cols[0].metric("Agents", len(AGENT_PROFILE_CATALOG))
    metric_cols[1].metric("Projects", len(projects))
    metric_cols[2].metric("Files", generated_file_count)
    metric_cols[3].metric("Providers", ready_provider_count)

    st.markdown("### ทีม Agent")
    office_display_height = st.slider(
        "ขนาดจอออฟฟิศ 3D",
        min_value=480,
        max_value=1040,
        value=720,
        step=40,
        key="office_display_height",
        help="เพิ่มหรือลดความสูงของพื้นที่แสดงออฟฟิศ 3D",
    )
    reduce_office_motion = st.checkbox(
        "ลดการกระพริบ/หยุดแอนิเมชัน 3D",
        value=True,
        key="reduce_office_motion",
        help="เปิดไว้เมื่อหน้าจอกระพริบหรือเครื่อง render ฉาก 3D หนักเกินไป",
    )
    render_three_agent_office(
        default_provider,
        default_model,
        research_model_settings,
        build_model_settings,
        director_provider,
        director_model,
        office_display_height,
        reduce_office_motion,
    )

    render_agent_directory(
        default_provider,
        default_model,
        research_model_settings,
        build_model_settings,
        director_provider,
        director_model,
    )


def session_api_key(provider: str) -> str | None:
    value = st.session_state.get(f"{SESSION_KEY_PREFIX}{provider}", "")
    return value.strip() or None


def effective_api_key(provider: str) -> str | None:
    return session_api_key(provider) or config.get_api_key(provider)


def load_saved_api_keys_for_user(force: bool = False) -> None:
    user = st.session_state.get("authenticated_user")
    if not user:
        return
    if not force and st.session_state.get("saved_api_keys_loaded_for") == user:
        return

    saved_keys = auth_store.get_user_api_keys(user)
    saved_providers: list[str] = []
    for provider in config.PROVIDER_API_KEYS:
        value = saved_keys.get(provider, "").strip()
        if not value:
            continue

        main_key = f"{SESSION_KEY_PREFIX}{provider}"
        mobile_key = f"mobile_{main_key}"
        if not st.session_state.get(main_key):
            st.session_state[main_key] = value
        if not st.session_state.get(mobile_key):
            st.session_state[mobile_key] = value
        st.session_state[f"saved_api_key_fingerprint_{provider}"] = hashlib.sha256(
            f"{provider}\0{value}".encode("utf-8")
        ).hexdigest()
        saved_providers.append(provider)

    st.session_state["saved_api_key_providers"] = saved_providers
    st.session_state["saved_api_keys_loaded_for"] = user


def persist_api_key_for_user(provider: str, value: str) -> None:
    user = st.session_state.get("authenticated_user")
    clean_value = value.strip()
    if not user or not clean_value:
        return

    fingerprint = hashlib.sha256(f"{provider}\0{clean_value}".encode("utf-8")).hexdigest()
    fingerprint_key = f"saved_api_key_fingerprint_{provider}"
    if st.session_state.get(fingerprint_key) == fingerprint:
        return

    result = auth_store.save_user_api_key(user, provider, clean_value)
    if result.ok:
        st.session_state[fingerprint_key] = fingerprint
        saved_providers = set(st.session_state.get("saved_api_key_providers", []))
        saved_providers.add(provider)
        st.session_state["saved_api_key_providers"] = sorted(saved_providers)
    else:
        st.warning(result.message)


def clear_saved_api_keys_for_user() -> auth_store.AuthResult:
    user = st.session_state.get("authenticated_user", "")
    result = auth_store.clear_user_api_keys(user)
    if result.ok:
        for provider in config.PROVIDER_API_KEYS:
            st.session_state[f"{SESSION_KEY_PREFIX}{provider}"] = ""
            st.session_state[f"mobile_{SESSION_KEY_PREFIX}{provider}"] = ""
            st.session_state.pop(f"saved_api_key_fingerprint_{provider}", None)
        st.session_state["saved_api_key_providers"] = []
        st.session_state["saved_api_keys_loaded_for"] = user
    return result


def clear_single_api_key_for_user(provider: str) -> auth_store.AuthResult:
    user = st.session_state.get("authenticated_user", "")
    st.session_state[f"{SESSION_KEY_PREFIX}{provider}"] = ""
    st.session_state[f"mobile_{SESSION_KEY_PREFIX}{provider}"] = ""
    st.session_state.pop(f"saved_api_key_fingerprint_{provider}", None)
    saved_providers = set(st.session_state.get("saved_api_key_providers", []))
    saved_providers.discard(provider)
    st.session_state["saved_api_key_providers"] = sorted(saved_providers)
    if user:
        return auth_store.save_user_api_key(user, provider, "")
    return auth_store.AuthResult(True, "ล้าง API key แล้ว")


def process_pending_api_key_clear() -> None:
    if st.session_state.pop("clear_all_api_keys_next", False):
        result = clear_saved_api_keys_for_user()
        st.session_state["settings_action_notice"] = result.message
        st.session_state["settings_action_notice_ok"] = result.ok

    provider = st.session_state.pop("clear_api_key_provider_next", None)
    if provider in config.PROVIDER_API_KEYS:
        result = clear_single_api_key_for_user(provider)
        st.session_state["settings_action_notice"] = result.message
        st.session_state["settings_action_notice_ok"] = result.ok


def process_pending_line_settings_clear() -> None:
    if st.session_state.pop("clear_line_settings_next", False):
        result = clear_saved_line_settings_for_user()
        st.session_state["settings_action_notice"] = result.message
        st.session_state["settings_action_notice_ok"] = result.ok


def render_transcription_error_actions(error_text: str, key: str) -> None:
    if "OpenAI API key ไม่ถูกต้อง" not in error_text:
        return
    if st.button("ล้าง OpenAI key ที่บันทึกไว้", key=key, use_container_width=True):
        st.session_state["clear_api_key_provider_next"] = "OpenAI / ChatGPT"
        st.rerun()


def render_provider_error_actions(error_text: str, provider: str, key: str) -> None:
    if "API key" not in error_text:
        return
    if st.button(f"ล้าง key ของ {provider}", key=key, use_container_width=True):
        st.session_state["clear_api_key_provider_next"] = provider
        st.rerun()


def effective_line_token() -> str | None:
    return st.session_state.get(LINE_TOKEN_SESSION_KEY, "").strip() or os.environ.get(LINE_TOKEN_ENV)


def effective_line_recipient_id() -> str | None:
    return st.session_state.get(LINE_RECIPIENT_SESSION_KEY, "").strip() or os.environ.get(LINE_RECIPIENT_ENV)


def load_saved_line_settings_for_user(force: bool = False) -> None:
    user = st.session_state.get("authenticated_user")
    if not user:
        return
    if not force and st.session_state.get("line_settings_loaded_for") == user:
        return

    saved_settings = auth_store.get_user_line_settings(user)
    token = saved_settings.get("channel_access_token", "").strip()
    recipient_id = saved_settings.get("recipient_id", "").strip()
    if token and not st.session_state.get(LINE_TOKEN_SESSION_KEY):
        st.session_state[LINE_TOKEN_SESSION_KEY] = token
    if recipient_id and not st.session_state.get(LINE_RECIPIENT_SESSION_KEY):
        st.session_state[LINE_RECIPIENT_SESSION_KEY] = recipient_id
    if token or recipient_id:
        fingerprint = hashlib.sha256(f"{token}\0{recipient_id}".encode("utf-8")).hexdigest()
        st.session_state["line_settings_fingerprint"] = fingerprint
    st.session_state["line_settings_loaded_for"] = user


def persist_line_settings_for_user(channel_access_token: str, recipient_id: str) -> None:
    user = st.session_state.get("authenticated_user")
    token = channel_access_token.strip()
    recipient = recipient_id.strip()
    if not user or (not token and not recipient):
        return

    fingerprint = hashlib.sha256(f"{token}\0{recipient}".encode("utf-8")).hexdigest()
    if st.session_state.get("line_settings_fingerprint") == fingerprint:
        return

    result = auth_store.save_user_line_settings(user, token, recipient)
    if result.ok:
        st.session_state["line_settings_fingerprint"] = fingerprint
    else:
        st.warning(result.message)


def clear_saved_line_settings_for_user() -> auth_store.AuthResult:
    user = st.session_state.get("authenticated_user", "")
    result = auth_store.clear_user_line_settings(user)
    if result.ok:
        st.session_state[LINE_TOKEN_SESSION_KEY] = ""
        st.session_state[LINE_RECIPIENT_SESSION_KEY] = ""
        st.session_state.pop("line_settings_fingerprint", None)
        st.session_state["line_settings_loaded_for"] = user
    return result


def clean_markdown_for_line(markdown_text: str) -> str:
    text = re.sub(r"```.*?```", "[code block]", markdown_text, flags=re.DOTALL)
    cleaned_lines: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("|"):
            continue
        line = re.sub(r"^#{1,6}\s*", "", line)
        line = re.sub(r"\*\*(.*?)\*\*", r"\1", line)
        line = re.sub(r"`([^`]+)`", r"\1", line)
        cleaned_lines.append(line)
        if len("\n".join(cleaned_lines)) > 3600:
            break
    return "\n".join(cleaned_lines).strip()


def build_line_summary_message(result_info: dict[str, str]) -> str:
    body = clean_markdown_for_line(result_info.get("final_output", ""))
    if len(body) > 3600:
        body = body[:3600].rstrip() + "\n...[ตัดต่อเพื่อให้เหมาะกับ LINE]"
    return (
        "AI Research Office: งานเสร็จแล้ว\n"
        f"โหมด: {result_info.get('mode_label', '-')}\n"
        f"หัวข้อ: {result_info.get('display_command', '-')}\n\n"
        f"{body or 'เปิดแอปเพื่อดูรายงานฉบับเต็ม'}\n\n"
        "ดูรายงานเต็มและไฟล์แนบได้ในแอป"
    )


def split_line_messages(text: str) -> list[dict[str, str]]:
    chunks: list[str] = []
    remaining = text.strip()
    max_total = LINE_TEXT_LIMIT * LINE_MAX_MESSAGES
    if len(remaining) > max_total:
        remaining = remaining[: max_total - 80].rstrip() + "\n...[ตัดข้อความเพราะเกินขนาดที่ LINE รองรับ]"

    while remaining:
        chunk = remaining[:LINE_TEXT_LIMIT]
        if len(remaining) > LINE_TEXT_LIMIT:
            split_at = max(chunk.rfind("\n"), chunk.rfind(" "))
            if split_at > LINE_TEXT_LIMIT * 0.6:
                chunk = remaining[:split_at].rstrip()
        chunks.append(chunk)
        remaining = remaining[len(chunk):].lstrip()
        if len(chunks) >= LINE_MAX_MESSAGES:
            break

    return [{"type": "text", "text": chunk} for chunk in chunks if chunk]


def send_line_push_message(text: str) -> tuple[bool, str]:
    token = effective_line_token()
    recipient_id = effective_line_recipient_id()
    if not token or not recipient_id:
        return False, "ยังไม่ได้ตั้งค่า LINE Channel Access Token หรือ Recipient ID"

    payload = {
        "to": recipient_id,
        "messages": split_line_messages(text),
        "notificationDisabled": False,
    }
    if not payload["messages"]:
        return False, "ไม่มีข้อความสำหรับส่งเข้า LINE"

    request = urllib.request.Request(
        LINE_PUSH_ENDPOINT,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "X-Line-Retry-Key": str(uuid.uuid4()),
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            if 200 <= response.status < 300:
                return True, "ส่งสรุปเข้า LINE แล้ว"
            return False, f"LINE ตอบกลับ HTTP {response.status}"
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        try:
            detail = json.loads(body).get("message", body)
        except Exception:
            detail = body
        return False, f"ส่ง LINE ไม่สำเร็จ: HTTP {exc.code} - {detail}"
    except Exception as exc:
        return False, f"ส่ง LINE ไม่สำเร็จ: {type(exc).__name__}: {exc}"


def build_llm_map(model_settings: dict[str, tuple[str, str]], google_grounding: bool = False):
    llms = {}
    missing_keys = []

    for key, (provider, model) in model_settings.items():
        api_key = effective_api_key(provider)
        if not api_key:
            missing_keys.append((provider, config.PROVIDER_API_KEYS[provider]))
            continue
        llms[key] = config.get_llm(
            provider,
            model,
            api_key=api_key,
            google_grounding=google_grounding,
        )

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


def friendly_transcription_error(exc: Exception) -> str:
    error_text = str(exc)
    error_type = type(exc).__name__
    lower_text = error_text.lower()

    if "invalid_api_key" in lower_text or "incorrect api key" in lower_text or "401" in lower_text:
        return (
            "ถอดเสียงไม่สำเร็จ: OpenAI API key ไม่ถูกต้องหรือถูกยกเลิกแล้ว "
            "ให้เปิด sidebar > `API keys ของผู้ใช้นี้` แล้วแก้ช่อง `OpenAI / ChatGPT` "
            "หรือกดล้าง API keys ที่บันทึกไว้แล้วใส่ key ใหม่"
        )
    if error_type == "PermissionDeniedError" or "403" in lower_text or "permission" in lower_text:
        return (
            "ถอดเสียงไม่สำเร็จ: OpenAI key นี้ไม่มีสิทธิ์ใช้การถอดเสียง (403) "
            "มักเกิดจากสร้าง key แบบ Restricted ให้เข้า platform.openai.com > API keys "
            "แล้วสร้าง key ใหม่แบบ Permissions: All หรือเปิดสิทธิ์ Model capabilities เป็น Write"
        )
    if "insufficient_quota" in lower_text or "quota" in lower_text or "billing" in lower_text:
        return (
            "ถอดเสียงไม่สำเร็จ: OpenAI key นี้ไม่มี quota หรือยังไม่ได้เปิด billing "
            "กรุณาตรวจบัญชี OpenAI หรือใช้การพิมพ์แทน"
        )
    if "rate limit" in lower_text or "429" in lower_text:
        return "ถอดเสียงไม่สำเร็จ: OpenAI rate limit ชั่วคราว กรุณารอสักครู่แล้วลองใหม่"
    if "timeout" in lower_text:
        return "ถอดเสียงไม่สำเร็จ: เชื่อมต่อ OpenAI นานเกินไป กรุณาลองใหม่หรืออัปโหลดไฟล์เสียงที่สั้นลง"

    return f"ถอดเสียงไม่สำเร็จ: {error_type}. กรุณาตรวจ OpenAI API key หรือใช้การพิมพ์แทน"


def audio_file_fingerprint(audio_file) -> str:
    try:
        data = audio_file.getvalue()
    except Exception:
        data = bytes(str(audio_file), "utf-8")
    name = getattr(audio_file, "name", "audio") or "audio"
    return hashlib.sha256(name.encode("utf-8") + b"\0" + data).hexdigest()


def transcribe_audio(audio_file) -> tuple[str | None, str | None]:
    api_key = effective_api_key("OpenAI / ChatGPT")
    if not api_key:
        return None, "ยังไม่ได้ตั้ง OpenAI API key จึงถอดเสียงไม่ได้ กรุณาใส่ key ในเมนูตั้งค่า/API keys ก่อน"

    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        audio_bytes = audio_file.getvalue()
        if not audio_bytes:
            return None, "ไฟล์เสียงว่างเปล่า กรุณากดอัดเสียงใหม่อีกครั้ง"
        if len(audio_bytes) > 25 * 1024 * 1024:
            return None, "ไฟล์เสียงใหญ่เกิน 25 MB กรุณาอัดใหม่ให้สั้นลง"

        file_name = getattr(audio_file, "name", "voice_input.wav") or "voice_input.wav"
        if "." not in file_name:
            mime_type = (getattr(audio_file, "type", "") or "audio/wav").split(";")[0]
            file_name += mimetypes.guess_extension(mime_type) or ".wav"
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=(file_name, audio_bytes),
        )
        text = getattr(transcript, "text", str(transcript))
        text = truncate_text(text.strip(), limit=4000)
        if not text:
            return None, "ถอดเสียงแล้วแต่ไม่พบข้อความ กรุณาลองพูดใหม่ให้ชัดขึ้น"
        return text, None
    except Exception as exc:
        return None, friendly_transcription_error(exc)


def get_office_agent(agent_key: str) -> dict[str, str]:
    for agent in OFFICE_AGENTS:
        if agent["key"] == agent_key:
            return agent
    return OFFICE_AGENTS[0]


def render_agent_speech_player(text: str, key: str, auto_play: bool = False) -> None:
    clean_text = text.strip()
    if not clean_text:
        return

    element_id = re.sub(r"[^a-zA-Z0-9_-]", "", key)
    status_id = f"{element_id}-status"
    speech_id = hashlib.sha256(f"{key}\0{clean_text}".encode("utf-8")).hexdigest()[:18]
    storage_key = f"ai_research_office_spoken_{speech_id}"
    element_id_json = json.dumps(element_id)
    status_id_json = json.dumps(status_id)
    text_json = json.dumps(clean_text, ensure_ascii=False)
    auto_play_json = json.dumps(auto_play)
    storage_key_json = json.dumps(storage_key)
    html = f"""
    <!doctype html>
    <html>
    <body style="margin:0;background:transparent;">
      <button id="{element_id}" style="
        border:1px solid rgba(56,189,248,.45);
        border-radius:8px;
        background:rgba(14,165,233,.12);
        color:#0f172a;
        font:600 13px system-ui, sans-serif;
        padding:8px 12px;
        cursor:pointer;
      ">🔊 ฟังเสียงตอบจาก Agent</button>
      <span id="{status_id}" style="margin-left:8px;color:rgba(148,163,184,.9);font:500 12px system-ui,sans-serif;"></span>
      <script>
        (function() {{
          const button = document.getElementById({element_id_json});
          const status = document.getElementById({status_id_json});
          const text = {text_json};
          const autoPlay = {auto_play_json};
          const storageKey = {storage_key_json};

          function speak(markAuto) {{
            if (!("speechSynthesis" in window)) {{
              button.textContent = "เบราว์เซอร์นี้ยังไม่รองรับเสียงอ่าน";
              return;
            }}
            if (markAuto) {{
              window.sessionStorage.setItem(storageKey, "1");
            }}
            window.speechSynthesis.cancel();
            const utterance = new SpeechSynthesisUtterance(text);
            utterance.lang = "th-TH";
            utterance.rate = .96;
            utterance.pitch = 1.02;
            utterance.onstart = function() {{
              button.textContent = "กำลังอ่านเสียง Agent...";
              status.textContent = "";
            }};
            utterance.onend = function() {{
              button.textContent = "🔊 ฟังเสียงตอบจาก Agent";
              status.textContent = "";
            }};
            utterance.onerror = function() {{
              button.textContent = "🔊 ฟังเสียงตอบจาก Agent";
              status.textContent = "กดฟังอีกครั้งได้";
            }};
            window.speechSynthesis.speak(utterance);
          }}

          button.addEventListener("click", function() {{
            window.sessionStorage.removeItem(storageKey);
            speak(false);
          }});

          if (autoPlay && !window.sessionStorage.getItem(storageKey)) {{
            window.setTimeout(function() {{ speak(true); }}, 450);
          }}
        }})();
      </script>
    </body>
    </html>
    """
    render_html_component(html, height=48, scrolling=False)


def render_audio_input_help() -> None:
    with st.expander("โหมดเสียง", expanded=False):
        st.markdown(
            """
            - ค่าเริ่มต้นจะไม่เปิดไมค์ จึงไม่ขอสิทธิ์ไมโครโฟน
            - ถ้าเปิด `ใช้ไมค์ในแอป` browser จะถามสิทธิ์ตามกฎความปลอดภัย และข้ามขั้นนี้ไม่ได้
            - ถ้าไม่อยากให้ browser ขอสิทธิ์ ให้อัปโหลดไฟล์เสียงแทน เช่น `.wav`, `.mp3`, `.m4a`, `.ogg`, `.webm`
            - การถอดเสียงยังต้องใช้ OpenAI API key ที่ถูกต้องในช่อง `OpenAI / ChatGPT`
            """
        )


def clear_agent_call_draft() -> None:
    for key in ["agent_call_draft", "agent_call_draft_source", "agent_call_transcript_notice", "agent_call_pending_text"]:
        st.session_state.pop(key, None)


def reset_agent_call_session(keep_agent: bool = True) -> None:
    exact_keys = {
        "agent_call_history",
        "agent_call_error",
        "agent_call_voice_turn",
        "agent_call_text_turn",
        "agent_call_draft",
        "agent_call_draft_source",
        "agent_call_transcript_notice",
        "agent_call_pending_text",
        "agent_call_clear_draft_next",
        "agent_call_processed_audio",
        "agent_call_retry_text",
    }
    if not keep_agent:
        exact_keys.add("agent_call_selected_key")
        exact_keys.add("agent_call_agent")

    for key in list(st.session_state.keys()):
        if (
            key in exact_keys
            or key.startswith("agent_call_audio_file_")
            or key.startswith("agent_call_voice_")
            or key.startswith("agent_call_chat_input_")
        ):
            st.session_state.pop(key, None)


def agent_call_greeting(agent: dict[str, str], mode_label: str) -> str:
    return (
        f"สวัสดีครับ ผม {agent['name']} รับสายอยู่ครับ "
        f"เล่าโจทย์งานแบบสั้น ๆ ได้เลย เดี๋ยวผมช่วยถามต่อและจัด brief สำหรับโหมด {mode_label} ให้ครับ"
    )


def start_agent_call(agent: dict[str, str], mode_label: str) -> None:
    reset_agent_call_session(keep_agent=True)
    st.session_state["agent_call_history"] = [
        {"role": "agent", "agent": agent["name"], "text": agent_call_greeting(agent, mode_label)}
    ]


def render_agent_call_header(agent: dict[str, str], provider: str, model: str, history: list[dict[str, str]]) -> None:
    turns = sum(1 for item in history if item.get("role") == "user")
    status = "พร้อมรับสาย" if turns == 0 else "กำลังคุยอยู่"
    if turns > 0 and history and history[-1].get("role") == "agent":
        status = "Agent ตอบแล้ว"
    st.markdown(
        f"""
        <div style="
            border:1px solid rgba(148,163,184,.32);
            border-radius:8px;
            padding:12px 14px;
            background:linear-gradient(135deg, rgba(14,165,233,.13), rgba(34,197,94,.09));
            margin:.25rem 0 .8rem;
        ">
            <div style="display:flex;gap:12px;align-items:center;justify-content:space-between;flex-wrap:wrap;">
                <div>
                    <div style="font-size:1.05rem;font-weight:750;">{escape(agent["icon"])} สายกับ {escape(agent["name"])}</div>
                    <div style="color:rgba(226,232,240,.76);font-size:.92rem;line-height:1.45;">{escape(agent["role"])}</div>
                </div>
                <div style="text-align:right;font-size:.84rem;color:rgba(226,232,240,.72);line-height:1.55;">
                    <div>{escape(status)} · {turns} รอบ</div>
                    <div>{escape(provider)} / {escape(model)}</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_agent_call_history(history: list[dict[str, str]], agent: dict[str, str]) -> None:
    if not history:
        st.info("เริ่มคุยได้เลย พูดหรือพิมพ์เหมือนโทรบอกงานกับผู้ช่วยคนหนึ่ง")
        return

    for item in history[-12:]:
        text = item.get("text", "").strip()
        if not text:
            continue
        if item.get("role") == "user":
            if hasattr(st, "chat_message"):
                with st.chat_message("user"):
                    st.markdown(text)
            else:
                st.markdown(f"**คุณ:** {text}")
        else:
            if hasattr(st, "chat_message"):
                with st.chat_message("assistant", avatar=agent["icon"]):
                    st.markdown(text)
            else:
                st.markdown(f"**{agent['name']}:** {text}")


def generate_agent_call_reply(
    agent: dict[str, str],
    mode_label: str,
    user_text: str,
    history: list[dict[str, str]],
    provider: str,
    model: str,
) -> tuple[str | None, str | None]:
    api_key = effective_api_key(provider)
    if not api_key:
        env_name = config.PROVIDER_API_KEYS[provider]
        return None, (
            f"ยังไม่มี API key สำหรับ {provider} (`{env_name}`) จึงให้ Agent ตอบกลับไม่ได้ "
            "กรุณาใส่ key ใน sidebar > `API keys ของผู้ใช้นี้` หรือเปลี่ยนโมเดลของ Agent"
        )

    try:
        from litellm import completion

        messages: list[dict[str, str]] = [
            {
                "role": "system",
                "content": (
                    "คุณคือเอเจนต์ใน AI Research Office ที่กำลังคุยโทรศัพท์กับผู้ใช้ "
                    f"ชื่อเอเจนต์: {agent['name']} บทบาท: {agent['role']} โหมดงาน: {mode_label}. "
                    "ตอบเป็นภาษาไทยเหมือนคนรับสายทำงานจริง สุภาพ เป็นกันเอง และเข้าใจง่าย "
                    "อย่าใช้ภาษาทางการเกินไป อย่าใช้ศัพท์เทคนิคถ้าไม่จำเป็น และห้ามตอบเหมือนรายงาน "
                    "ทุกครั้งให้ทวนความเข้าใจสั้น ๆ ก่อนหนึ่งประโยค แล้วช่วยพาผู้ใช้ไปขั้นต่อไป "
                    "ตอบครั้งละ 2-4 ประโยคเท่านั้น ถ้าข้อมูลยังไม่พอให้ถามคำถามเดียวที่สำคัญที่สุด "
                    "ถ้าข้อมูลพอแล้วให้บอกว่าพร้อมสรุปเป็น brief ส่งให้ทีมต่อ และสรุปเป็นภาษาคนสั้น ๆ "
                    "อย่าใช้ตาราง และอย่าขึ้นหัวข้อยาว"
                ),
            }
        ]
        for item in history[-8:]:
            role = "assistant" if item.get("role") == "agent" else "user"
            speaker = item.get("agent", "ผู้ใช้") if role == "assistant" else "ผู้ใช้"
            messages.append({"role": role, "content": f"{speaker}: {item.get('text', '')}"})
        messages.append({"role": "user", "content": user_text})

        response = completion(
            model=f"{config.PROVIDER_PREFIXES[provider]}{model}",
            messages=messages,
            api_key=api_key,
            temperature=0.55,
            max_tokens=360,
            timeout=45,
        )
        message = response.choices[0].message
        reply = message.get("content") if isinstance(message, dict) else getattr(message, "content", "")
        reply = truncate_text((reply or "").strip(), limit=1800)
        if not reply:
            return None, "Agent ตอบกลับเป็นข้อความว่าง กรุณาลองส่งคำสั่งอีกครั้ง"
        return reply, None
    except Exception as exc:
        error_text = str(exc)
        lower_text = error_text.lower()
        if "invalid_api_key" in lower_text or "incorrect api key" in lower_text or "401" in lower_text:
            return None, f"Agent ตอบกลับไม่ได้: API key ของ {provider} ไม่ถูกต้อง กรุณาล้าง key เดิมแล้วใส่ใหม่"
        if "rate limit" in lower_text or "429" in lower_text:
            return None, f"Agent ตอบกลับไม่ได้: {provider} rate limit ชั่วคราว กรุณารอสักครู่แล้วลองใหม่"
        return None, f"Agent ตอบกลับไม่สำเร็จ: {type(exc).__name__}. กรุณาตรวจ API key/model แล้วลองใหม่"


def submit_agent_call_turn(
    user_text: str,
    agent: dict[str, str],
    mode_label: str,
    provider: str,
    model: str,
) -> bool:
    clean_text = user_text.strip()
    if not clean_text:
        st.session_state["agent_call_error"] = "ยังไม่มีข้อความในสาย กรุณาพูดหรือพิมพ์ก่อนส่ง"
        return False

    history = st.session_state.setdefault("agent_call_history", [])
    retrying_last_failed_turn = (
        st.session_state.get("agent_call_retry_text", "").strip() == clean_text
        and bool(st.session_state.get("agent_call_error"))
        and bool(history)
        and history[-1].get("role") == "user"
        and history[-1].get("text", "").strip() == clean_text
    )
    prior_history = list(history[:-1] if retrying_last_failed_turn else history)
    reply, error = generate_agent_call_reply(agent, mode_label, clean_text, prior_history, provider, model)
    if retrying_last_failed_turn:
        history = history[:-1]
    history.append({"role": "user", "text": clean_text})
    if error:
        st.session_state["agent_call_error"] = error
        st.session_state["agent_call_retry_text"] = clean_text
        st.session_state["agent_call_history"] = history
        return False
    else:
        st.session_state.pop("agent_call_error", None)
        st.session_state.pop("agent_call_retry_text", None)
        history.append({"role": "agent", "agent": agent["name"], "text": reply or ""})
    st.session_state["agent_call_history"] = history
    return True


def queue_agent_call_text(text: str) -> None:
    clean_text = text.strip()
    if clean_text:
        st.session_state["agent_call_pending_text"] = clean_text


def run_agent_call_turn(
    text: str,
    agent: dict[str, str],
    mode_label: str,
    provider: str,
    model: str,
    spinner_label: str | None = None,
) -> bool:
    label = spinner_label or f"{agent['name']} กำลังตอบ..."
    with st.spinner(label):
        return submit_agent_call_turn(text, agent, mode_label, provider, model)


def run_agent_call_audio_turn(
    audio_file,
    audio_fingerprint: str,
    agent: dict[str, str],
    mode_label: str,
    provider: str,
    model: str,
) -> bool:
    st.session_state["agent_call_processed_audio"] = audio_fingerprint
    transcript_text, transcript_error = transcribe_audio(audio_file)
    if transcript_error:
        st.session_state["agent_call_error"] = transcript_error
        st.session_state.pop("agent_call_retry_text", None)
        st.session_state.pop("agent_call_transcript_notice", None)
        return False

    sent = submit_agent_call_turn(transcript_text or "", agent, mode_label, provider, model)
    st.session_state["agent_call_voice_turn"] = st.session_state.get("agent_call_voice_turn", 0) + 1
    st.session_state["agent_call_transcript_notice"] = (
        "Agent ตอบจากเสียงแล้ว"
        if sent
        else "ถอดเสียงแล้วและส่งเข้าแชตแล้ว แต่ Agent ยังตอบไม่ได้"
    )
    return sent


def build_agent_call_brief(agent: dict[str, str], mode_label: str, history: list[dict[str, str]]) -> str:
    lines = [
        "ใช้บทสนทนาโทรสั่งงานนี้เป็น brief หลักสำหรับทีม Agent",
        f"- โหมดงาน: {mode_label}",
        f"- Agent ที่รับสาย: {agent['name']} ({agent['role']})",
        "- วิธีทำงาน: สกัดเจตนาจริงของผู้ใช้ ใช้ภาษาคนเข้าใจง่าย และถามต่อเฉพาะจุดที่จำเป็น",
        "",
        "## บันทึกบทสนทนา",
    ]
    seen_user_turn = False
    for item in history:
        if item.get("role") == "user":
            seen_user_turn = True
        elif not seen_user_turn:
            continue
        speaker = "ผู้ใช้" if item.get("role") == "user" else item.get("agent", "Agent")
        lines.append(f"- {speaker}: {item.get('text', '').strip()}")
    lines.extend(
        [
            "",
            "## คำสั่ง",
            "สกัดเป้าหมาย ข้อกำหนด ขอบเขตงาน ข้อจำกัด และ next steps จากบทสนทนานี้ แล้วดำเนินงานให้ครบตามโหมดที่เลือก โดยอธิบายผลลัพธ์เป็นภาษาไทยที่คนทั่วไปเข้าใจง่าย",
        ]
    )
    return truncate_text("\n".join(lines), limit=6000)


def render_agent_call_mode(
    mode_label: str,
    default_provider: str,
    default_model: str,
    research_model_settings: dict[str, tuple[str, str]],
    build_model_settings: dict[str, tuple[str, str]],
    director_provider: str,
    director_model: str,
) -> None:
    with st.expander("📞 โทรสั่งงาน Agent", expanded=False):
        if st.session_state.pop("agent_call_clear_draft_next", False):
            clear_agent_call_draft()

        st.caption("คุยสั่งงานเป็นรอบ ๆ เหมือนโทรหาเพื่อนร่วมงาน แล้วค่อยส่ง brief เข้าทีม Agent")

        agent_labels = [f"{agent['icon']} {agent['name']} — {agent['role']}" for agent in OFFICE_AGENTS]
        selected_label = st.selectbox("โทรหา Agent", agent_labels, key="agent_call_agent")
        selected_index = agent_labels.index(selected_label)
        agent = OFFICE_AGENTS[selected_index]
        if st.session_state.get("agent_call_selected_key") != agent["key"]:
            start_agent_call(agent, mode_label)
            st.session_state["agent_call_selected_key"] = agent["key"]

        provider, model = model_for_agent(
            agent["key"],
            default_provider,
            default_model,
            research_model_settings,
            build_model_settings,
            director_provider,
            director_model,
        )

        history = st.session_state.setdefault("agent_call_history", [])
        if not history:
            start_agent_call(agent, mode_label)
            history = st.session_state.setdefault("agent_call_history", [])
        render_agent_call_header(agent, provider, model, history)

        pending_text = st.session_state.pop("agent_call_pending_text", "").strip()
        if pending_text:
            run_agent_call_turn(pending_text, agent, mode_label, provider, model)
            st.rerun()

        call_cols = st.columns([1, 1])
        if call_cols[0].button("เริ่มสายใหม่", use_container_width=True):
            start_agent_call(agent, mode_label)
            st.rerun()
        if call_cols[1].button("ล้างข้อความที่กำลังจะส่ง", use_container_width=True):
            clear_agent_call_draft()
            st.rerun()

        has_user_turn = any(item.get("role") == "user" for item in history)
        auto_agent_speech = st.checkbox(
            "อ่านเสียงตอบจาก Agent อัตโนมัติ",
            value=False,
            key="agent_call_auto_speak",
        )

        render_agent_call_history(history, agent)
        last_agent_reply = next((item for item in reversed(history) if item.get("role") == "agent"), None)
        if last_agent_reply and has_user_turn:
            render_agent_speech_player(
                last_agent_reply.get("text", ""),
                f"agent-call-speak-{len(history)}",
                auto_play=auto_agent_speech and has_user_turn and history[-1].get("role") == "agent",
            )

        call_error = st.session_state.get("agent_call_error")
        if call_error:
            st.warning(call_error)
            render_transcription_error_actions(call_error, "clear_openai_key_from_call_error")
            render_provider_error_actions(call_error, provider, f"clear_provider_key_from_call_error_{agent['key']}")
            retry_text = st.session_state.get("agent_call_retry_text", "").strip()
            if retry_text and st.button("ลองส่งข้อความล่าสุดอีกครั้ง", use_container_width=True):
                run_agent_call_turn(
                    retry_text,
                    agent,
                    mode_label,
                    provider,
                    model,
                    spinner_label=f"{agent['name']} กำลังลองตอบอีกครั้ง...",
                )
                st.rerun()

        if not effective_api_key("OpenAI / ChatGPT"):
            st.caption("หมายเหตุ: การพูดด้วยเสียงต้องใช้ OpenAI API key สำหรับถอดเสียง แต่ยังพิมพ์คุยกับ Agent ได้")

        render_audio_input_help()
        auto_voice_turn = st.checkbox(
            "ส่งเสียงให้ Agent อัตโนมัติหลังอัด/อัปโหลด",
            value=True,
            key="agent_call_auto_voice_turn",
        )
        use_call_mic = st.checkbox(
            "ใช้ไมค์ในแอป",
            value=False,
            key="agent_call_use_browser_mic",
            help="ถ้าเปิด browser จะถามสิทธิ์ไมโครโฟนครั้งแรกตามกฎความปลอดภัย",
        )
        call_audio = None
        if use_call_mic:
            if hasattr(st, "audio_input"):
                audio_key = f"agent_call_voice_{st.session_state.get('agent_call_voice_turn', 0)}"
                call_audio = st.audio_input("กดพูดในสาย", key=audio_key)
            else:
                st.info("Streamlit เวอร์ชันนี้ยังไม่รองรับการอัดเสียงผ่าน browser")
        uploaded_call_audio = st.file_uploader(
            "หรืออัปโหลดไฟล์เสียงในสาย",
            type=AUDIO_UPLOAD_TYPES,
            key=f"agent_call_audio_file_{st.session_state.get('agent_call_voice_turn', 0)}",
        )
        selected_call_audio = call_audio or uploaded_call_audio
        if selected_call_audio is not None:
            st.audio(selected_call_audio)
            selected_audio_fingerprint = audio_file_fingerprint(selected_call_audio)
            already_processed_audio = st.session_state.get("agent_call_processed_audio") == selected_audio_fingerprint
            if auto_voice_turn and not already_processed_audio:
                with st.spinner("กำลังถอดเสียงและให้ Agent ตอบ..."):
                    run_agent_call_audio_turn(
                        selected_call_audio,
                        selected_audio_fingerprint,
                        agent,
                        mode_label,
                        provider,
                        model,
                    )
                st.rerun()
            call_audio_error = st.session_state.get("agent_call_error", "")
            if (
                already_processed_audio
                and ("ถอดเสียง" in call_audio_error or "OpenAI API key" in call_audio_error)
                and st.button("ลองถอดเสียงไฟล์นี้อีกครั้ง", use_container_width=True)
            ):
                st.session_state.pop("agent_call_processed_audio", None)
                st.rerun()
            if not auto_voice_turn and st.button("ถอดเสียงแล้วส่งให้ Agent ตอบ", use_container_width=True):
                with st.spinner("กำลังถอดเสียงและให้ Agent ตอบ..."):
                    run_agent_call_audio_turn(
                        selected_call_audio,
                        selected_audio_fingerprint,
                        agent,
                        mode_label,
                        provider,
                        model,
                    )
                st.rerun()

        transcript_notice = st.session_state.get("agent_call_transcript_notice")
        if transcript_notice:
            st.success(transcript_notice)

        if hasattr(st, "chat_input"):
            chat_text = st.chat_input(
                "พิมพ์คุยกับ Agent แล้วกด Enter",
                key=f"agent_call_chat_input_{agent['key']}",
            )
            if chat_text:
                st.session_state["agent_call_text_turn"] = st.session_state.get("agent_call_text_turn", 0) + 1
                run_agent_call_turn(chat_text, agent, mode_label, provider, model)
                st.rerun()
        else:
            st.text_area(
                "ข้อความที่จะพูดกับ Agent",
                key="agent_call_draft",
                height=92,
                placeholder="พิมพ์เหมือนคุยโทรศัพท์ เช่น ช่วยดูตลาดรถเช่าให้หน่อย แล้วทำแผนเว็บที่ใช้ได้จริง",
            )
            draft_cols = st.columns([2, 1])
            if draft_cols[0].button("ส่งข้อความนี้ให้ Agent ตอบ", type="primary", use_container_width=True):
                sent = submit_agent_call_turn(st.session_state.get("agent_call_draft", ""), agent, mode_label, provider, model)
                if sent:
                    st.session_state["agent_call_text_turn"] = st.session_state.get("agent_call_text_turn", 0) + 1
                    st.session_state["agent_call_clear_draft_next"] = True
                st.rerun()
            if draft_cols[1].button("ล้าง", use_container_width=True):
                st.session_state["agent_call_clear_draft_next"] = True
                st.rerun()

        if history:
            st.caption("คำพูดลัดในสาย")
            quick_cols = st.columns(len(CALL_QUICK_TURNS))
            for index, (label, prompt) in enumerate(CALL_QUICK_TURNS):
                if quick_cols[index].button(label, key=f"agent_call_quick_{index}", use_container_width=True):
                    run_agent_call_turn(prompt, agent, mode_label, provider, model)
                    st.rerun()

        has_user_turn = any(item.get("role") == "user" for item in history)
        if has_user_turn:
            brief = build_agent_call_brief(agent, mode_label, history)
            st.text_area("Brief จากสายนี้", value=brief, height=170, disabled=True)
            send_cols = st.columns(2)
            if send_cols[0].button("ส่ง brief นี้เป็นคำสั่งหลัก", use_container_width=True):
                st.session_state["call_prompt_to_send"] = brief
                st.session_state["call_command_notice"] = agent["name"]
                st.rerun()
            if send_cols[1].button("ส่งแล้วเริ่มงานทันที", use_container_width=True):
                st.session_state["call_prompt_to_send"] = brief
                st.session_state["call_command_notice"] = agent["name"]
                st.session_state["auto_submit_call"] = True
                st.rerun()


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

        if not effective_api_key("OpenAI / ChatGPT"):
            st.info("การถอดเสียงต้องใช้ OpenAI API key กรุณาใส่ key ก่อนใช้งานเสียงพูด")

        render_audio_input_help()
        use_voice_mic = st.checkbox(
            "ใช้ไมค์แทนการอัปโหลดเสียง",
            value=False,
            key="voice_use_browser_mic",
            help="ถ้าเปิด browser จะถามสิทธิ์ไมโครโฟนครั้งแรกตามกฎความปลอดภัย",
        )
        audio_capture = None
        if use_voice_mic:
            if hasattr(st, "audio_input"):
                audio_capture = st.audio_input("พูดแทนการพิมพ์", key="voice_input")
            else:
                st.info("Streamlit เวอร์ชันนี้ยังไม่รองรับการอัดเสียงผ่าน browser")
        audio_upload = st.file_uploader(
            "หรืออัปโหลดไฟล์เสียงแทนการพิมพ์",
            type=AUDIO_UPLOAD_TYPES,
            key="voice_file",
        )
        audio_file = audio_capture or audio_upload

        if audio_file is not None:
            st.audio(audio_file)
            if st.button("1) ถอดเสียงเป็นร่างคำสั่ง", use_container_width=True):
                transcript_text, transcript_error = transcribe_audio(audio_file)
                if transcript_error:
                    st.session_state["voice_transcript_error"] = transcript_error
                    st.session_state.pop("voice_transcript", None)
                else:
                    st.session_state["voice_transcript"] = transcript_text
                    st.session_state.pop("voice_transcript_error", None)
                    st.session_state.pop("voice_draft", None)
                    st.session_state.pop("voice_draft_source", None)
                st.rerun()

        voice_error = st.session_state.get("voice_transcript_error")
        if voice_error:
            st.warning(voice_error)
            render_transcription_error_actions(voice_error, "clear_openai_key_from_voice_error")

        voice_text = st.session_state.get("voice_transcript", "").strip()
        if voice_text:
            if st.session_state.get("voice_draft_source") != voice_text:
                st.session_state["voice_draft"] = voice_text
                st.session_state["voice_draft_source"] = voice_text
            voice_draft = st.text_area(
                "ร่างคำสั่งจากเสียง",
                height=120,
                key="voice_draft",
            )
            voice_cols = st.columns(2)
            if voice_cols[0].button("2) ส่งร่างนี้ให้ Agent", use_container_width=True):
                if voice_draft.strip():
                    st.session_state["voice_prompt_to_send"] = voice_draft.strip()
                    st.session_state["voice_command_notice"] = voice_draft.strip()
                    st.session_state["auto_submit_voice"] = True
                    st.rerun()
                else:
                    st.warning("ร่างคำสั่งจากเสียงยังว่างอยู่")
            if voice_cols[1].button("ล้างเสียงนี้", use_container_width=True):
                for key in ["voice_transcript", "voice_transcript_error", "voice_draft", "voice_draft_source"]:
                    st.session_state.pop(key, None)
                st.rerun()

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


def build_agent_skill_context(mode_key: str, google_grounding: bool) -> str:
    skills = AGENT_SKILL_CATALOG["research" if mode_key == "research" else "build"]
    skill_lines = "\n".join(f"- {name}: {detail}" for name, detail in skills)
    grounding_note = (
        "เปิด Google Grounding แล้ว: ถ้า agent ใช้ Google Gemini ให้ค้นข้อมูลล่าสุดเมื่อคำถามพึ่งพาข่าว ราคา กฎ รุ่นสินค้า หรือข้อมูลที่เปลี่ยนเร็ว"
        if google_grounding
        else "ยังไม่ได้เปิด Google Grounding: ถ้างานต้องใช้ข้อมูลล่าสุด ให้ระบุข้อจำกัดและแนะนำให้เปิด Google Grounding ก่อนฟันธง"
    )
    return (
        "## Agent Skill Boost\n"
        "ให้ทีม agent ทำงานแบบ proactive ไม่รอข้อมูลสำเร็จรูปจากผู้ใช้อย่างเดียว:\n"
        f"{grounding_note}\n\n"
        "สกิลเฉพาะ agent ที่ต้องใช้ในงานนี้:\n"
        f"{skill_lines}\n\n"
        "ข้อกำหนดผลลัพธ์เพิ่มเติม:\n"
        "- แสดง assumption หรือข้อมูลที่ยังไม่แน่ชัดด้วย ⚠️\n"
        "- เสนอคำค้น/แหล่งข้อมูล/ขั้นตอนตรวจเพิ่มเมื่อข้อมูลยังไม่พอ\n"
        "- ใส่หัวข้อ `## 🧩 คำแนะนำเพิ่มสกิล/วิธีทำงานต่อ` ในรายงานสุดท้าย"
    )


def render_agent_skill_recommendations(mode_key: str, google_grounding: bool) -> None:
    skills = AGENT_SKILL_CATALOG["research" if mode_key == "research" else "build"]
    with st.expander("🧩 สกิล Agent และคำแนะนำการทำงาน", expanded=False):
        if google_grounding:
            st.success("Google Grounding พร้อมใช้กับ agent ที่เลือก Google Gemini")
        else:
            st.info("ถ้างานต้องอ้างอิงข่าว/ราคา/ข้อมูลล่าสุด แนะนำเปิด Google Grounding ใน sidebar")
        for name, detail in skills:
            st.markdown(f"- **{name}** — {detail}")


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
            if key.startswith("line_"):
                st.session_state.pop(key, None)
            elif (
                key.startswith(SESSION_KEY_PREFIX)
                or key.startswith(f"mobile_{SESSION_KEY_PREFIX}")
                or key.startswith("saved_api_key_")
            ):
                st.session_state[key] = ""
        st.session_state.pop("authenticated_user", None)
        st.session_state.pop("saved_api_keys_loaded_for", None)
        st.session_state.pop("saved_api_key_providers", None)
        st.session_state.pop("line_settings_loaded_for", None)
        st.rerun()


def render_quick_mobile_settings() -> None:
    with st.expander("📱 ตั้งค่าด่วนสำหรับมือถือ", expanded=False):
        st.caption("กรอก API key ตรงนี้ได้เลย ไม่ต้องเปิด sidebar ระบบจะบันทึกไว้กับบัญชีนี้")
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
                persist_api_key_for_user(provider, value)

            status_label = "พร้อม" if effective_api_key(provider) else "ยังไม่มี"
            status_cols[index % 3].metric(provider, status_label)

        action_cols = st.columns(2)
        if action_cols[0].button("ใช้โหมดประหยัด quota", use_container_width=True):
            st.session_state["economy_mode"] = True
            st.rerun()
        if action_cols[1].button("เปิดสร้างไฟล์ Build", use_container_width=True):
            st.session_state["write_files_mode"] = True
            st.rerun()

        if st.button("ล้าง API keys ที่บันทึกไว้", use_container_width=True, key="mobile_clear_api_keys"):
            st.session_state["clear_all_api_keys_next"] = True
            st.rerun()


def render_line_settings_panel() -> None:
    with st.expander("📲 ส่งสรุปเข้า LINE", expanded=False):
        st.caption(
            "ใช้ LINE Messaging API ผ่าน LINE Official Account. "
            "LINE Notify เดิมยุติบริการแล้ว จึงต้องใช้ Channel Access Token + recipient ID"
        )
        token = st.text_input(
            "LINE Channel Access Token",
            type="password",
            key=LINE_TOKEN_SESSION_KEY,
            placeholder="วาง token จาก LINE Developers Console",
        )
        recipient_id = st.text_input(
            "Recipient ID",
            key=LINE_RECIPIENT_SESSION_KEY,
            placeholder="userId, groupId หรือ roomId เช่น U... / C... / R...",
            help="ต้องเป็น ID ที่มาจาก Messaging API/webhook หรือ Basic settings ของ channel ไม่ใช่ LINE ID ที่ใช้ค้นหาเพื่อน",
        )
        if token.strip() or recipient_id.strip():
            persist_line_settings_for_user(token, recipient_id)

        st.checkbox(
            "ส่งสรุปเข้า LINE อัตโนมัติหลังงานเสร็จ",
            value=False,
            key="line_auto_send_enabled",
        )

        action_cols = st.columns(2)
        if action_cols[0].button("ส่งข้อความทดสอบ", use_container_width=True):
            ok, message = send_line_push_message("AI Research Office ทดสอบส่งข้อความเข้า LINE สำเร็จ")
            if ok:
                st.success(message)
            else:
                st.warning(message)
        if action_cols[1].button("ล้างการตั้งค่า LINE", use_container_width=True):
            st.session_state["clear_line_settings_next"] = True
            st.rerun()

        if effective_line_token() and effective_line_recipient_id():
            st.success("LINE พร้อมส่งสรุปงาน")
        else:
            st.info("ยังต้องใส่ token และ recipient ID ก่อนส่งเข้า LINE")


def remember_completed_result(
    result_title: str,
    mode_label: str,
    display_command: str,
    final_output: str,
) -> dict[str, str]:
    result_id = hashlib.sha256(
        f"{result_title}\0{mode_label}\0{display_command}\0{final_output}".encode("utf-8")
    ).hexdigest()
    result_info = {
        "id": result_id,
        "result_title": result_title,
        "mode_label": mode_label,
        "display_command": display_command,
        "final_output": final_output,
    }
    st.session_state["last_completed_result"] = result_info
    return result_info


def render_line_delivery_panel() -> None:
    result_info = st.session_state.get("last_completed_result")
    if not result_info:
        return

    st.markdown("### 📲 ส่งสรุปเข้า LINE")
    if not effective_line_token() or not effective_line_recipient_id():
        st.info("ตั้งค่า LINE Channel Access Token และ Recipient ID ใน sidebar ก่อนส่งสรุปเข้า LINE")
        return

    line_message = build_line_summary_message(result_info)
    with st.expander("ดูข้อความที่จะส่งเข้า LINE", expanded=False):
        st.text_area(
            "LINE summary preview",
            value=line_message,
            height=220,
            disabled=True,
            label_visibility="collapsed",
        )

    if st.button("ส่งสรุปงานล่าสุดเข้า LINE", use_container_width=True):
        ok, message = send_line_push_message(line_message)
        if ok:
            st.session_state["last_line_sent_result_id"] = result_info["id"]
            st.success(message)
        else:
            st.warning(message)


def maybe_auto_send_line_summary(result_info: dict[str, str]) -> None:
    if not st.session_state.get("line_auto_send_enabled"):
        return
    if not effective_line_token() or not effective_line_recipient_id():
        st.warning("เปิด auto-send LINE อยู่ แต่ยังไม่ได้ตั้งค่า token หรือ recipient ID")
        return
    if st.session_state.get("last_line_auto_sent_result_id") == result_info["id"]:
        return

    ok, message = send_line_push_message(build_line_summary_message(result_info))
    if ok:
        st.session_state["last_line_auto_sent_result_id"] = result_info["id"]
        st.success(message)
    else:
        st.warning(message)


def render_ai_model_settings() -> tuple[
    str,
    str,
    dict[str, tuple[str, str]],
    dict[str, tuple[str, str]],
    str,
    str,
    bool,
]:
    with st.expander("🧠 เลือกโมเดล / AI ต่อ Agent", expanded=True):
        st.caption(
            "เลือก provider และ model ที่ใช้จริงได้ตรงนี้ ถ้าเปิดโหมดแยกต่อ Agent "
            "แต่ละ Agent จะใช้ AI คนละตัวตามที่เลือก"
        )

        default_provider, default_model = render_model_picker(
            "default",
            "โมเดลหลัก",
            config.DEFAULT_PROVIDER,
            config.DEFAULT_MODEL,
        )

        advanced_models = st.checkbox(
            "เลือก AI/model แยกต่อ Agent",
            value=False,
            key="advanced_models",
            help="เปิดเพื่อกำหนด provider/model แยกให้ Director, Research team และ Build team",
        )

        director_provider = default_provider
        director_model = default_model
        research_model_settings = {
            agent_key: (default_provider, default_model) for agent_key, _label in RESEARCH_AGENT_KEYS
        }
        build_model_settings = {
            agent_key: (default_provider, default_model) for agent_key, _label in BUILD_AGENT_KEYS
        }

        if advanced_models:
            director_tab, research_tab, build_tab = st.tabs(["Director", "Research team", "Build team"])
            with director_tab:
                director_provider, director_model = render_model_picker(
                    "director",
                    "Director",
                    default_provider,
                    default_model,
                )
            with research_tab:
                st.caption("เลือก AI ที่ Research Agent แต่ละตัวจะใช้")
                for agent_key, agent_label in RESEARCH_AGENT_KEYS:
                    provider, model = render_model_picker(
                        f"research_{agent_key}",
                        agent_label,
                        default_provider,
                        default_model,
                    )
                    research_model_settings[agent_key] = (provider, model)
            with build_tab:
                st.caption("เลือก AI ที่ Build Agent แต่ละตัวจะใช้")
                for agent_key, agent_label in BUILD_AGENT_KEYS:
                    provider, model = render_model_picker(
                        f"build_{agent_key}",
                        agent_label,
                        default_provider,
                        default_model,
                    )
                    build_model_settings[agent_key] = (provider, model)

        summary_cols = st.columns(3)
        summary_cols[0].metric("โมเดลหลัก", default_provider)
        summary_cols[1].metric("Model", default_model)
        summary_cols[2].metric("แยกต่อ Agent", "เปิด" if advanced_models else "ปิด")

    return (
        default_provider,
        default_model,
        research_model_settings,
        build_model_settings,
        director_provider,
        director_model,
        advanced_models,
    )


apply_page_styles()
require_login()
load_saved_api_keys_for_user()
load_saved_line_settings_for_user()
process_pending_api_key_clear()
process_pending_line_settings_clear()

render_app_header()
settings_action_notice = st.session_state.pop("settings_action_notice", None)
if settings_action_notice:
    if st.session_state.pop("settings_action_notice_ok", True):
        st.success(settings_action_notice)
    else:
        st.warning(settings_action_notice)
with st.expander("👋 เริ่มต้นใช้งาน", expanded=False):
    render_landing(show_login=False)


render_quick_mobile_settings()
(
    default_provider,
    default_model,
    research_model_settings,
    build_model_settings,
    director_provider,
    director_model,
    advanced_models,
) = render_ai_model_settings()


with st.sidebar:
    render_account_panel()
    st.header("⚙️ การตั้งค่า")
    st.markdown("### 🧠 โมเดล")
    st.caption(f"โมเดลหลัก: `{default_provider} / {default_model}`")
    st.caption(f"เลือกแยกต่อ Agent: `{'เปิด' if advanced_models else 'ปิด'}`")
    st.caption("เปลี่ยนโมเดลได้ที่แผง `🧠 เลือกโมเดล / AI ต่อ Agent` บนหน้าหลัก")
    st.caption(
        "ตั้ง API key เป็น environment variable เช่น "
        "`GEMINI_API_KEY`, `OPENAI_API_KEY`, หรือ `ANTHROPIC_API_KEY`"
    )
    with st.expander("🔑 สถานะ API keys", expanded=False):
        saved_providers = set(st.session_state.get("saved_api_key_providers", []))
        for provider, env_name in config.PROVIDER_API_KEYS.items():
            if provider in saved_providers and session_api_key(provider):
                st.success(f"{provider}: ใช้ key ที่บันทึกไว้กับบัญชีนี้")
            elif session_api_key(provider):
                st.success(f"{provider}: ใช้ key ของผู้ใช้นี้")
            elif config.get_api_key(provider):
                st.success(f"{provider}: พบ `{env_name}` จาก server")
            else:
                st.warning(f"{provider}: ยังไม่พบ key")

    with st.expander("🔐 API keys ของผู้ใช้นี้", expanded=False):
        st.caption("key ที่กรอกตรงนี้จะบันทึกไว้กับบัญชีผู้ใช้นี้ ไม่เขียนลงไฟล์ .env และไม่ถูก commit")
        for provider in config.PROVIDER_API_KEYS:
            value = st.text_input(
                provider,
                type="password",
                key=f"{SESSION_KEY_PREFIX}{provider}",
                placeholder="วาง API key ของคุณเอง",
            )
            if value.strip():
                persist_api_key_for_user(provider, value)

        if st.button("ล้าง API keys ที่บันทึกไว้ของบัญชีนี้"):
            st.session_state["clear_all_api_keys_next"] = True
            st.rerun()

    render_line_settings_panel()

    economy_mode = st.checkbox(
        "โหมดประหยัด quota",
        value=True,
        key="economy_mode",
        help="ใช้ agent เดียวต่อหนึ่งงาน เหมาะกับ free tier หรือช่วงโดน rate limit",
    )
    google_grounding = st.checkbox(
        "เปิดใช้ Google Grounding 🌐 (ค้นข่าวเรียลไทม์)",
        value=False,
        key="google_grounding",
        help="ใช้ได้กับ Google Gemini เท่านั้น และอาจมีค่าใช้จ่าย/ใช้ quota เพิ่มจาก Google",
    )
    if google_grounding:
        st.caption("Grounding จะทำงานเฉพาะ agent ที่เลือก provider เป็น Google Gemini")
    agent_skill_boost = st.checkbox(
        "เพิ่มสกิล Agent + ค้นคว้าเชิงรุก",
        value=True,
        key="agent_skill_boost",
        help="เพิ่ม research plan, fact-checking, trade-off analysis และคำแนะนำพัฒนาสกิลใน prompt ของทีม agent",
    )
    write_files_mode = st.checkbox(
        "สร้างไฟล์โปรเจกต์จริงจากผลลัพธ์ Build",
        value=False,
        key="write_files_mode",
        help="เขียนไฟล์จาก Markdown code blocks ลง generated_projects เฉพาะโหมดสร้างโปรเจกต์",
    )

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
if agent_skill_boost:
    render_agent_skill_recommendations(mode_key, google_grounding)

render_agent_call_mode(
    mode_label,
    default_provider,
    default_model,
    research_model_settings,
    build_model_settings,
    director_provider,
    director_model,
)

input_label = "📝 หัวข้อที่ต้องการวิจัย" if mode_key == "research" else "🛠️ โปรเจกต์ที่อยากให้ AI ช่วยสร้าง"
input_placeholder = (
    "เช่น 'แท็บเล็ตที่เหมาะกับเด็กอายุ 8 ขวบในปี 2026'"
    if mode_key == "research"
    else "เช่น 'สร้างเว็บ landing page สำหรับร้านรถเช่า พร้อมฟอร์มติดต่อ'"
)

if "call_prompt_to_send" in st.session_state:
    st.session_state["command_input"] = st.session_state.pop("call_prompt_to_send")
if "voice_prompt_to_send" in st.session_state:
    st.session_state["command_input"] = st.session_state.pop("voice_prompt_to_send")
if "user_input" in st.session_state:
    st.session_state["command_input"] = st.session_state.pop("user_input")

user_input = st.text_area(
    input_label,
    placeholder=input_placeholder,
    key="command_input",
    height=112,
)

voice_command_notice = st.session_state.pop("voice_command_notice", None)
if voice_command_notice:
    st.info(f"🎙️ ส่งคำสั่งจากเสียงให้ Agent แล้ว: **{voice_command_notice}**")

call_command_notice = st.session_state.pop("call_command_notice", None)
if call_command_notice:
    st.info(f"📞 ส่ง brief จากสายของ **{call_command_notice}** เป็นคำสั่งหลักแล้ว")


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

attachment_context = render_attachment_tools()
skill_context = build_agent_skill_context(mode_key, google_grounding) if agent_skill_boost else ""
combined_context = "\n\n".join(block for block in [attachment_context, skill_context] if block)
prompt_for_agents = combine_user_input(user_input, combined_context)
display_command = user_input.strip() or "คำสั่งจากไฟล์/รูปภาพ/เสียงที่แนบ"


run_button_label = "🚀 เริ่มการวิจัย" if mode_key == "research" else "🏗️ เริ่มวางแผนสร้างโปรเจกต์"
auto_submit_voice = st.session_state.pop("auto_submit_voice", False)
auto_submit_call = st.session_state.pop("auto_submit_call", False)
line_delivery_panel_rendered = False

if st.button(run_button_label, type="primary", use_container_width=True) or auto_submit_voice or auto_submit_call:
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
                st.write(f"🌐 Google Grounding: `{'เปิด' if google_grounding else 'ปิด'}`")
                st.write(f"🧩 Agent Skill Boost: `{'เปิด' if agent_skill_boost else 'ปิด'}`")
                st.write("---")
                director_llm = build_llm_map(
                    {"director": (director_provider, director_model)},
                    google_grounding=google_grounding,
                )["director"]
                team_llms = build_llm_map(active_settings, google_grounding=google_grounding)

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
            result_info = remember_completed_result(result_title, mode_label, display_command, final_output)
            render_compact_markdown(result_title, final_output)
            maybe_auto_send_line_summary(result_info)
            render_line_delivery_panel()
            line_delivery_panel_rendered = True

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

if not line_delivery_panel_rendered:
    render_line_delivery_panel()


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
