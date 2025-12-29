import os
from flask import Flask, render_template, request, jsonify, send_from_directory
from PIL import Image, ImageEnhance, ImageOps, ImageFilter
import base64
from io import BytesIO
import uuid
import numpy as np
import cv2

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
PROCESSED_FOLDER = 'processed'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PROCESSED_FOLDER'] = PROCESSED_FOLDER

# Ensure directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

# --- Image Conversion Helpers ---

def pil_to_cv2(pil_image):
    """Converts a Pillow Image to an OpenCV image (numpy array), handling RGBA."""
    if pil_image.mode == 'RGBA':
        return cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGBA2BGRA)
    else:
        return cv2.cvtColor(np.array(pil_image.convert('RGB')), cv2.COLOR_RGB2BGR)

def cv2_to_pil(cv2_image):
    """Converts an OpenCV image (numpy array) to a Pillow Image."""
    if cv2_image.shape[2] == 4:
        return Image.fromarray(cv2.cvtColor(cv2_image, cv2.COLOR_BGRA2RGBA))
    else:
        return Image.fromarray(cv2.cvtColor(cv2_image, cv2.COLOR_BGR2RGB))

# --- Decoding and Encoding ---

def encode_cv2_image_to_base64(cv2_image):
    """Encodes an OpenCV image to a base64 data URL."""
    pil_image = cv2_to_pil(cv2_image)
    buffered = BytesIO()
    pil_image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return "data:image/png;base64," + img_str

# --- Professional Adjustment Functions (OpenCV-based) ---

def apply_brightness_contrast(image, brightness, contrast):
    b = float(brightness)
    c = float(contrast)
    if b != 0:
        shadow, highlight = 0, 255
        alpha_b = (highlight - shadow) / 255
        gamma_b = shadow
        image = cv2.addWeighted(image, alpha_b, image, 0, gamma_b + b)
    if c != 0:
        f = 131 * (c + 127) / (127 * (131 - c))
        alpha_c, gamma_c = f, 127 * (1 - f)
        image = cv2.addWeighted(image, alpha_c, image, 0, gamma_c)
    return image

def apply_saturation(image, saturation_value):
    s = float(saturation_value)
    if s == 0: return image
    image_hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV).astype("float32")
    h, sat, v = cv2.split(image_hsv)
    factor = (s + 100) / 100.0
    sat = np.clip(sat * factor, 0, 255)
    image_hsv = cv2.merge([h, sat, v])
    return cv2.cvtColor(image_hsv.astype("uint8"), cv2.COLOR_HSV2BGR)

def apply_temperature(image, temp_value):
    t = float(temp_value)
    if t == 0: return image
    increase = np.interp(np.arange(256), [0, 255], [0, abs(t) * 2])
    lut_b, lut_r = (np.arange(256) - increase, np.arange(256) + increase) if t > 0 else (np.arange(256) + increase, np.arange(256) - increase)
    lut_r = np.clip(lut_r, 0, 255).astype(np.uint8)
    lut_b = np.clip(lut_b, 0, 255).astype(np.uint8)
    b, g, r = cv2.split(image)
    r = cv2.LUT(r, lut_r)
    b = cv2.LUT(b, lut_b)
    return cv2.merge((b, g, r))

def apply_highlights(image, highlight_value):
    h = float(highlight_value)
    if h == 0: return image
    image_lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(image_lab)
    l_out = np.clip(l + (h / 100.0) * (255 - l), 0, 255).astype(np.uint8)
    merged_lab = cv2.merge((l_out, a, b))
    return cv2.cvtColor(merged_lab, cv2.COLOR_LAB2BGR)

def apply_shadows(image, shadow_value):
    s = float(shadow_value)
    if s == 0: return image
    image_lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(image_lab)
    l_out = np.clip(l + (s / 100.0) * l, 0, 255).astype(np.uint8)
    merged_lab = cv2.merge((l_out, a, b))
    return cv2.cvtColor(merged_lab, cv2.COLOR_LAB2BGR)

def apply_exposure(image, exposure_value):
    e = float(exposure_value)
    if e == 0: return image
    gamma = 1 - (e / 125.0)
    invGamma = 1.0 / gamma
    table = np.array([((i / 255.0) ** invGamma) * 255 for i in np.arange(0, 256)]).astype("uint8")
    return cv2.LUT(image, table)

