import os
from flask import Flask, render_template, request, jsonify, send_from_directory
from PIL import Image, ImageEnhance, ImageOps, ImageFilter
import base64
from io import BytesIO
import uuid

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
PROCESSED_FOLDER = 'processed'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PROCESSED_FOLDER'] = PROCESSED_FOLDER

# Ensure directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/processed/<filename>')
def processed_file(filename):
    return send_from_directory(app.config['PROCESSED_FOLDER'], filename)

# Base64 decode helper
def decode_image(data_url):
    # The data URL is expected to be in the format: "data:image/png;base64,ENCODED_STRING"
    header, encoded = data_url.split(",", 1)
    image_data = base64.b64decode(encoded)
    image = Image.open(BytesIO(image_data))
    # Ensure image is in a mode that supports transparency for certain operations
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    return image

# Base64 encode helper
def encode_image(image):
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return "data:image/png;base64," + img_str

@app.route('/api/trim', methods=['POST'])
def trim_image():
    data = request.json
    try:
        image = decode_image(data['imageData'])
        
        # Get the bounding box of the non-alpha part of the image
        bbox = image.getbbox()
        if bbox:
            image = image.crop(bbox)
        
        result_url = encode_image(image)
        return jsonify({'imageUrl': result_url})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/resize', methods=['POST'])
def resize_image_route():
    data = request.json
    try:
        image = decode_image(data['imageData'])
        width = int(data.get('width', 0))
        
        # We only need one dimension to maintain aspect ratio
        if width <= 0:
            return jsonify({'error': 'A valid width must be provided.'}), 400

        original_width, original_height = image.size
        aspect_ratio = original_height / original_width
        new_height = int(width * aspect_ratio)
        new_size = (width, new_height)

        resized_image = image.resize(new_size, Image.Resampling.LANCZOS)
        result_url = encode_image(resized_image)

        return jsonify({'imageUrl': result_url})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/flip', methods=['POST'])
def flip_image():
    data = request.json
    try:
        image = decode_image(data['imageData'])
        flipped_image = image.transpose(Image.FLIP_LEFT_RIGHT)
        result_url = encode_image(flipped_image)
        return jsonify({'imageUrl': result_url})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/flip_vertical', methods=['POST'])
def flip_image_vertical():
    data = request.json
    try:
        image = decode_image(data['imageData'])
        flipped_image = image.transpose(Image.FLIP_TOP_BOTTOM)
        result_url = encode_image(flipped_image)
        return jsonify({'imageUrl': result_url})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/crop', methods=['POST'])
def crop_image():
    data = request.json
    try:
        image = decode_image(data['imageData'])
        x = int(data['x'])
        y = int(data['y'])
        width = int(data['width'])
        height = int(data['height'])
        
        # The crop box is a 4-tuple (left, upper, right, lower)
        cropped_image = image.crop((x, y, x + width, y + height))
        result_url = encode_image(cropped_image)
        
        return jsonify({'imageUrl': result_url})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/rotate', methods=['POST'])
def rotate_image_route():
    data = request.json
    try:
        image = decode_image(data['imageData'])
        angle = float(data.get('angle', 0))
        
        # Rotate the image. `expand=True` makes sure the output image is large enough to hold the entire rotated image.
        # `fillcolor=(0,0,0,0)` makes the background transparent.
        rotated_image = image.rotate(angle, expand=True, fillcolor=(0,0,0,0))
        result_url = encode_image(rotated_image)

        return jsonify({'imageUrl': result_url})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/adjust_saturation', methods=['POST'])
def adjust_saturation_route():
    data = request.json
    try:
        image = decode_image(data['imageData'])
        factor = float(data.get('factor', 1.0))
        
        enhancer = ImageEnhance.Color(image)
        enhanced_image = enhancer.enhance(factor)
        
        result_url = encode_image(enhanced_image)

        return jsonify({'imageUrl': result_url})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/adjust/brightness', methods=['POST'])
