import streamlit as st
import fitz  # PyMuPDF
from PIL import Image
import io
import img2pdf
import zipfile
import os

# --- PAGE SETUP ---
# Grabs your icon.png for the browser tab and mobile install
icon_path = "icon.png"
if os.path.exists(icon_path):
    st.set_page_config(page_title="Compress and Convert", page_icon=Image.open(icon_path), layout="centered")
else:
    st.set_page_config(page_title="Compress and Convert", layout="centered")

# --- THE "COVER IT UP" HACK ---
# Hides the Streamlit deploy button, GitHub menu, and footer without breaking the left sidebar menu.
hide_github_style = """
<style>
.github-cover {
    position: fixed;
    top: 0;
    right: 0;
    width: 120px;
    height: 60px;
    background-color: white;
    z-index: 999999;
}
@media (prefers-color-scheme: dark) {
    .github-cover { background-color: #0e1117; }
}
footer {visibility: hidden;}
</style>
<div class="github-cover"></div>
"""
st.markdown(hide_github_style, unsafe_allow_html=True)

# --- MAIN APP UI ---
st.title("🗜️ Compress and Convert")
st.write("Fast, secure, and private document tools.")

# Sidebar navigation
option = st.sidebar.selectbox(
    "Choose a tool", 
    ["Compress Image", "Compress PDF", "PDF to Images", "Images to PDF"]
)

if option == "Compress Image":
    st.header("🖼️ Compress Image")
    uploaded_file = st.file_uploader("Upload Image (JPG/PNG)", type=['png', 'jpg', 'jpeg'])
    
    st.write("### Compression Settings")
    scale_percent = st.slider("Resize Image (Resolution %)", 5, 100, 30, help="Lower this to shrink the physical size of the image for extreme compression.")
    quality = st.slider("JPEG Quality", 1, 100, 30, help="Lower this to reduce file size.")
    
    if uploaded_file:
        img = Image.open(uploaded_file)
        # Convert transparent PNGs to solid JPGs
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
            
        # Extreme compression: Shrink physical dimensions
        if scale_percent < 100:
            new_width = int(img.width * (scale_percent / 100.0))
            new_height = int(img.height * (scale_percent / 100.0))
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
        out_io = io.BytesIO()
        img.save(out_io, format="JPEG", quality=quality, optimize=True)
        
        orig_size = uploaded_file.size / 1024
        new_size = out_io.getbuffer().nbytes / 1024
        
        st.success(f"Reduced from **{orig_size:.0f} KB** to **{new_size:.0f} KB**!")
        
        st.download_button(
            label="⬇️ Download Compressed Image", 
            data=out_io, 
            file_name=f"compressed_{uploaded_file.name}", 
            mime="image/jpeg"
        )

elif option == "Compress PDF":
    st.header("📄 Compress PDF")
    uploaded_file = st.file_uploader("Upload PDF", type=['pdf'])
    
    if uploaded_file:
        with st.spinner("Compressing..."):
            doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
            out_io = io.BytesIO()
            doc.save(out_io, garbage=4, deflate=True, clean=True)
            
            orig_size = uploaded_file.size / 1024
            new_size = out_io.getbuffer().nbytes / 1024
        
        st.success(f"Reduced from **{orig_size:.0f} KB** to **{new_size:.0f} KB**!")
        
        st.download_button(
            label="⬇️ Download Compressed PDF", 
            data=out_io, 
            file_name=f"compressed_{uploaded_file.name}", 
            mime="application/pdf"
        )

elif option == "PDF to Images":
    st.header("📑 PDF to Images")
    uploaded_file = st.file_uploader("Upload PDF", type=['pdf'])
    dpi = st.slider("Resolution (DPI)", 72, 300, 150)
    
    if uploaded_file:
        if st.button("Convert to Images"):
            with st.spinner("Converting..."):
                doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
                    for page_num in range(len(doc)):
                        page = doc.load_page(page_num)
                        pix = page.get_pixmap(dpi=dpi)
                        img_bytes = pix.tobytes("jpeg")
                        zip_file.writestr(f"page_{page_num + 1}.jpg", img_bytes)
            
            st.success("✅ Conversion complete!")
            st.download_button(
                label="⬇️ Download ZIP of Images", 
                data=zip_buffer.getvalue(), 
                file_name=f"{uploaded_file.name}_images.zip", 
                mime="application/zip"
            )

elif option == "Images to PDF":
    st.header("🖼️ Images to PDF")
    uploaded_files = st.file_uploader("Upload Images", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True)
    
    if uploaded_files:
        if st.button("Convert to PDF"):
            with st.spinner("Merging..."):
                image_list = []
                for file in uploaded_files:
                    img = Image.open(file)
                    if img.mode in ("RGBA", "P"):
                        img = img.convert("RGB")
                    img_io = io.BytesIO()
                    img.save(img_io, format="JPEG")
                    image_list.append(img_io.getvalue())
                
                pdf_bytes = img2pdf.convert(image_list)
            
            st.success("✅ PDF generated successfully!")
            st.download_button(
                label="⬇️ Download PDF", 
                data=pdf_bytes, 
                file_name="merged_images.pdf", 
                mime="application/pdf"
            )
