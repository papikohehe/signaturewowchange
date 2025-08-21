import streamlit as st
import fitz  # PyMuPDF
from io import BytesIO
import os

# --- ROBUST FONT PATH LOGIC ---
# Get the absolute path to the directory where this script is located
try:
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
except NameError:
    # This is a fallback for certain environments where __file__ is not defined
    SCRIPT_DIR = os.getcwd()
    
FONT_PATH = os.path.join(SCRIPT_DIR, "fonts", "angsa.ttf")

# --- Streamlit App UI ---
st.set_page_config(layout="wide")

# --- NEW DEBUGGING SECTION ---
with st.expander("🔍 Font File Debugging Info (Please check this section)"):
    st.write(f"**Current Working Directory:** `{os.getcwd()}`")
    st.write(f"**Script Directory:** `{SCRIPT_DIR}`")
    st.write(f"**Expected Font Path:** `{FONT_PATH}`")
    
    st.markdown("---")
    
    # Check for the 'fonts' directory
    font_dir_path = os.path.join(SCRIPT_DIR, "fonts")
    st.write(f"**Checking for 'fonts' folder at:** `{font_dir_path}`")
    if os.path.isdir(font_dir_path):
        st.success("✅ 'fonts' directory FOUND.")
        try:
            st.write(f"**Contents of 'fonts' directory:** `{os.listdir(font_dir_path)}`")
        except Exception as e:
            st.error(f"Could not read contents of 'fonts' directory: {e}")
    else:
        st.error("❌ 'fonts' directory NOT FOUND.")
        st.write(f"**Contents of Script Directory:** `{os.listdir(SCRIPT_DIR)}`")
        
    st.markdown("---")

    # Check for the font file itself
    st.write(f"**Checking for font file at:** `{FONT_PATH}`")
    if os.path.exists(FONT_PATH):
        try:
            font_size = os.path.getsize(FONT_PATH)
            st.success(f"✅ Font file 'angsa.ttf' FOUND.")
            st.write(f"**File Size:** {font_size} bytes.")
            if font_size < 1000:
                st.warning("⚠️ **Warning:** The file size is extremely small. This suggests the font file is empty or corrupted.")
        except Exception as e:
            st.error(f"Found the file, but could not get its size: {e}")
    else:
        st.error("❌ Font file 'angsa.ttf' NOT FOUND at the expected path.")


# --- Main Application ---
st.title("📄 Contract Signatory Updater")
st.write("This tool updates the signatory name and title on **Page 4** of your PDF contract files.")

# The rest of your app code remains the same...
REPLACEMENTS = {
    "นางธนาภรณ์ พลอยวิเศษ": "นายเจษฎากร สมิทธิอรรถกร",
    "People and Organizational Development Team": "Chief Executive Officer"
}

def replace_text_on_page4(uploaded_file):
    try:
        # ... function code is unchanged ...
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

uploaded_files = st.file_uploader("Drag and drop your contract PDF files here", type="pdf", accept_multiple_files=True)

if st.button("✨ Process Files", type="primary"):
    if uploaded_files:
        with st.spinner("Processing... Please wait."):
            # ... UI code is unchanged ...
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
            st.success("✅ Processing complete! Your updated files are ready for download above.")
    else:
        st.warning("⚠️ Please upload at least one PDF file to process.")
