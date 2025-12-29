## Project Overview

This project is a web-based image processing tool built with Python. It uses the Flask framework for the backend and the Pillow library for image manipulation. The frontend is a single-page application using HTML, CSS, and vanilla JavaScript, which provides a user-friendly interface for image operations.

**Key Technologies:**

*   **Backend:** Python, Flask
*   **Image Processing:** Pillow
*   **Frontend:** HTML, CSS, JavaScript (with HTML5 Canvas)

**Architecture:**

The application follows a simple client-server model.
- The **backend** (`app.py`) exposes a set of RESTful APIs for various image operations like trimming, resizing, rotating, applying filters, and adjusting image properties. It handles image data encoded in base64 format.
- The **frontend** (`templates/index.html`) allows users to upload an image, which is then displayed on an HTML Canvas. User actions trigger JavaScript functions that send API requests to the backend with the current image data. The backend processes the image and returns the new image, which is then displayed on the canvas.

The project structure includes:
- `app.py`: The main Flask application file.
- `requirements.txt`: A list of Python dependencies.
- `templates/index.html`: The HTML file for the user interface.
- `uploads/`: A directory for storing uploaded images.
- `processed/`: A directory for storing processed images.

## Building and Running

### 1. Environment Setup

It is recommended to use a Python virtual environment to manage dependencies.

```bash
# Create a virtual environment
python3 -m venv venv

# Activate the virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
.\\venv\\Scripts\\activate
```

### 2. Install Dependencies

Install the required Python packages using pip:

```bash
pip install -r requirements.txt
```

### 3. Running the Application

There are two ways to run the Flask application:

**Method 1: Using the `flask` command**

```bash
export FLASK_APP=app.py
export FLASK_ENV=development
flask run --port 5510
```

**Method 2: Directly running the Python script**

```bash
python app.py
```

The application will be available at `http://127.0.0.1:5510`.

## Development Conventions

*   **Backend:** The backend is written in Python using the Flask framework. Code is organized into functions that correspond to API endpoints.
*   **Frontend:** The frontend uses vanilla JavaScript to interact with the backend. Image manipulations are visualized using the HTML5 Canvas.
*   **API:** The API is designed to be RESTful, with endpoints for each image processing operation. Image data is transferred between the client and server as base64-encoded strings within JSON payloads.
*   **Styling:** The UI is styled with CSS within the `index.html` file, providing a clean and straightforward user experience.
