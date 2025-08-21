import streamlit as st
import fitz  # PyMuPDF
from io import BytesIO

# --- Configuration: Define the text replacements ---
REPLACEMENTS = {
    "นางธนาภรณ์ พลอยวิเศษ": "นายเจษฎากร สมิทธิอรรถกร",
    "People and Organizational Development Team": "Chief Executive Officer"
}

def replace_text_on_page4(uploaded_file):
    try:
        file_bytes = uploaded_file.getvalue()
        pdf_document = fitz.open(stream=file_bytes, filetype="pdf")

        if len(pdf_document) < 4:
            st.warning(f"'{uploaded_file.name}' has fewer than 4 pages and was skipped.")
            return None

        page = pdf_document[3]  # Page 4

        for search_text, replace_text in REPLACEMENTS.items():
            text_instances = page.search_for(search_text)

            for inst in text_instances:
                # White-out the old text
                page.add_redact_annot(inst, fill=(1, 1, 1))
                page.apply_redactions()

                # Insert replacement text aligned with original
                page.insert_textbox(
                    inst,                      # bounding box of original text
                    replace_text,
                    fontsize=11,
                    fontname="helv",
                    align=fitz.TEXT_ALIGN_LEFT
                )

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
st.info(f"""
The following changes will be applied:
- **Replaces:** `นางธนาภรณ์ พลอยวิเศษ` → `นายเจษฎากร สมิทธิอรรถกร`
- **Replaces:** `People and Organizational Development Team` → `Chief Executive Officer`
""")

# File Uploader
uploaded_files = st.file_uploader(
    "Drag and drop your contract PDF files here",
    type="pdf",
    accept_multiple_files=True
)

st.markdown("---")

if st.button("✨ Process Files", type="primary"):
    if uploaded_files:
        with st.spinner("Processing... Please wait."):
            cols = st.columns(3)
            col_idx = 0
            
            for uploaded_file in uploaded_files:
                modified_pdf_stream = replace_text_on_page4(uploaded_file)
                
                if modified_pdf_stream:
                    new_filename = f"{uploaded_file.name.replace('.pdf', '')}_UPDATED.pdf"
                    
                    with cols[col_idx % 3]:
                        st.download_button(
                            label=f"⬇️ Download {new_filename}",
                            data=modified_pdf_stream,
                            file_name=new_filename,
                            mime="application/pdf"
                        )
                        st.write("")
                    
                    col_idx += 1
        st.success("✅ Processing complete! Your updated files are ready for download above.")
    else:
        st.warning("⚠️ Please upload at least one PDF file to process.")
