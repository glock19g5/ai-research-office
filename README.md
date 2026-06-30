# AI Research Office

แอป Streamlit สำหรับรันทีม AI agents ด้วย CrewAI และ Google Gemini

ตอนนี้มี 2 โหมด:

- `วิจัยและแนะนำ` - Director จัด brief แล้วส่งต่อทีม Research 5 agents
- `สร้างโปรเจกต์ใหม่` - Director จัด brief แล้วส่งต่อทีม Build เพื่อสร้าง PRD, architecture, implementation package และ QA review
- ในโหมด Build สามารถเปิด `สร้างไฟล์โปรเจกต์จริงจากผลลัพธ์ Build` เพื่อเขียนไฟล์จาก Markdown code blocks ลง `generated_projects/`

รองรับการเลือกโมเดล:

- Google Gemini ผ่าน `GEMINI_API_KEY`
- OpenAI / ChatGPT ผ่าน `OPENAI_API_KEY`
- Anthropic Claude ผ่าน `ANTHROPIC_API_KEY`

ใน sidebar สามารถเลือกโมเดลหลักของทั้งทีม หรือเปิด `เลือกโมเดลแยกต่อ agent` เพื่อให้ Director, Research agents และ Build agents ใช้โมเดลคนละตัวได้

## โครงสร้างไฟล์

- `app.py` - Streamlit UI
- `config.py` - ตั้งค่า Gemini API key และ LLM
- `agents.py` - นิยาม agents ทั้ง 5 ตัว
- `crew_runner.py` - สร้าง tasks และรัน CrewAI workflow
- `director.py` - Director agent และตัวจัด brief
- `build_agents.py` - นิยามทีม Build
- `build_runner.py` - workflow สำหรับโหมดสร้างโปรเจกต์
- `quick_runner.py` - workflow agent เดียวสำหรับโหมดประหยัด quota
- `project_writer.py` - แปลง Markdown code blocks เป็นไฟล์จริงใน `generated_projects/`
- `requirements.txt` - dependencies

## วิธีรัน

```bash
pip install -r requirements.txt
export GEMINI_API_KEY="your-key-here"
streamlit run app.py
```

บน PowerShell:

```powershell
$env:GEMINI_API_KEY="your-key-here"
streamlit run app.py
```

ถ้าต้องการใช้ OpenAI หรือ Claude:

```powershell
$env:OPENAI_API_KEY="your-openai-key"
$env:ANTHROPIC_API_KEY="your-anthropic-key"
```

ถ้าเครื่องไม่รู้จักคำสั่ง `pip` หรือ `streamlit` ให้ใช้สคริปต์ช่วย:

```powershell
.\setup.ps1
.\run.ps1
```

## เปิดแบบ Desktop App

หลังสร้าง shortcut แล้ว สามารถเปิดจาก Desktop:

```text
AI Research Office
```

หรือเปิดจากไฟล์ในโฟลเดอร์โปรเจกต์:

- `Open AI Research Office.vbs` - เปิดแบบเงียบและเปิด browser ให้อัตโนมัติ
- `Open AI Research Office.bat` - เปิดแบบเห็นหน้าต่าง server สำหรับ debug
- `Stop AI Research Office.bat` - หยุด server ที่รันบน port 8501
- `Create Desktop Shortcut.bat` - สร้าง shortcut บน Desktop ใหม่

ถ้าต้องการเก็บ API keys ไว้ในเครื่องแบบไม่ต้องพิมพ์ทุกครั้ง ให้ copy `.env.example` เป็น `.env` แล้วใส่ key เฉพาะ provider ที่ใช้ ห้ามแชร์ไฟล์ `.env` หรือถ่ายภาพให้เห็น key

## แชร์ให้คนอื่นใช้

ตั้งรหัสเข้าแอปใน `.env`:

```env
APP_PASSWORD=your-password
```

ถ้าไม่อยากให้คนอื่นใช้ API key ของคุณ ให้เว้น provider keys ใน `.env` ว่างไว้ แล้วให้ผู้ใช้กรอก key ของตัวเองใน sidebar ตรง:

```text
API keys ของผู้ใช้นี้
```

key ที่กรอกในช่องนี้อยู่ใน session ของผู้ใช้ ไม่ถูกเขียนลง `.env`

หมายเหตุ:

- ถ้ารันบนเครื่องคุณด้วย `localhost:8501` คนอื่นจะเข้าไม่ได้จากอินเทอร์เน็ต
- ถ้าอยู่ Wi-Fi เดียวกัน อาจเข้าได้ผ่าน `http://เลข-IP-เครื่องคุณ:8501` เมื่อ firewall อนุญาต
- ถ้าต้องการให้คนนอกบ้าน/คนนอกเครือข่ายเข้าได้จริง ควร deploy ขึ้น server/cloud และใช้ HTTPS