def adjust_brightness_route():
    data = request.json
    try:
        image = decode_image(data['imageData'])
        factor = float(data.get('factor', 1.0))
        enhancer = ImageEnhance.Brightness(image)
        enhanced_image = enhancer.enhance(factor)
        result_url = encode_image(enhanced_image)
        return jsonify({'imageUrl': result_url})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/adjust/contrast', methods=['POST'])
def adjust_contrast_route():
    data = request.json
    try:
        image = decode_image(data['imageData'])
        factor = float(data.get('factor', 1.0))
        enhancer = ImageEnhance.Contrast(image)
        enhanced_image = enhancer.enhance(factor)
        result_url = encode_image(enhanced_image)
        return jsonify({'imageUrl': result_url})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/adjust/sharpness', methods=['POST'])
def adjust_sharpness_route():
    data = request.json
    try:
        image = decode_image(data['imageData'])
        factor = float(data.get('factor', 1.0))
        enhancer = ImageEnhance.Sharpness(image)
        enhanced_image = enhancer.enhance(factor)
        result_url = encode_image(enhanced_image)
        return jsonify({'imageUrl': result_url})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --- Filters ---
def apply_sepia_filter(image):
    """
    Apply a sepia filter to the image using a color matrix conversion for efficiency.
    """
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    
    # Preserve the alpha channel
    alpha = image.split()[3]

    # Convert to RGB before applying the matrix
    rgb_image = image.convert('RGB')

    # Apply the sepia matrix to the RGB channels
    sepia_matrix = [
        0.393, 0.769, 0.189, 0,
        0.349, 0.686, 0.168, 0,
        0.272, 0.534, 0.131, 0
    ]
    sepia_rgb_image = rgb_image.convert("RGB", sepia_matrix)
    
    # Re-add the alpha channel
    sepia_rgb_image.putalpha(alpha)
    
    return sepia_rgb_image

@app.route('/api/filter/grayscale', methods=['POST'])
def filter_grayscale_route():
    data = request.json
    try:
        image = decode_image(data['imageData'])
        grayscale_image = image.convert('L')
        result_url = encode_image(grayscale_image)
        return jsonify({'imageUrl': result_url})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/filter/sepia', methods=['POST'])
def filter_sepia_route():
    data = request.json
    try:
        image = decode_image(data['imageData'])
        sepia_image = apply_sepia_filter(image)
        result_url = encode_image(sepia_image)
        return jsonify({'imageUrl': result_url})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/filter/invert', methods=['POST'])
def filter_invert_route():
    data = request.json
    try:
        image = decode_image(data['imageData'])
        # Invert needs an RGB image, not RGBA
        if image.mode == 'RGBA':
            r,g,b,a = image.split()
            rgb_image = Image.merge('RGB', (r,g,b))
            inverted_image = ImageOps.invert(rgb_image)
            r,g,b = inverted_image.split()
            final_image = Image.merge('RGBA', (r,g,b,a))
        else:
            final_image = ImageOps.invert(image)

        result_url = encode_image(final_image)
        return jsonify({'imageUrl': result_url})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/filter/sharpen', methods=['POST'])
def filter_sharpen_route():
    data = request.json
    try:
        image = decode_image(data['imageData'])
        sharpened_image = image.filter(ImageFilter.SHARPEN)
        result_url = encode_image(sharpened_image)
        return jsonify({'imageUrl': result_url})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/filter/blur', methods=['POST'])
def filter_blur_route():
    data = request.json
    try:
        image = decode_image(data['imageData'])
        blurred_image = image.filter(ImageFilter.BLUR)
        result_url = encode_image(blurred_image)
        return jsonify({'imageUrl': result_url})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/filter/contour', methods=['POST'])
def filter_contour_route():
    data = request.json
    try:
        image = decode_image(data['imageData'])
        contoured_image = image.filter(ImageFilter.CONTOUR)
        result_url = encode_image(contoured_image)
        return jsonify({'imageUrl': result_url})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/filter/edge_enhance', methods=['POST'])
def filter_edge_enhance_route():
    data = request.json
    try:
        image = decode_image(data['imageData'])
        edge_enhanced_image = image.filter(ImageFilter.EDGE_ENHANCE)
        result_url = encode_image(edge_enhanced_image)
        return jsonify({'imageUrl': result_url})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5510)
