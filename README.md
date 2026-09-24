# Tafheem

A professional-grade AI-powered Arabic grammar analyzer featuring proof-based I'raab analysis, morphology breakdown (Sarf), Quranic corpus lookup, and intelligent practice question generation.

## Features

- **Nahw**: one tab, two distances on the same sentence:
  - *Tarkeeb*, the wide view; the bracket tree of how the words join, with 47 worked examples from Tasheel al-Nahw and a tree for any ayah
  - *I'raab*, the close-up; word-by-word case & function analysis with proof citations
- **Morphology (Sarf)**: Root extraction, verb patterns, conjugation tables
- **Quranic Lookup**: Full-text search across Qur'anic corpus with optional deep AI analysis
- **Memorise**: a printed mushaf page with words taken out, typed back or picked from four
- **Dictionary**: Bidirectional Arabic↔English search, built from the Wiktionary Arabic extract (Hans Wehr is under copyright and is not shipped)
- **Practice Questions**: AI-generated 4-question sets tailored to any sentence

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+ & npm

Optional, for the AI explanations only: a free [Groq API key](https://console.groq.com/keys),
or Ollama running locally. The app runs fully offline without either.

### Setup

1. **Clone/extract** the repository
2. **Configure API key**:
   ```bash
   # optional - the app runs offline with no .env at all
   # create one only to set GROQ_API_KEY or AI_BACKEND
   # Edit .env and paste your Groq API key (get free key from https://console.groq.com/keys)
   ```

3. **Install & run**:

   **Linux/macOS**:
   ```bash
   chmod +x start.sh
   ./start.sh
   ```

   **Windows** (PowerShell as admin):
   ```powershell
   python -m venv venv
   venv\Scripts\Activate
   pip install -r requirements.txt
   
   # In separate terminal (PowerShell)
   cd frontend
   npm install
   npm run dev

   # In first terminal (from the project root, NOT from backend/)
   python -m uvicorn backend.main:app --reload
   ```

4. Open **http://localhost:5173** in your browser

## API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `POST` | `/api/analyze` | I'raab sentence analysis |
| `GET` | `/api/tarkeeb/examples` | Worked tarkeeb trees from the books |
| `GET` | `/api/quran/{surah}/{ayah}/tarkeeb` | The tarkeeb tree of one ayah, derived from the corpus tags |
| `POST` | `/api/morphology` | Sarf word breakdown |
| `GET` | `/api/quran/{surah}/{ayah}` | Quranic verse lookup |
| `GET` | `/api/quran/search` | Quran search: Quran.com, falling back to the local index |
| `GET` | `/api/dictionary/search` | Arabic/English dictionary lookup |
| `POST` | `/api/practice` | Generate practice questions |
| `GET` | `/api/health` | Service status check |

See the endpoint table below for the available request and response shapes.

## Architecture

- **Backend**: FastAPI + Groq LLM + PyArabic morphology
- **Frontend**: React 19 + TanStack Query + Tailwind CSS + Vite
- **Data**: Quranic corpus (SQLite), Wiktionary-built dictionary (JSON), grammar rules database

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `GROQ_API_KEY not set` | Check .env file and restart backend after changing |
| `Ayah not found` | Verify surah (1-114) and ayah numbers are correct |
| `Analysis timeout` | LLM request timed out; try again (retry logic built-in) |
| `Empty dictionary` | Ensure `backend/data/arabic_dictionary.json` exists; build it with `python backend/scripts/build_dictionary.py` |

## Project Structure

```
tafheem/
├── backend/              # FastAPI server
│   ├── main.py             # Entry point
│   ├── config.py           # Settings & validation
│   ├── services/           # Business logic (Groq, corpus, dictionary)
│   ├── routers/            # API endpoints
│   ├── models/             # Pydantic schemas
│   └── data/               # Rules, corpus
├── frontend/            # React app
│   ├── src/
│   │   ├── App.jsx         # Main container
│   │   ├── components/     # UI components
│   │   ├── api.js          # HTTP client
│   │   └── grammarRoles.js # Role-to-class helper
│   └── package.json
├── requirements.txt     # Python dependencies
```

## Development Notes

- **Async**: All API endpoints use async/await with proper retry logic
- **Logging**: Structured logging to file (`backend.log`) and console
- **Type Safety**: Pydantic models for full request/response validation
- **Error Handling**: User-friendly error messages with actionable hints
- **State Management**: TanStack Query for efficient server state caching

## Known Limitations

- The dictionary holds what the Wiktionary extract covers, which is less than a printed lexicon
- Deep Quranic analysis uses same LLM as regular analysis (no special weighting)

## Contributing

To extend this tool:
1. Add new routers in `backend/routers/`
2. Create services in `backend/services/`
3. Add React components in `frontend/src/components/`
4. Update `package.json` or `requirements.txt` for dependencies

## License

This project uses educational data and free APIs. Please respect copyright and usage terms for all external resources.

---

**Questions?** Check backend logs with: `tail -f backend.log`
