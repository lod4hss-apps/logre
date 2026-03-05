from pathlib import Path
import streamlit as st
import re
from components.init import init
from components.menu import menu

# Page initialization
init(avoid_anchor_titles=False)
menu()

# Path to documentation
BASE_DIR = str(Path(__file__).resolve().parent.parent.parent)
documentation_path = BASE_DIR + "/documentation/faq.md"

# Read documentation
with open(documentation_path, "r", encoding="utf-8") as file:
    content = file.read()


def parse_sections(text: str):
    lines = text.splitlines()
    intro_lines = []
    sections = []
    current_title = None
    current_lines = []

    for line in lines:
        if line.startswith("### "):
            if current_title:
                sections.append((current_title, "\n".join(current_lines).strip()))
            elif current_lines:
                intro_lines = current_lines.copy()
            current_title = line[4:].strip()
            current_lines = []
        else:
            current_lines.append(line)

    if current_title:
        sections.append((current_title, "\n".join(current_lines).strip()))
    elif not intro_lines:
        intro_lines = current_lines

    return "\n".join(intro_lines).strip(), sections


# Slugify helper to build stable anchors
def _slugify(title: str, existing: dict[str, int]) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower())
    slug = slug.strip("-") or "section"
    count = existing.get(slug, 0)
    existing[slug] = count + 1
    if count:
        slug = f"{slug}-{count}"
    return slug


intro_md, sections = parse_sections(content)

section_param = st.query_params.get("section")
if isinstance(section_param, (list, tuple)):
    section_param = section_param[0] if section_param else None

anchors_seen: dict[str, int] = {}
sections_with_anchors = []
for title, body in sections:
    if not body:
        continue
    anchor = _slugify(title, anchors_seen)
    sections_with_anchors.append((anchor, title, body))

st.markdown(intro_md)

selected_section = None
if section_param:
    selected_section = next(
        (section for section in sections_with_anchors if section[0] == section_param),
        None,
    )

if selected_section:
    anchor, title, body = selected_section
    st.markdown(f"<div id='{anchor}' data-doc-anchor></div>", unsafe_allow_html=True)
    with st.expander(title, expanded=True):
        st.markdown(body)
    st.divider()

for anchor, title, body in sections_with_anchors:
    if selected_section and anchor == selected_section[0]:
        continue
    st.markdown(f"<div id='{anchor}' data-doc-anchor></div>", unsafe_allow_html=True)
    with st.expander(title):
        st.markdown(body)
