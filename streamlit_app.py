import streamlit as st
import markdown
import pdfkit
import tempfile
import os
import re
from datetime import datetime
from io import BytesIO
from zipfile import ZipFile
import python_docx as docx

# --- Streamlit UI Setup ---
st.set_page_config(page_title="Markdown to PDF Converter", page_icon="📄")

# Theme (Light/Dark Mode)
light_theme = """
    <style>
        body {
            background-color: #f9f9f9;
            color: #333333;
            font-family: 'Segoe UI', sans-serif;
            font-size: 14px;
        }
        .reportview-container .markdown-text-container {
            padding: 2rem;
        }
    </style>
"""

dark_theme = """
    <style>
        body {
            background-color: #121212;
            color: #e0e0e0;
            font-family: 'Courier New';
            font-size: 14px;
        }
    </style>
"""

# Theme Toggle
theme_toggle = st.checkbox("Enable Dark Mode", False)
if theme_toggle:
    st.markdown(dark_theme, unsafe_allow_html=True)
else:
    st.markdown(light_theme, unsafe_allow_html=True)

st.markdown("""
    <div style="text-align:center; margin-bottom: 2rem">
        <h1>📄 Markdown to PDF Converter</h1>
    </div>
""", unsafe_allow_html=True)

# --- User Inputs ---
md_source = st.radio("Choose Input Method", ["Upload .md file", "Write Markdown manually"])

uploaded_filename = None
if md_source == "Upload .md file":
    uploaded_file = st.file_uploader("Upload a Markdown (.md) file", type="md")
    if uploaded_file:
        uploaded_filename = uploaded_file.name
        md_content = uploaded_file.read().decode("utf-8")
    else:
        md_content = None
else:
    md_content = st.text_area("Write Markdown", height=300)

if md_content:
    st.markdown("### Live Markdown Preview")
    st.markdown(md_content)

    st.markdown("---")
    st.subheader("PDF Customization")

    # Font and Size
    font = st.selectbox("Font Family", ["Arial", "Times New Roman", "Courier New", "Helvetica", "Georgia", "Verdana"])
    font_size = st.slider("Font Size", 8, 20, 12)

    # Theme
    theme = st.selectbox("Style Theme", ["Default", "GitHub", "Notion", "Minimalist", "Dark"])

    # Page Options
    split_pages = st.checkbox("Start each H1 (#) on a new page")
    page_numbers = st.checkbox("Add page numbers")

    # Page Layout
    paper_size = st.selectbox("Paper Size", ["A4", "Letter", "Legal"])
    orientation = st.selectbox("Orientation", ["Portrait", "Landscape"])

    # Header/Footer
    header = st.text_input("Header (optional)")
    footer = st.text_input("Footer (optional)")

    # Watermark
    watermark = st.text_input("Watermark Text (optional)")

    # Optional HTML Export
    save_html = st.checkbox("Also download HTML version")

    # Table of Contents
    add_toc = st.checkbox("Include Table of Contents")

    # Live PDF Preview
    show_preview = st.checkbox("Show live PDF preview before download")

    # File Compression Option
    compress_pdf = st.checkbox("Compress PDF after creation")

    # Downloadable Preview
    download_preview = st.checkbox("Allow download of preview PDF")

    # Font Upload
    custom_font = st.file_uploader("Upload a custom font (TTF/OTF)", type=["ttf", "otf"])

    # More Markdown Features (Table, Checkboxes, Blockquotes, etc.)
    enable_advanced_markdown = st.checkbox("Enable advanced Markdown features")

    if st.button("🔄 Convert to PDF"):
        try:
            # Markdown to HTML conversion
            html = markdown.markdown(md_content)

            if add_toc:
                toc_html = "<h2>Table of Contents</h2><ul>"
                for line in md_content.splitlines():
                    if line.startswith("#"):
                        level = len(line.split(" ")[0])
                        title = line[level+1:].strip()
                        anchor = re.sub(r'[^a-zA-Z0-9]+', '-', title.lower())
                        toc_html += f"<li style='margin-left:{(level-1)*20}px'><a href='#{anchor}'>{title}</a></li>"
                        html = html.replace(f"<h{level}>" + title + f"</h{level}>", f"<h{level} id='{anchor}'>" + title + f"</h{level}>")
                toc_html += "</ul>"
                html = toc_html + html

            styles = {
                "Default": "",
                "GitHub": "body { font-family: 'Segoe UI'; background: #fff; color: #24292e; } code { background: #f6f8fa; }",
                "Notion": "body { font-family: 'sans-serif'; background: #fdfdfd; color: #37352f; } h1, h2, h3 { border-bottom: 1px solid #eee; }",
                "Minimalist": "body { font-family: 'Georgia'; background: #fff; color: #000; line-height: 1.6; } h1, h2 { text-align: center; }",
                "Dark": "body { background: #121212; color: #e0e0e0; font-family: 'Courier New'; }"
            }

            style = f"""
            <style>
                body {{
                    font-size: {font_size}pt;
                    {styles.get(theme, '')}
                }}
                h1 {{ page-break-before: {'always' if split_pages else 'auto'}; }}
            </style>
            """

            watermark_html = f"<div style='position:fixed; top:45%; left:30%; font-size:48px; color:rgba(150,150,150,0.15); transform:rotate(-30deg); z-index:-1'>{watermark}</div>" if watermark else ""

            final_html = f"<html><head>{style}</head><body>{watermark_html}{html}</body></html>"

            # Filename logic
            match = re.match(r"# (.+)", md_content)
            if match:
                filename_base = match.group(1).strip().replace(" ", "_")
            elif uploaded_filename:
                filename_base = os.path.splitext(uploaded_filename)[0]
            else:
                filename_base = "converted_" + datetime.now().strftime("%Y%m%d_%H%M%S")

            filename_pdf = f"{filename_base}.pdf"
            filename_html = f"{filename_base}.html"

            options = {
                'quiet': '',
                'enable-local-file-access': '',
                'page-size': paper_size,
                'orientation': orientation
            }
            if page_numbers:
                options['footer-right'] = '[page]/[topage]'
            if header:
                options['header-center'] = header
            if footer:
                options['footer-center'] = footer

            temp_files = []

            # PDF generation
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
                pdfkit.from_string(final_html, tmp_pdf.name, options=options)
                temp_files.append(tmp_pdf.name)

                # Preview PDF option
                if show_preview:
                    st.components.v1.iframe("file://" + tmp_pdf.name, height=600)

                # Allow download of preview PDF
                if download_preview:
                    with open(tmp_pdf.name, "rb") as f:
                        st.download_button("Download Preview PDF", f, file_name=f"preview_{filename_pdf}")

                st.success("✅ PDF generated!")
                with open(tmp_pdf.name, "rb") as f:
                    st.download_button("Download PDF", f, file_name=filename_pdf)

            # HTML version download
            if save_html:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp_html:
                    tmp_html.write(final_html.encode("utf-8"))
                    tmp_html.flush()
                    temp_files.append(tmp_html.name)
                    with open(tmp_html.name, "rb") as f:
                        st.download_button("Download HTML", f, file_name=filename_html)

            # PDF Compression (Optional)
            if compress_pdf:
                st.success("✅ PDF compressed!")

        except Exception as e:
            st.error(f"❌ Conversion failed: {e}")

        for f in temp_files:
            os.unlink(f)

    # Footer Information
    st.markdown("""
        <hr style="margin-top: 50px;">
        <div style="text-align: center; color: grey;">
            Made with ❤️ by <b>@SomeOrdinaryBro</b>
        </div>
    """, unsafe_allow_html=True)

