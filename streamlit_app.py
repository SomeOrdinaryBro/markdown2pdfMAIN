import streamlit as st
import markdown
import pdfkit
import tempfile
import os
import re
from datetime import datetime
from docx import Document  # for docx export
from pikepdf import Pdf  # for PDF compression

# --- Streamlit UI Setup ---
st.set_page_config(page_title="Markdown to PDF Converter", page_icon="📄")

LIGHT_THEME = """
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
    font = st.selectbox("Font Family", ["Arial", "Times New Roman", "Courier New", "Helvetica"])
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

    # Real-time Collaboration (Placeholder)
    collaboration = st.checkbox("Enable real-time collaboration")  # This would require additional setup

    # CSS-based Content Styling
    custom_css = st.text_area("Custom CSS (optional)", height=100)

    # Live PDF Preview
    show_preview = st.checkbox("Show live PDF preview before download")

    # File Compression Option
    compress_pdf = st.checkbox("Compress PDF after generation")

    # Export Options
    export_docx = st.checkbox("Export as .docx")

    if st.button("🔄 Convert to PDF"):
        try:
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
                    {custom_css}
                }}
                h1 {{ page-break-before: {'always' if split_pages else 'auto'}; }}
            </style>
            """

            watermark_html = f"<div style='position:fixed; top:45%; left:30%; font-size:48px; color:rgba(150,150,150,0.15); transform:rotate(-30deg); z-index:-1'>{watermark}</div>" if watermark else ""

            final_html = f"<html><head>{style}</head><body>{watermark_html}{html}</body></html>"

            match = re.match(r"# (.+)", md_content)
            if match:
                filename_base = match.group(1).strip().replace(" ", "_")
            elif uploaded_filename:
                filename_base = os.path.splitext(uploaded_filename)[0]
            else:
                filename_base = "converted_" + datetime.now().strftime("%Y%m%d_%H%M%S")

            filename_pdf = f"{filename_base}.pdf"
            filename_html = f"{filename_base}.html"
            filename_docx = f"{filename_base}.docx"

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

            # Generate PDF
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
                pdfkit.from_string(final_html, tmp_pdf.name, options=options)
                temp_files.append(tmp_pdf.name)

                # Compress PDF
                if compress_pdf:
                    with open(tmp_pdf.name, 'rb') as original_file:
                        with open(tmp_pdf.name, 'wb') as compressed_file:
                            pdf = Pdf.open(original_file)
                            pdf.save(compressed_file, compress_stream=True)

                # Show preview
                if show_preview:
                    st.components.v1.iframe("file://" + tmp_pdf.name, height=600)

                st.success("✅ PDF generated!")
                with open(tmp_pdf.name, "rb") as f:
                    st.download_button("Download PDF", f, file_name=filename_pdf)

            # Export .docx
            if export_docx:
                doc = Document()
                doc.add_paragraph(md_content)
                doc.save(filename_docx)
                st.download_button("Download DOCX", filename_docx)

            if save_html:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp_html:
                    tmp_html.write(final_html.encode("utf-8"))
                    tmp_html.flush()
                    temp_files.append(tmp_html.name)
                    with open(tmp_html.name, "rb") as f:
                        st.download_button("Download HTML", f, file_name=filename_html)

        except Exception as e:
            st.error(f"❌ Conversion failed: {e}")

        for f in temp_files:
            os.unlink(f)

    st.markdown("""
        <hr style="margin-top: 50px;">
        <div style="text-align: center; color: grey;">
            Made with ❤️ by <b>@SomeOrdinaryBro</b>
        </div>
    """, unsafe_allow_html=True)
