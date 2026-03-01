# VisionVoyage ✈️📸

VisionVoyage is an AI-powered travel discovery app. Simply upload an aesthetic travel photo you love, and our AI (CLIP embeddings + ChromaDB) will match the visual vibe to a verified destination in India!

We then use the **TBO API** to find real-time hotel availability at your destination, and **Google Gemini** to chat with you about the location and help you curate and book your perfect stay.

---

## 🚀 Setting Up From Scratch

This guide assumes you are starting with a brand-new laptop and have **nothing** installed yet. Don't worry, we'll walk you through step-by-step.

### Step 1: Install Required Software (Prerequisites)

Before you can run this app, your computer needs to understand Python (for the backend) and JavaScript/Node (for the frontend).

1. **Install Python 3.10+**
   - Download the installer from the [official Python website](https://www.python.org/downloads/).
   - **CRITICAL (Windows users):** During installation, you MUST check the box that says `"Add Python to PATH"` at the very bottom of the first screen.

2. **Install Node.js (for the frontend)**
   - Download the "LTS" (Long Term Support) version from the [official Node.js website](https://nodejs.org/).
   - Run the installer and click "Next" through the default options.

3. **Install Git (Optional but Recommended)**
   - If you need to clone this code from GitHub, install Git from [git-scm.com](https://git-scm.com/downloads).

---

### Step 2: Set Up the Backend (Python)

The backend handles the AI image matching and connects to the TBO Hotel API & Gemini LLMs.

1. **Open your terminal** (Command Prompt on Windows, Terminal on Mac/Linux) and navigate to the project backend folder:
   ```bash
   cd path/to/VisionVoyage/backend
   ```

2. **Create a Virtual Environment** (This keeps all your Python packages organized in one folder):
   ```bash
   # On Mac/Linux:
   python3 -m venv venv
   
   # On Windows:
   python -m venv venv
   ```

3. **Activate the Virtual Environment**:
   ```bash
   # On Mac/Linux:
   source venv/bin/activate
   
   # On Windows (Command Prompt):
   venv\Scripts\activate.bat
   
   # On Windows (PowerShell):
   venv\Scripts\Activate.ps1
   ```
   *(You should now see `(venv)` at the beginning of your terminal line).*

4. **Install the Required Packages**:
   The backend relies on FastAPI, ChromaDB, Sentence-Transformers (for CLIP), and Gemini.
   ```bash
   pip install -r requirements.txt
   ```
   *(This might take a few minutes as it downloads large AI libraries like PyTorch and CLIP).*

5. **Set Up the Destination Images**:
   For the AI to match images correctly, the backend must have a library of reference images.
   - Ensure the `backend/destinations/` folder is populated with subfolders of destinations (e.g., `goa`, `manali`).
   - Each folder should contain images like `1.jpg`, `2.jpg`, etc.
   - If this folder is missing, run one of the provided download scripts (e.g., `python download_diverse_photos_20.py`) to generate sample imagery.

6. **Configure API Keys (`.env` file)**:
   - Inside the `backend/` folder, create a new file named exactly `.env` (don't forget the dot).
   - Add your API details inside:
     ```env
     GEMINI_API_KEY=your_google_gemini_api_key_here
     
     # TBO API Credentials (Optional - app will intelligently invoke fake_tbo as a fallback if omitted)
     TBO_API_USER=YourUsername
     TBO_API_PASSWORD=YourPassword
     TBO_B2B_USER=YourUsername
     TBO_B2B_PASSWORD=YourPassword
     ```

7. **Initialize the AI Brain**:
   Before running the app for the very first time, you must process the destination photos into AI numerics (embeddings) and load them into Chroma DB. **Run these once**:
   ```bash
   python generate_embeddings.py
   python load_chromadb.py
   ```

8. **Start the Backend Server**:
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```
   *Leave this terminal window open!*

---

### Step 3: Set Up the Frontend (React / Vite)

The frontend is the React-based user interface connected to the backend APIs.

1. **Open a SECOND, NEW terminal window** (leave the backend running in the first one).
2. Navigate to the frontend folder:
   ```bash
   cd path/to/VisionVoyage/frontend
   ```

3. **Install JavaScript Dependencies**:
   The frontend utilizes React, Framer Motion, TailwindCSS, and Lucide React.
   ```bash
   npm install
   ```

4. **Start the Frontend Server**:
   ```bash
   npm run dev
   ```

5. **Open the App**:
   The terminal will print a local web address (usually `http://localhost:5173/`).
   **Hold CTRL (or CMD on Mac) and click the link**, or copy-paste it into your web browser.

---

### 🎉 You're Done!
You should now see the VisionVoyage upload screen. Upload an aesthetic landscape photo, adjust your constraints like Budget and Duration, and let the AI find your perfect match!

### Troubleshooting

- **"Command not found: python"**: Try typing `python3` instead of `python`. If that fails, Python was not installed correctly or not added to your system PATH.
- **"npm is not recognized"**: You need to install Node.js (see Step 1), or you forgot to restart your terminal after installing Node.js.
- **"No such file or directory: 'destinations'"**: You skipped setting up the destination images folder. AI needs images to analyze visual similarity!
- **App matches perfectly but chat crashes**: Ensure your `.env` file exists in the backend folder and contains a valid `GEMINI_API_KEY`.
