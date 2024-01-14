import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import os
import io

# Add your resolution_um_mapping dictionary here
# Add your resolution_um_mapping dictionary here
resolution_um_mapping = {
    'NIKON TC1 (640 x 480) - 4x': 3.41880341880341,
    'NIKON TC1 (640 x 480) - 10x': 1.34916351861845,
    'NIKON TC1 (640 x 480) - 20x': 0.68259385665529,
    'NIKON TC1 (640 x 480) - 40x': 0.341880341880342,
    'NIKON Ti (Microscope Room) (772 x 618) - 4x': 2.63157894736842,
    'NIKON Ti (Microscope Room) (772 x 618) - 10x': 1.07376785139052,
    'NIKON Ti (Microscope Room) (772 x 618) - 20x': 0.530982849253969,
    'NIKON Ti (Microscope Room) (772 x 618) - 40x': 0.263157894736842,
    'INCUCYTE (1408 x 1040) - 4x': 2.82007896221094,
    'INCUCYTE (1408 x 1040) - 10x': 1.23992560446373,
    'INCUCYTE (1408 x 1040) - 20x': 0.619962802231866,
    'ZEISS L12 (OLD) (1388 x 1040) - 5x': 1.30005200208008,
    'ZEISS L12 (OLD) (1388 x 1040) - 10x': 0.642219510628733,
    'ZEISS L12 (OLD) (1388 x 1040) - 20x': 0.322206469905916,
    'ZEISS L12 (OLD) (1388 x 1040) - 40x': 0.160300081753042,
    'ZEISS L12 (OLD) (1388 x 1040) - 63x': 0.101800857163217,
    'ZEISS L12 (NEW) (2752 x 2208) - 10x': 0.455083280240284,
    'ZEISS L12 (NEW) (2752 x 2208) - 20x': 0.227837142010891,
    'ZEISS L12 (NEW) (2752 x 2208) - 40x': 0.113190034749341,
    'ZOE TC1 TIFF (2592 x 1944) - 20x': 0.381199252849464,
    'NIKON TC1 DISSECTING MICROSCOPE - 0.63x': 9.43396226415094,
    'NIKON TC1 (1280 x 720) - 20x': 1.709401709401705,
    'NIKON TC1 (1280 x 720) - 10x': 0.674581759309225,
    'NIKON TC1 (1280 x 720) - 4x': 0.341296928327645
}

def draw_scale_bar(image, micron_per_pixel, bar_length_microns, bar_position, bar_height, bar_color, label, font_size, font_name, label_x_offset):
    draw = ImageDraw.Draw(image)
    bar_length_pixels = bar_length_microns / micron_per_pixel
    bar_end_position = (bar_position[0] + bar_length_pixels, bar_position[1] + bar_height)
    draw.rectangle([bar_position, bar_end_position], fill=bar_color)

    font_path = f"{font_name}.ttf"
    if os.path.exists(font_path):
        font = ImageFont.truetype(font_path, font_size)
    else:
        st.warning(f"Font file for '{font_name}' not found. Using default font.")
        font = ImageFont.load_default()

    text_position = (bar_position[0] + label_x_offset, bar_position[1] + bar_height + 5)
    draw.text(text_position, label, fill=bar_color, font=font)

    return image

def extract_resolution(key):
    try:
        resolution_part = next(part for part in key.split() if 'x' in part)
        width, height = resolution_part.split('x')
        return int(width.strip()), int(height.strip())
    except (StopIteration, ValueError):
        return None

def crop_to_square(image, crop_offset):
    width, height = image.size
    side_length = min(width, height)
    max_offset = (width - side_length) // 2
    left = max_offset + crop_offset
    right = width - max_offset + crop_offset
    return image.crop((left, 0, right, height))

def save_image(image, filename):
    img_bytes = io.BytesIO()
    image.save(img_bytes, format='TIFF')
    img_bytes.seek(0)
    st.download_button(label="Download Image with Scale Bar",
                       data=img_bytes,
                       file_name=filename,
                       mime="image/tiff")

st.title("Scalebar Overlay Tool")

selected_option = st.selectbox("Select the microscope/objective:", list(resolution_um_mapping.keys()) + ["Custom"])

custom_um_per_pixel = st.text_input("...or enter a custom 'um per pixel' value:") if selected_option == "Custom" else None

if selected_option in resolution_um_mapping:
    micron_per_pixel = resolution_um_mapping[selected_option]
elif custom_um_per_pixel:
    try:
        micron_per_pixel = float(custom_um_per_pixel)
    except ValueError:
        st.error("Please enter a valid number for custom 'um per pixel' value.")
        micron_per_pixel = None
else:
    st.error("Selected resolution does not match any entry in the file.")
    micron_per_pixel = None

uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png", "tif"])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    uploaded_image_resolution = (image.width, image.height)

    expected_resolution = extract_resolution(selected_option) if selected_option != "Custom" else None
    if expected_resolution and uploaded_image_resolution != expected_resolution:
        st.warning(f"The resolution of the uploaded image ({uploaded_image_resolution[0]}x{uploaded_image_resolution[1]}) does not match the expected resolution ({expected_resolution[0]}x{expected_resolution[1]}) for the selected microscope objective.")
    else:
        st.image(image, caption='Uploaded Image', use_column_width=True)

        crop_image = st.checkbox("Crop image to square by removing horizontal pixels")
        if crop_image:
            width, height = image.size
            side_length = min(width, height)
            max_offset = (width - side_length) // 2
            crop_offset = st.slider("Crop Offset", -max_offset, max_offset, 0)
            image = crop_to_square(image, crop_offset)
            st.image(image, caption='Cropped Image', use_column_width=True)

        bar_length_microns = st.number_input("Enter the length of the scale bar in micrometers:", value=100.0, format="%.5f")
        bar_height = st.slider("Select the thickness of the scale bar (pixels):", min_value=1, max_value=20, value=5)
        bar_color = st.color_picker("Select the color of the scale bar", '#FFFFFF')
        font_size = st.slider("Select the font size for the label:", min_value=10, max_value=500, value=20)
        label = st.text_input("Enter the label text (e.g., '100μm'):", value=f'{bar_length_microns}μm')
        font_name = st.selectbox("Select the font for the label:", ['myriad pro', 'arial', 'times new roman', 'verdana', 'courier new'])
        label_x_offset = st.slider("Adjust the horizontal position of the label:", min_value=-100, max_value=100, value=0)

        x_position = st.number_input("Enter the X position for the scale bar:", value=int(image.width - 200), min_value=0)
        y_position = st.number_input("Enter the Y position for the scale bar:", value=int(image.height - 50), min_value=0)

        if st.button('Add Scale Bar'):
            result_image = draw_scale_bar(image, micron_per_pixel, bar_length_microns, (x_position, y_position), bar_height, bar_color, label, font_size, font_name, label_x_offset)
            st.image(result_image, caption='Image with Scale Bar', use_column_width=True)

            # Save and provide a download link for the image
            file_name = f"{uploaded_file.name.split('.')[0]}_scalebar_{bar_length_microns}um.tiff"
            save_image(result_image, file_name)
