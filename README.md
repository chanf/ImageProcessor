# 简易图片处理工具

这是一个基于 Flask 和 Pillow 库构建的简易图片处理 Web 应用程序。它提供了一个直观的 Web 界面，允许用户上传图片，并进行基本的图片操作，如裁剪透明区域、左右翻转、按宽度等比缩放以及自定义区域裁剪。

## 功能

*   **图片上传**: 支持用户从本地上传图片。
*   **裁剪透明区域**: 自动裁剪图片四周的透明空白区域。
*   **左右翻转**: 将图片水平翻转。
*   **按宽度等比缩放**: 用户输入目标宽度，图片将按比例缩放。
*   **区域裁剪**: 用户可以在图片上拖动选择区域进行精确裁剪。
*   **实时预览**: 所有操作都在前端即时显示效果。
*   **图片下载**: 处理后的图片可以下载到本地。

## 技术栈

*   **后端**:
    *   Python 3
    *   Flask (Web 框架)
    *   Pillow (图像处理库)
*   **前端**:
    *   HTML5
    *   CSS3
    *   JavaScript (使用 Canvas 进行图片操作和预览)

## 环境搭建与运行

请按照以下步骤在本地设置和运行项目：

### 1. 克隆仓库

首先，将项目仓库克隆到您的本地机器：

```bash
git clone git@github.com:chanf/ImageProcessor.git
cd ImageProcessor
```

### 2. 创建并激活虚拟环境

推荐使用虚拟环境来管理项目依赖：

```bash
python3 -m venv venv
# Windows
.\venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### 3. 安装依赖

激活虚拟环境后，安装 `requirements.txt` 中列出的所有依赖：

```bash
pip install -r requirements.txt
```

### 4. 运行应用

设置 Flask 应用并启动服务器：

```bash
export FLASK_APP=app.py
export FLASK_ENV=development # 或者根据需要设置为 production
flask run --port 5510
```

或者直接运行 `app.py`：

```bash
python app.py
```

应用将运行在 `http://127.0.0.1:5510/`。

### 5. 访问应用

在您的 Web 浏览器中打开 `http://127.0.0.1:5510/` 即可开始使用。

## 使用方法

1.  **上传图片**: 点击 "上传图片" 按钮，选择您想要处理的图片。
2.  **执行操作**:
    *   点击 "裁剪透明区域" 按钮自动裁剪。
    *   点击 "左右翻转" 按钮翻转图片。
    *   在 "按宽度等比缩放" 输入框中输入新的宽度，然后点击 "确认缩放"。
    *   在图片预览区域拖动鼠标选择一个区域，然后点击 "裁剪选中区域" 进行裁剪。
3.  **下载图片**: 操作完成后，点击 "下载处理后的图片" 按钮将图片保存到本地。

## 项目结构

```
.
├── app.py                  # Flask 后端应用主文件，处理图片操作 API
├── requirements.txt        # Python 依赖列表
├── templates/
│   └── index.html          # 前端 HTML 页面，提供用户界面
├── uploads/                # 原始图片上传目录 (运行时创建)
└── processed/              # 处理后的图片输出目录 (运行时创建)
```
