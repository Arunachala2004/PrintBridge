import streamlit as st
import tempfile
#import os
import platform
from PIL import Image, ImageOps
#import numpy as np
from io import BytesIO
import qrcode

amt = 0
quantity = 1
cost = 2
# OS-specific printing modules
if platform.system() == "Windows":
    import win32print
    import win32api
elif platform.system() == "Linux":
    import cups


def print_file(file_path, copies, color, duplex):
    """Send file to printer with options"""
    if platform.system() == "Windows":
        printer_name = win32print.GetDefaultPrinter()
        hprinter = win32print.OpenPrinter(printer_name)
        printer_info = win32print.GetPrinter(hprinter, 2)
        pdc = win32print.GetDefaultPrinter()

        print_options = f'/d:"{printer_name}"'

        if duplex:
            print_options += " /duplex"

        if color:
            print_options += " /color"

        for _ in range(copies):
            win32api.ShellExecute(0, "print", file_path, print_options, ".", 0)

        st.success(f"Sent to printer: {printer_name} ({copies} copies)")

    elif platform.system() == "Linux":
        conn = cups.Connection()
        printers = conn.getPrinters()
        if printers:
            printer_name = list(printers.keys())[0]
            options = {
                "copies": str(copies),
                "sides": "two-sided-long-edge" if duplex else "one-sided",
                "ColorMode": "color" if color else "monochrome"
            }
            conn.printFile(printer_name, file_path, "Streamlit Print Job", options)
            st.success(f"Sent to printer: {printer_name} ({copies} copies)")
        else:
            st.error("No printers found.")
    else:
        st.error("Printing is not supported on this OS.")


def resize_to_a4(image):
    """Resize image to fit A4 (210mm x 297mm) while maintaining aspect ratio"""
    a4_size = (2480, 3508)  # A4 size in pixels at 300 DPI
    #return ImageOps.fit(image, a4_size, Image.ANTIALIAS)
    return ImageOps.fit(image, a4_size, Image.LANCZOS)


# Streamlit UI
st.title("🖨 Print Documents App with Editing")

uploaded_file = st.file_uploader("Upload a file (PDF, TXT, or Image)", type=["pdf", "txt", "png", "jpg", "jpeg"])

if uploaded_file is not None:
    file_ext = uploaded_file.name.split(".")[-1].lower()

    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_ext}") as temp_file:
        temp_file.write(uploaded_file.getbuffer())
        temp_path = temp_file.name

    st.success(f"Uploaded: {uploaded_file.name}")

    if file_ext in ["png", "jpg", "jpeg"]:
        image = Image.open(uploaded_file)

        # Image Cropping
        st.subheader("Edit Image")
        st.image(image, caption="Original Image", use_column_width=True)

        left, right = st.slider("Crop Left & Right", 0, image.width, (0, image.width))
        top, bottom = st.slider("Crop Top & Bottom", 0, image.height, (0, image.height))

        cropped_image = image.crop((left, top, right, bottom))
        resized_image = resize_to_a4(cropped_image)

        st.image(resized_image, caption="Resized for A4", use_column_width=True)

        # Save edited image
        edited_image_path = temp_path.replace(file_ext, "edited.png")
        resized_image.save(edited_image_path)
        temp_path = edited_image_path

    # Print Options
    st.subheader("Print Options")
    copies = st.number_input("Number of Copies", min_value=1, max_value=50, value=1, step=1)
    duplex = st.checkbox("Print on Both Sides (Duplex)")
    color = st.checkbox("Print in Color")
    if duplex:
        quantity = 1.5
    if color:
        cost = 10
    amt = quantity * cost * copies
    upi_front = "upi://pay?pa=srirogu@okaxis&pn=Sritharan Xerox&am="
    upi_mid = str(amt)
    upi_back = "&cu=INR"
    upi_link = upi_front + upi_mid + upi_back
    amt = quantity * cost

    if st.button("Print Document"):
        qr = qrcode.QRCode(
            version=1,  # QR code complexity (1-40, 1 is the smallest)
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4
        )
        qr.add_data(upi_link)
        qr.make(fit=True)

        # Create an image from the QR code
        qr_img = qr.make_image(fill="black", back_color="white")

        # Convert to bytes
        image_bytes = BytesIO()
        qr_img.save(image_bytes, format="PNG")  # Save as PNG format
        image_bytes.seek(0)  # Move to the start of the byte stream

        # Display QR code in Streamlit
        st.success(upi_link)
        st.image(image_bytes, caption="UPI Payment QR Code", use_column_width=True)
        print_file(temp_path, copies, color, duplex)

    # Define UPI payment link
    upi_link = upi_front + upi_mid + upi_back

    # Generate QR code
    qr = qrcode.make(upi_link)

    # Save the QR code as an image
    st.image(image_bytes, caption="Example Image", use_column_width=True)

    print("QR code saved as upi_payment_qr.png")