def apply_vibrance(image, vibrance_value):
    v = float(vibrance_value)
    if v == 0: return image
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV).astype(np.float32)
    h, s, val = cv2.split(hsv)
    s_factor = v / 100.0
    mask = s < 180 
    s[mask] = np.clip(s[mask] + s_factor * (255 - s[mask]), 0, 255)
    hsv = cv2.merge([h, s, val])
    return cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)

def apply_clarity(image, clarity_value):
    c = float(clarity_value)
    if c == 0: return image
    blurred = cv2.GaussianBlur(image, (0, 0), 5)
    usm = cv2.addWeighted(image, 1.0 + (c/100.0), blurred, -(c/100.0), 0)
    return usm

def apply_hsl(image, hsl_adjustments):
    if not hsl_adjustments: return image
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV).astype(np.float32)
    h, s, v = cv2.split(hsv)
    color_ranges = {'red': ((-10, 10), (170, 180)), 'yellow': ((15, 35),), 'green': ((40, 80),), 'cyan': ((85, 105),), 'blue': ((110, 130),), 'magenta': ((140, 165),)}
    for color, adjustments in hsl_adjustments.items():
        if color not in color_ranges: continue
        hue_adj, sat_adj, lum_adj = float(adjustments.get('h', 0)), float(adjustments.get('s', 0)) / 100.0, float(adjustments.get('l', 0))
        mask = np.zeros_like(h, dtype=bool)
        for r in color_ranges[color]:
            lower, upper = r[0] % 180, r[1] % 180
            if lower > upper: mask |= (h >= lower) | (h <= upper)
            else: mask |= (h >= lower) & (h <= upper)
        if hue_adj != 0: h[mask] = (h[mask] + hue_adj) % 180
        if sat_adj != 0: s[mask] = np.clip(s[mask] * (1.0 + sat_adj), 0, 255)
        if lum_adj != 0: v[mask] = np.clip(v[mask] + lum_adj, 0, 255)
    final_hsv = cv2.merge([h, s, v])
    return cv2.cvtColor(final_hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)

# --- Flask Routes ---

@app.route('/')
def index():
    return render_template('index.html')

def decode_image(data_url):
    header, encoded = data_url.split(",", 1)
    image_data = base64.b64decode(encoded)
    image = Image.open(BytesIO(image_data))
    if image.mode != 'RGBA': image = image.convert('RGBA')
    return image

def encode_image(image):
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return "data:image/png;base64," + img_str

@app.route('/api/pro_adjust', methods=['POST'])
def pro_adjust_route():
    data = request.json
    try:
        pil_rgba = decode_image(data['imageData'])
        pil_rgb = pil_rgba.convert('RGB')
        alpha_channel = np.array(pil_rgba.getchannel('A'))
        cv_image_bgr = cv2.cvtColor(np.array(pil_rgb), cv2.COLOR_RGB2BGR)
        adjustments = data.get('adjustments', {})
        if 'exposure' in adjustments: cv_image_bgr = apply_exposure(cv_image_bgr, adjustments['exposure'])
        if 'temperature' in adjustments: cv_image_bgr = apply_temperature(cv_image_bgr, adjustments['temperature'])
        if 'brightness' in adjustments or 'contrast' in adjustments: cv_image_bgr = apply_brightness_contrast(cv_image_bgr, adjustments.get('brightness', 0), adjustments.get('contrast', 0))
        if 'highlights' in adjustments: cv_image_bgr = apply_highlights(cv_image_bgr, adjustments['highlights'])
        if 'shadows' in adjustments: cv_image_bgr = apply_shadows(cv_image_bgr, adjustments['shadows'])
        if 'clarity' in adjustments: cv_image_bgr = apply_clarity(cv_image_bgr, adjustments['clarity'])
        if 'vibrance' in adjustments: cv_image_bgr = apply_vibrance(cv_image_bgr, adjustments['vibrance'])
        if 'saturation' in adjustments: cv_image_bgr = apply_saturation(cv_image_bgr, adjustments['saturation'])
        if 'hsl' in adjustments: cv_image_bgr = apply_hsl(cv_image_bgr, adjustments['hsl'])
        cv_image_bgra = cv2.cvtColor(cv_image_bgr, cv2.COLOR_BGR2BGRA)
        cv_image_bgra[:, :, 3] = alpha_channel
        result_url = encode_cv2_image_to_base64(cv_image_bgra)
        return jsonify({'imageUrl': result_url})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# --- Legacy and Basic Operation Routes ---
@app.route('/api/trim', methods=['POST'])
def trim_image():
    data = request.json
    try:
        image = decode_image(data['imageData'])
        bbox = image.getbbox()
        if bbox: image = image.crop(bbox)
        return jsonify({'imageUrl': encode_image(image)})
    except Exception as e: return jsonify({'error': str(e)}), 500

