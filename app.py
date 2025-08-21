import streamlit as st
import fitz  # PyMuPDF
from io import BytesIO
import os

# --- Configuration: Define the text replacements ---
REPLACEMENTS = {
    "นางธนาภรณ์ พลอยวิเศษ": "นายเจษฎากร สมิทธิอรรถกร",
    "People and Organizational Development Team": "Chief Executive Officer"
}

# --- ROBUST FONT PATH LOGIC ---
try:
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
except NameError:
    SCRIPT_DIR = os.getcwd()
FONT_PATH = os.path.join(SCRIPT_DIR, "fonts", "angsa.ttf")


def replace_text_on_page4(uploaded_file):
    try:
        file_bytes = uploaded_file.getvalue()
        pdf_document = fitz.open(stream=file_bytes, filetype="pdf")

        if len(pdf_document) < 4:
            st.warning(f"'{uploaded_file.name}' has fewer than 4 pages and was skipped.")
            return None

        page = pdf_document[3]

        font_is_registered = False
        if os.path.exists(FONT_PATH):
            page.insert_font(fontfile=FONT_PATH, fontname="custom-thai")
            font_is_registered = True
        else:
            # Only show this error if the file is truly missing now
            st.error(f"Font file not found at {FONT_PATH}. Please ensure it's in the repository.")
            return None

        for search_text, replace_text in REPLACEMENTS.items():
            if "นางธนาภรณ์" in search_text:
                font_name = "custom-thai" if font_is_registered else "helv"
                alignment = fitz.TEXT_ALIGN_CENTER
            else:
                font_name = "TNR"
                alignment = fitz.TEXT_ALIGN_LEFT
            
            text_instances = page.search_for(search_text)
            for inst in text_instances:
                page.add_redact_annot(inst, text=replace_text, fontname=font_name, fontsize=11, align=alignment, fill=(1, 1, 1), text_color=(0, 0, 0))
        
        page.apply_redactions()
        output_stream = BytesIO()
        pdf_document.save(output_stream, garbage=3, deflate=True)
        pdf_document.close()
        output_stream.seek(0)
        return output_stream
    except Exception as e:
        st.error(f"An error occurred while processing '{uploaded_file.name}': {e}")
        return None

# --- Streamlit App UI ---
st.set_page_config(layout="wide")
st.title("📄 Contract Signatory Updater")
st.write("This tool updates the signatory name and title on **Page 4** of your PDF contract files.")

uploaded_files = st.file_uploader("Drag and drop your contract PDF files here", type="pdf", accept_multiple_files=True)

if st.button("✨ Process Files", type="primary"):
    if uploaded_files:
        with st.spinner("Processing... Please wait."):
            cols = st.columns(3)
            col_idx = 0
            for uploaded_file in uploaded_files:
                uploaded_file.seek(0)
                modified_pdf_stream = replace_text_on_page4(uploaded_file)
                if modified_pdf_stream:
                    new_filename = f"{uploaded_file.name.replace('.pdf', '')}_UPDATED.pdf"
                    with cols[col_idx % 3]:
                        st.download_button(label=f"⬇️ Download {new_filename}", data=modified_pdf_stream, file_name=new_filename, mime="application/pdf")
                        st.write("")
                    col_idx += 1
            st.success("✅ Processing complete!")
    else:
        st.warning("⚠️ Please upload at least one PDF file.")
