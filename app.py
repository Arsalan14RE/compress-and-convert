import streamlit as st
import fitz  # PyMuPDF
from PIL import Image
import io
import img2pdf
import zipfile
import base64  # Needed to embed the icon
import os
# Hide the GitHub menu and Streamlit footer, but KEEP the header and sidebar button
hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            .stAppDeployButton {display:none;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)
# --- ADVANCED PWA ICON HACK ---
# This block reads your icon.png and embeds it as base64 data in the HTML header.
# This makes it load properly on mobile home screens even locally.
icon_path = os.path.join(os.path.dirname(__file__), "icon.png")

icon_header_html = ""
favicon_data = ""

if os.path.exists(icon_path):
    try:
        # 1. Prepare Favicon for Browser Tabs
        fav_img = Image.open(icon_path)
        fav_io = io.BytesIO()
        fav_img.save(fav_io, format="PNG")
        favicon_data = fav_io.getvalue()

        # 2. Prepare high-res icons for mobile Home Screen
        with open(icon_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()
            
        # Create HTML link tags pointing to the base64 data
        icon_header_html = f"""
        <link rel="apple-touch-icon" sizes="512x512" href="data:image/png;base64,{encoded_string}">
        <link rel="icon" type="image/png" sizes="512x512" href="data:image/png;base64,{encoded_string}">
        <link rel="manifest" href="data:application/manifest+json;base64,{{
          "name": "Local Docs Toolkit",
          "short_name": "Docs Toolkit",
          "start_url": ".",
          "display": "standalone",
          "background_color": "#ffffff",
          "description": "Private file tools.",
          "icons": [
            {{
              "src": "data:image/png;base64,{encoded_string}",
              "sizes": "512x512",
              "type": "image/png",
              "purpose": "any maskable"
            }}
          ]
        }}">
        """
    except Exception as e:
        print(f"Error processing icon: {e}")
else:
    print(f"icon.png not found at {icon_path}. Skipping PWA setup.")

# --- INITIAL SETUP ---
# Pass the favicon data (if it exists) to set the tab icon
if favicon_data:
    st.set_page_config(page_title="Local Docs Toolkit", page_icon=Image.open(io.BytesIO(favicon_data)), layout="centered")
else:
    st.set_page_config(page_title="Local Docs Toolkit", layout="centered")

# Inject the advanced PWA icon code into the HTML head
if icon_header_html:
    st.markdown(icon_header_html, unsafe_allow_html=True)


# --- APPLICATION CODE (SAME AS BEFORE) ---
st.title("🗜️ Local Docs Toolkit")
st.write("100% private file conversion and compression. Your data never leaves your computer.")

# Sidebar navigation
option = st.sidebar.selectbox(
    "Choose a tool", 
    ["Compress Image", "Compress PDF", "PDF to Images", "Images to PDF"]
)

if option == "Compress Image":
    st.header("Compress Image")
    uploaded_file = st.file_uploader("Upload Image (JPG/PNG)", type=['png', 'jpg', 'jpeg'])
    quality = st.slider("Compression Quality", 10, 100, 70)
    
    if uploaded_file:
        img = Image.open(uploaded_file)
        # Convert RGBA (like PNGs with transparency) to RGB for JPEG saving
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
            
        out_io = io.BytesIO()
        img.save(out_io, format="JPEG", quality=quality)
        
        st.write(f"**Original size:** {uploaded_file.size / 1024:.2f} KB")
        st.write(f"**Compressed size:** {out_io.getbuffer().nbytes / 1024:.2f} KB")
        
        st.download_button(
            label="Download Compressed Image", 
            data=out_io, 
            file_name=f"compressed_{uploaded_file.name}", 
            mime="image/jpeg"
        )

elif option == "Compress PDF":
    st.header("Compress PDF")
    uploaded_file = st.file_uploader("Upload PDF", type=['pdf'])
    
    if uploaded_file:
        # Load the PDF from memory
        doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        out_io = io.BytesIO()
        
        # Save with garbage collection and deflation to reduce size losslessly
        doc.save(out_io, garbage=4, deflate=True, clean=True)
        
        st.write(f"**Original size:** {uploaded_file.size / 1024 / 1024:.2f} MB")
        st.write(f"**Compressed size:** {out_io.getbuffer().nbytes / 1024 / 1024:.2f} MB")
        
        st.download_button(
            label="Download Compressed PDF", 
            data=out_io, 
            file_name=f"compressed_{uploaded_file.name}", 
            mime="application/pdf"
        )

elif option == "PDF to Images":
    st.header("Convert PDF to Images")
    uploaded_file = st.file_uploader("Upload PDF", type=['pdf'])
    dpi = st.slider("Resolution (DPI)", 72, 300, 150)
    
    if uploaded_file:
        doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        
        if st.button("Convert to Images"):
            zip_buffer = io.BytesIO()
            # Create a zip file in memory to hold all the generated images
            with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
                for page_num in range(len(doc)):
                    page = doc.load_page(page_num)
                    pix = page.get_pixmap(dpi=dpi)
                    img_bytes = pix.tobytes("jpeg")
                    zip_file.writestr(f"page_{page_num + 1}.jpg", img_bytes)
            
            st.success("Conversion complete!")
            st.download_button(
                label="Download ZIP of Images", 
                data=zip_buffer.getvalue(), 
                file_name=f"{uploaded_file.name}_images.zip", 
                mime="application/zip"
            )

elif option == "Images to PDF":
    st.header("Convert Images to PDF")
    uploaded_files = st.file_uploader("Upload Images", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True)
    
    if uploaded_files:
        if st.button("Convert to PDF"):
            image_list = []
            for file in uploaded_files:
                img = Image.open(file)
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")
                img_io = io.BytesIO()
                img.save(img_io, format="JPEG")
                image_list.append(img_io.getvalue())
            
            # Combine all image bytes into a single PDF
            pdf_bytes = img2pdf.convert(image_list)
            st.success("PDF generated successfully!")
            st.download_button(
                label="Download PDF", 
                data=pdf_bytes, 
                file_name="merged_images.pdf", 
                mime="application/pdf"
            )