@app.route('/api/resize', methods=['POST'])
def resize_image_route():
    data = request.json
    try:
        image = decode_image(data['imageData'])
        width = int(data.get('width', 0))
        if width <= 0: return jsonify({'error': 'A valid width must be provided.'}), 400
        h = int(width * image.height / image.width)
        resized_image = image.resize((width, h), Image.Resampling.LANCZOS)
        return jsonify({'imageUrl': encode_image(resized_image)})
    except Exception as e: return jsonify({'error': str(e)}), 500

@app.route('/api/flip', methods=['POST'])
def flip_image():
    data = request.json
    try:
        image = decode_image(data['imageData'])
        return jsonify({'imageUrl': encode_image(image.transpose(Image.FLIP_LEFT_RIGHT))})
    except Exception as e: return jsonify({'error': str(e)}), 500

@app.route('/api/flip_vertical', methods=['POST'])
def flip_image_vertical():
    data = request.json
    try:
        image = decode_image(data['imageData'])
        return jsonify({'imageUrl': encode_image(image.transpose(Image.FLIP_TOP_BOTTOM))})
    except Exception as e: return jsonify({'error': str(e)}), 500

@app.route('/api/crop', methods=['POST'])
def crop_image():
    data = request.json
    try:
        image = decode_image(data['imageData'])
        x, y, w, h = int(data['x']), int(data['y']), int(data['width']), int(data['height'])
        return jsonify({'imageUrl': encode_image(image.crop((x, y, x + w, y + h)))})
    except Exception as e: return jsonify({'error': str(e)}), 500

@app.route('/api/rotate', methods=['POST'])
def rotate_image_route():
    data = request.json
    try:
        image = decode_image(data['imageData'])
        angle = float(data.get('angle', 0))
        return jsonify({'imageUrl': encode_image(image.rotate(angle, expand=True, fillcolor=(0,0,0,0)))})
    except Exception as e: return jsonify({'error': str(e)}), 500

# --- Adjustment Routes (Legacy Pillow) ---
@app.route('/api/adjust/<string:adj_type>', methods=['POST'])
def adjust_route(adj_type):
    data = request.json
    try:
        image = decode_image(data['imageData'])
        factor = float(data.get('factor', 1.0))
        enhancer_map = {'saturation': ImageEnhance.Color, 'brightness': ImageEnhance.Brightness, 'contrast': ImageEnhance.Contrast, 'sharpness': ImageEnhance.Sharpness}
        enhancer = enhancer_map.get(adj_type)
        if not enhancer: return jsonify({'error': f'Adjustment "{adj_type}" not found.'}), 404
        return jsonify({'imageUrl': encode_image(enhancer(image).enhance(factor))})
    except Exception as e: return jsonify({'error': str(e)}), 500

# --- Filter Routes ---
def apply_sepia_filter(image):
    if image.mode != 'RGBA': image = image.convert('RGBA')
    alpha = image.split()[3]
    rgb_image = image.convert('RGB')
    sepia_matrix = [0.393, 0.769, 0.189, 0, 0.349, 0.686, 0.168, 0, 0.272, 0.534, 0.131, 0]
    sepia_rgb_image = rgb_image.convert("RGB", sepia_matrix)
    sepia_rgb_image.putalpha(alpha)
    return sepia_rgb_image

@app.route('/api/filter/<string:filter_name>', methods=['POST'])
def simple_pillow_filter(filter_name):
    data = request.json
    try:
        image = decode_image(data['imageData'])
        if filter_name == 'grayscale':
            processed_image = image.convert('L')
        elif filter_name == 'sepia':
            processed_image = apply_sepia_filter(image)
        elif filter_name == 'invert':
            if image.mode == 'RGBA':
                r,g,b,a = image.split()
                rgb_image = Image.merge('RGB', (r,g,b))
                inverted_image = ImageOps.invert(rgb_image)
                r,g,b = inverted_image.split()
                processed_image = Image.merge('RGBA', (r,g,b,a))
            else:
                processed_image = ImageOps.invert(image)
        else:
            filter_constant_name = filter_name.upper().replace('-', '_')
            pillow_filter = getattr(ImageFilter, filter_constant_name, None)
            if not pillow_filter:
                return jsonify({'error': f'Filter "{filter_name}" not found.'}), 404
            processed_image = image.filter(pillow_filter)
        
        return jsonify({'imageUrl': encode_image(processed_image)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5510)