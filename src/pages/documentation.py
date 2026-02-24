from pathlib import Path
import streamlit as st
import re
from streamlit.components.v1 import html
from components.init import init
from components.menu import menu


init(avoid_anchor_titles=False)
menu()


BASE_DIR = str(Path(__file__).resolve().parent.parent.parent)
folder_path = BASE_DIR + '/documentation/faq.md'

content = folder_path.read_text(encoding='utf-8')


def parse_sections(text: str):
    lines = text.splitlines()
    intro_lines = []
    sections = []
    current_title = None
    current_lines = []

    for line in lines:
        if line.startswith('### '):
            if current_title:
                sections.append((current_title, '\n'.join(current_lines).strip()))
            elif current_lines:
                intro_lines = current_lines.copy()
            current_title = line[4:].strip()
            current_lines = []
        else:
            current_lines.append(line)

    if current_title:
        sections.append((current_title, '\n'.join(current_lines).strip()))
    elif not intro_lines:
        intro_lines = current_lines

    return '\n'.join(intro_lines).strip(), sections


# Slugify helper to build stable anchors
def _slugify(title: str, existing: dict[str, int]) -> str:
    slug = re.sub(r'[^a-z0-9]+', '-', title.lower())
    slug = slug.strip('-') or 'section'
    count = existing.get(slug, 0)
    existing[slug] = count + 1
    if count:
        slug = f"{slug}-{count}"
    return slug


intro_md, sections = parse_sections(content)

st.markdown(intro_md)

st.subheader("FAQ détaillée")
anchors_seen: dict[str, int] = {}
for title, body in sections:
    if not body:
        continue
    anchor = _slugify(title, anchors_seen)
    st.markdown(f"<div id='{anchor}' data-doc-anchor></div>", unsafe_allow_html=True)
    with st.expander(title):
        st.markdown(body)

html(
    """
    <script>
    (function() {
        const findDetails = (anchor) => {
            let el = anchor.nextElementSibling;
            while (el) {
                if (el.querySelector) {
                    const details = el.querySelector('details');
                    if (details) return details;
                }
                el = el.nextElementSibling;
            }
            return null;
        };

        const openAnchor = () => {
            const hash = window.location.hash.slice(1);
            if (!hash) return;
            const anchor = document.getElementById(hash);
            if (!anchor) return false;
            const details = findDetails(anchor);
            if (details && !details.open) {
                details.open = true;
            }
            requestAnimationFrame(() => anchor.scrollIntoView({behavior: "smooth", block: "start"}));
            return true;
        };

        const ensureAnchor = () => {
            if (openAnchor()) return;
            const observer = new MutationObserver(() => {
                if (openAnchor()) observer.disconnect();
            });
            observer.observe(document.body, { childList: true, subtree: true });
        };

        window.addEventListener('load', ensureAnchor);
        window.addEventListener('hashchange', openAnchor);
    })();
    </script>
    """,
    height=0,
)
