# AnimationEngine 🚀

AnimationEngine (Video to Unity Sprite Converter) is a Python-based desktop application built with **PyQt6** designed to streamline the game development workflow. It automates the extraction and conversion of video sequences into clean, ready-to-use 2D sprite frames geared especially for **Unity** and other game engines.

## 🌟 Key Features

*   **Intelligent Frame Extraction:** Extract specific frames using predefined skip rates or resample videos to a target FPS to easily match in-engine animation rates.
*   **AI-Driven Background Removal:** Leverages `rembg` with robust **ONNX** models (e.g., `u2net`, `isnet-general-use`, `birefnet-general`) to cleanly separate characters from backgrounds.
*   **Advanced Matting & Cleanup:** Built-in edge refinement through alpha matting, edge smoothing, and automated threshold-based cleanup of residual color screens (White/Green/Blue screens).
*   **Interactive Frame Editor:** An integrated post-processing editor equipped with Wand, Rect, Lasso, and Eraser tools to fine-tune individual frames and erase stray pixels.
*   **Game Engine Ready Formatting:** 
    *   **Stability Control:** Maintain original positioning to prevent jumping/jittering in idle animations.
    *   **Canvas Normalization:** Force uniform sprite sizes (e.g., 512x512) and padding, ensuring straightforward pivot assignment in Unity.

## 🛠️ Technology Stack

*   **Language:** Python
*   **UI Framework:** PyQt6
*   **Computer Vision / Image Processing:** OpenCV (`opencv-python`), Pillow (PIL), NumPy
*   **AI & Machine Learning:** `rembg`, ONNX Runtime

## 📦 Installation & Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/yourusername/AnimationEngine.git
    cd AnimationEngine
    ```

2.  **Create a Virtual Environment (Recommended):**
    ```bash
    python -m venv venv
    # Windows
    venv\Scripts\activate
    # macOS/Linux
    source venv/bin/activate
    ```

3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## 🚀 Usage

1.  Launch the application by running the main entry point:
    ```bash
    python src/main.py
    ```
2.  Navigate to the **Frame Extractor** tab.
3.  Load your input video (`.mp4`, `.avi`, `.mov`) or image file.
4.  Configure your desired Extraction Strategy, Resizing, and Quality/AI settings.
5.  Set your output folder and click **Start Processing**.
6.  Use the built-in **Animator Studio** and **Frame Editor** to make precise adjustments before taking the sprites to your game engine!

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue if you encounter any bugs or have feature suggestions.
