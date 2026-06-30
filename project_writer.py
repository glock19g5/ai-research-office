"""Write generated project files from Markdown code blocks."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from urllib.parse import quote
from pathlib import Path
import re


GENERATED_ROOT = Path(__file__).resolve().parent / "generated_projects"


@dataclass
class GeneratedFile:
    path: str
    language: str
    content: str


@dataclass
class ProjectInfo:
    name: str
    path: Path
    modified_at: datetime
    files: list[Path]
    report_path: Path | None


@dataclass
class SiteContent:
    page_title: str = ""
    brand_name: str = ""
    hero_title: str = ""
    hero_text_1: str = ""
    hero_text_2: str = ""
    contact_email: str = ""
    contact_phone: str = ""
    contact_address: str = ""


PATH_RE = re.compile(
    r"^\s*(?:#{1,6}\s+)*\**(?P<path>[\w./\\ -]+\.[A-Za-z0-9]+)\**\s*$"
)


def slugify_project_name(text: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9ก-๙]+", "-", text.strip()).strip("-").lower()
    return slug[:50] or "ai-generated-project"


def extract_generated_files(markdown: str) -> list[GeneratedFile]:
    files: list[GeneratedFile] = []
    seen: set[str] = set()
    lines = markdown.splitlines()
    i = 0

    while i < len(lines):
        path_match = PATH_RE.match(lines[i])
        if not path_match or i + 1 >= len(lines) or not lines[i + 1].startswith("```"):
            i += 1
            continue

        raw_path = path_match.group("path").strip().replace("\\", "/")
        if raw_path.startswith(("/", ".")) or ".." in Path(raw_path).parts:
            i += 1
            continue
        if raw_path in seen:
            i += 1
            continue

        language = lines[i + 1].strip().strip("`")
        code_lines: list[str] = []
        i += 2
        while i < len(lines) and not lines[i].startswith("```"):
            code_lines.append(lines[i])
            i += 1

        seen.add(raw_path)
        files.append(
            GeneratedFile(
                path=raw_path,
                language=language,
                content="\n".join(code_lines).rstrip() + "\n",
            )
        )
        i += 1

    return files


def write_project_files(project_name: str, markdown: str) -> tuple[Path, list[GeneratedFile]]:
    project_dir = (GENERATED_ROOT / slugify_project_name(project_name)).resolve()
    root = GENERATED_ROOT.resolve()

    if root not in project_dir.parents and project_dir != root:
        raise ValueError("Project path escaped the generated_projects directory")

    files = extract_generated_files(markdown)
    project_dir.mkdir(parents=True, exist_ok=True)

    readme = project_dir / "AI_BUILD_REPORT.md"
    readme.write_text(markdown, encoding="utf-8")

    for generated_file in files:
        target = (project_dir / generated_file.path).resolve()
        if root not in target.parents:
            raise ValueError(f"Generated file path escaped the project directory: {generated_file.path}")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(generated_file.content, encoding="utf-8")

    return project_dir, files


def list_generated_projects() -> list[ProjectInfo]:
    if not GENERATED_ROOT.exists():
        return []

    projects: list[ProjectInfo] = []
    for project_dir in GENERATED_ROOT.iterdir():
        if not project_dir.is_dir():
            continue

        files = sorted(path for path in project_dir.rglob("*") if path.is_file())
        report_path = project_dir / "AI_BUILD_REPORT.md"
        modified_at = datetime.fromtimestamp(project_dir.stat().st_mtime)
        projects.append(
            ProjectInfo(
                name=project_dir.name,
                path=project_dir,
                modified_at=modified_at,
                files=files,
                report_path=report_path if report_path.exists() else None,
            )
        )

    return sorted(projects, key=lambda project: project.modified_at, reverse=True)


def relative_project_file(project: ProjectInfo, path: Path) -> str:
    return path.relative_to(project.path).as_posix()


def find_preview_html(project: ProjectInfo) -> Path | None:
    index = project.path / "index.html"
    if index.exists():
        return index

    html_files = [path for path in project.files if path.suffix.lower() == ".html"]
    return html_files[0] if html_files else None


def html_data_url(html_path: Path) -> str:
    html = build_preview_html(html_path)
    return "data:text/html;charset=utf-8," + quote(html)


def update_team_member_names(project: ProjectInfo, new_name: str) -> int:
    script_path = project.path / "script.js"
    if not script_path.exists():
        return 0

    script = script_path.read_text(encoding="utf-8", errors="replace")
    team_match = re.search(r"(const\s+teamMembers\s*=\s*\[)(?P<body>.*?)(\];)", script, flags=re.DOTALL)
    if not team_match:
        return 0

    body = team_match.group("body")
    updated_body, count = re.subn(
        r'name:\s*"[^"]*"',
        f'name: "{new_name}"',
        body,
    )
    if count == 0:
        return 0

    updated_script = (
        script[: team_match.start("body")]
        + updated_body
        + script[team_match.end("body") :]
    )
    script_path.write_text(updated_script, encoding="utf-8")
    return count


def _first_group(pattern: str, text: str, default: str = "") -> str:
    match = re.search(pattern, text, flags=re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else default


def read_site_content(project: ProjectInfo) -> SiteContent:
    index_path = project.path / "index.html"
    if not index_path.exists():
        return SiteContent()

    html = index_path.read_text(encoding="utf-8", errors="replace")
    about_match = re.search(
        r'<section\s+id=["\']about["\'][^>]*>.*?<h2>(?P<title>.*?)</h2>\s*'
        r"<p>(?P<p1>.*?)</p>\s*<p>(?P<p2>.*?)</p>",
        html,
        flags=re.DOTALL | re.IGNORECASE,
    )

    return SiteContent(
        page_title=_first_group(r"<title>(.*?)</title>", html),
        brand_name=_first_group(r"<header[^>]*>.*?<h1>(.*?)</h1>", html),
        hero_title=about_match.group("title").strip() if about_match else "",
        hero_text_1=about_match.group("p1").strip() if about_match else "",
        hero_text_2=about_match.group("p2").strip() if about_match else "",
        contact_email=_first_group(r"mailto:([^\"']+)", html),
        contact_phone=_first_group(r"tel:([^\"']+)", html),
        contact_address=_first_group(r"<p>ที่อยู่:\s*(.*?)</p>", html),
    )


def update_site_content(project: ProjectInfo, content: SiteContent) -> bool:
    index_path = project.path / "index.html"
    if not index_path.exists():
        return False

    html = index_path.read_text(encoding="utf-8", errors="replace")
    replacements = [
        (r"<title>.*?</title>", f"<title>{content.page_title}</title>"),
        (r"(<header[^>]*>.*?<h1>).*?(</h1>)", rf"\1{content.brand_name}\2"),
        (r'(<section\s+id=["\']about["\'][^>]*>.*?<h2>).*?(</h2>)', rf"\1{content.hero_title}\2"),
        (
            r'(<section\s+id=["\']about["\'][^>]*>.*?<h2>.*?</h2>\s*<p>).*?(</p>)',
            rf"\1{content.hero_text_1}\2",
        ),
        (
            r'(<section\s+id=["\']about["\'][^>]*>.*?<h2>.*?</h2>\s*<p>.*?</p>\s*<p>).*?(</p>)',
            rf"\1{content.hero_text_2}\2",
        ),
        (r'mailto:[^"\']+', f"mailto:{content.contact_email}"),
        (r'tel:[^"\']+', f"tel:{content.contact_phone}"),
        (r"<p>อีเมล:\s*<a[^>]*>.*?</a></p>", f'<p>อีเมล: <a href="mailto:{content.contact_email}">{content.contact_email}</a></p>'),
        (r"<p>โทรศัพท์:\s*<a[^>]*>.*?</a></p>", f'<p>โทรศัพท์: <a href="tel:{content.contact_phone}">{content.contact_phone}</a></p>'),
        (r"<p>ที่อยู่:\s*.*?</p>", f"<p>ที่อยู่: {content.contact_address}</p>"),
    ]

    for pattern, replacement in replacements:
        html = re.sub(pattern, replacement, html, count=1, flags=re.DOTALL | re.IGNORECASE)

    index_path.write_text(html, encoding="utf-8")
    return True


def build_preview_html(html_path: Path) -> str:
    project_dir = html_path.parent
    html = html_path.read_text(encoding="utf-8", errors="replace")

    def inline_css(match: re.Match[str]) -> str:
        href = match.group("href")
        css_path = (project_dir / href).resolve()
        if project_dir.resolve() not in css_path.parents or not css_path.exists():
            return match.group(0)
        css = css_path.read_text(encoding="utf-8", errors="replace")
        return f"<style>\n{css}\n</style>"

    def inline_js(match: re.Match[str]) -> str:
        src = match.group("src")
        js_path = (project_dir / src).resolve()
        if project_dir.resolve() not in js_path.parents or not js_path.exists():
            return match.group(0)
        js = js_path.read_text(encoding="utf-8", errors="replace")
        return f"<script>\n{js}\n</script>"

    html = re.sub(
        r'<link\s+[^>]*rel=["\']stylesheet["\'][^>]*href=["\'](?P<href>[^"\']+)["\'][^>]*>',
        inline_css,
        html,
        flags=re.IGNORECASE,
    )
    html = re.sub(
        r'<script\s+[^>]*src=["\'](?P<src>[^"\']+)["\'][^>]*>\s*</script>',
        inline_js,
        html,
        flags=re.IGNORECASE,
    )

    if "</head>" in html:
        html = html.replace(
            "</head>",
            "<style>html,body{background:#ffffff;color:#111111;}</style></head>",
            1,
        )

    return html
