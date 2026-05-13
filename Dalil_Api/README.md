# Dalil AI — Backend Engine

> Intelligent Business Data Analysis Chatbot for [Tafseela](https://tafseela.com) SaaS Platform

Dalil AI analyzes uploaded CSV/Excel business data and answers questions using **Gemini 2.5 Flash**.

---

## Quick Start

### 1. Clone & Setup

```bash
cd Dalil_Api
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac
pip install -r requirements.txt
```

### 2. Configure API Key

```bash
# Copy the environment template
cp .env.example .env

# Edit .env and add your Gemini API key
# Get your key from: https://aistudio.google.com/
```

**In your `.env` file:**
```
GOOGLE_API_KEY=AIzaSy...your_actual_key_here
API_SECRET_KEY=generate_a_random_secret_for_auth
```

### 3. Run the Server

```bash
uvicorn app.main:app --reload --port 8000
```

### 4. Open API Docs

Visit: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/ready` | Readiness check |
| `POST` | `/api/files/upload` | Upload CSV/Excel file |
| `POST` | `/api/chat/` | Chat with Dalil AI |
| `GET` | `/api/datasets/` | List all datasets |
| `GET` | `/api/datasets/{id}` | Get dataset details |
| `DELETE` | `/api/datasets/{id}` | Delete a dataset |

**All `/api/*` endpoints require the `X-API-Key` header.**

---

## Usage Example

### Step 1: Upload a file
```bash
curl -X POST http://localhost:8000/api/files/upload \
  -H "X-API-Key: your_secret_key" \
  -F "file=@sales_data.csv"
```

Response:
```json
{
  "dataset_id": "abc-123-def",
  "filename": "sales_data.csv",
  "rows": 10000,
  "columns": 8,
  "column_names": ["product", "sales", "date", ...]
}
```

### Step 2: Ask a question
```bash
curl -X POST http://localhost:8000/api/chat/ \
  -H "X-API-Key: your_secret_key" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What are the top 5 products by total sales?",
    "dataset_id": "abc-123-def"
  }'
```

---

## Project Structure

```
Dalil_Api/
├── app/
│   ├── main.py              # FastAPI entry point
│   ├── config/              # Settings & logging
│   ├── routers/             # API endpoints
│   ├── services/            # Business logic
│   ├── middleware/           # Auth, rate limiting, errors
│   ├── ai/                  # AI engine
│   │   ├── gemini_client.py # Gemini API wrapper
│   │   ├── pipeline.py      # Processing pipeline
│   │   ├── code_executor.py # Sandboxed execution
│   │   ├── prompts/         # Prompt templates
│   │   ├── context/         # Memory & summarization
│   │   └── tools/           # Analysis tools
│   ├── data/                # Data processing
│   ├── db/                  # Database layer
│   ├── schemas/             # Pydantic models
│   └── utils/               # Utilities
├── tests/                   # Test suite
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

---

## Architecture

**Agentic Code-Generation Pattern:**
1. User asks a question
2. Dalil AI receives schema metadata + sample rows (NOT full data)
3. Gemini generates Python/Pandas code to answer the question
4. Code is executed in a sandboxed environment against the actual data
5. Results are formatted and returned

This approach is superior to RAG for tabular data because it preserves table structure and handles aggregations accurately.

---

## Docker Deployment

```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f app

# Stop
docker-compose down
```

---

## Running Tests

```bash
pytest tests/ -v
```

---

## Security Notes

- **NEVER** commit `.env` to git
- API key auth on all endpoints
- Sandboxed code execution (no file/network access)
- CSV injection protection
- File upload validation (type, size)
- Rate limiting per IP

---

## License

Proprietary — Tafseela © 2025
