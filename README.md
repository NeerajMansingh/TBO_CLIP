# VibeTravel 🌍✈️

> Upload your travel inspiration photo. Get an affordable destination that matches the vibe.

## What It Does

1. User uploads a travel inspiration photo (Santorini, Bali, etc.)
2. CLIP visual AI matches it to one of 30 Indian/budget destinations
3. Budget filtering ensures prices fit within the user's range
4. Gemini AI opens a conversation to refine the choice
5. User chats to adjust preferences; the app re-searches dynamically
6. Final booking card shows 3 hotel options + "Book on TBO" button

## Tech Stack

| Layer | Technology |
|---|---|
| Visual matching | CLIP (clip-ViT-B-32 via sentence-transformers) |
| Vector database | ChromaDB (local, no external service) |
| Conversation AI | Gemini 1.5 Flash |
| Backend | FastAPI (Python) |
| Frontend | React + Vite + Tailwind CSS |
| TBO data | fake_tbo.py (hardcoded realistic data) |

---

## One-Time Setup

### 1. Backend

```bash
cd backend/
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Set your Gemini API key

Edit `backend/.env`:
```
GEMINI_API_KEY=your_actual_key_here
```

Get a free key at: https://aistudio.google.com/app/apikey

### 3. Generate destination photos

```bash
cd backend/
# Optional: set UNSPLASH_ACCESS_KEY=your_key for real photos
python download_destination_photos.py
```

Without an Unsplash key, colored placeholder images are generated automatically.

### 4. Generate CLIP embeddings (run once)

```bash
cd backend/
python generate_embeddings.py
```

This creates `destination_embeddings.json`. Takes ~2-3 minutes on first run (downloads CLIP model).

### 5. Load embeddings into ChromaDB (run once)

```bash
cd backend/
python load_chromadb.py
```

Creates `chroma_store/` folder. Prints a test query result to confirm it worked.

---

## Running the App

### Start the backend

```bash
cd backend/
source venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Check it's running: http://localhost:8000/health

### Start the frontend

```bash
cd frontend/
npm install   # first time only
npm run dev
```

Open: http://localhost:5173

---

## Demo Script (60 seconds)

1. Open http://localhost:5173 — Upload Screen appears
2. Drag & drop a Santorini photo into the upload zone
3. Enter budget: **₹40,000** → dates: Nov 15–22 → click **Find My Match**
4. Loading screen shows 3 animated steps (CLIP → ChromaDB → TBO)
5. Match appears: **Pondicherry**, ₹14,000/person, reasons: coastal · whitewashed architecture · romantic
6. AI: *"Your photo has a quiet romantic coastal feel. Is the beach the priority or the old-town atmosphere?"*
7. Type: **"I want something more mountainous"**
8. Left panel smoothly updates → Coorg or Manali
9. Type: **"This looks perfect!"**
10. Booking screen: 3 hotel cards + **Book on TBO** button

---

## Adding Real TBO API Later

Only one file changes: replace `get_tbo_data()` in `backend/fake_tbo.py`.  
The function signature stays identical — the rest of the codebase is unchanged.

---

## Project Structure

```
vibetravel/
├── backend/
│   ├── main.py                  # FastAPI: /match /chat /confirm /health
│   ├── clip_utils.py            # CLIP embeddings + zero-shot vibe tags
│   ├── chromadb_utils.py        # Vector similarity search
│   ├── gemini_utils.py          # Gemini conversation + match explanation
│   ├── fake_tbo.py              # 30 destinations, realistic fake prices
│   ├── session_store.py         # In-memory session state
│   ├── generate_embeddings.py   # One-time: generate CLIP embeddings
│   ├── load_chromadb.py         # One-time: load embeddings into ChromaDB
│   └── download_destination_photos.py  # One-time: download/generate photos
└── frontend/
    └── src/
        ├── App.jsx              # Screen router + API calls
        ├── screens/             # UploadScreen, LoadingScreen, MatchChatScreen, BookingScreen
        └── components/          # ChatWindow, DestinationPanel, HotelCard
```
