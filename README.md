# 🎬 Anime & Manga Scraper API

Unified REST API router for scraping anime and manga from multiple Indonesian providers. One endpoint, switch providers with `?provider=`.

> ⚠️ **Disclaimer**: This project is for educational purposes only. No files are stored. All content is linked from third-party services.

---

## 📦 Supported Providers

| Provider | Type | Search | Detail | Stream/Read |
|---|---|---|---|---|
| **HiAnime** | Anime | ✅ | ✅ | ✅ m3u8/HLS |
| **AnimePahe** | Anime | ✅ | ✅ | ✅ embed URLs |
| **Maid** | Manga | ✅ | ✅ | ✅ 18 images/ch |
| **Komikpedia** | Manga | ✅ | ✅ | ✅ 16 images/ch |

---

## 🚀 Quick Start

```bash
# 1. Clone
git clone https://github.com/chuyoriko/fazrouter.git
cd fazrouter

# 2. Install Python deps
pip install -r requirements.txt

# 3. Run router
python router.py
# Server runs on http://localhost:8888
```

---

## 📡 API Usage

### Search
```bash
curl "http://localhost:8888/search?q=one+piece&provider=hianime"
curl "http://localhost:8888/search?q=one+piece&provider=animepahe"
curl "http://localhost:8888/search?q=one+piece&provider=maid"
curl "http://localhost:8888/search?q=one+piece&provider=komikpedia"
```

### Anime Detail
```bash
curl "http://localhost:8888/anime/one-piece?provider=hianime"
curl "http://localhost:8888/anime/one-piece?provider=animepahe"
```

### Watch (get streaming sources)
```bash
curl "http://localhost:8888/watch/one-piece/ep-1?provider=hianime"
# Returns: servers (HSUB/SUB/DUB) + m3u8 qualities (360p/720p/1080p)
```

### Manga Detail
```bash
curl "http://localhost:8888/manga/one-piece?provider=maid"
curl "http://localhost:8888/manga/one-piece?provider=komikpedia"
```

### Read Chapter
```bash
curl "http://localhost:8888/chapter/one-piece/one-piece-chapter-1162?provider=maid"
# Returns: list of direct image URLs
```

### Full Endpoint List

| Endpoint | HiAnime | AnimePahe | Maid | Komikpedia |
|---|---|---|---|---|
| `GET /search?q=` | ✅ | ✅ | ✅ | ✅ |
| `GET /home` | ✅ | ✅ | ✅ | ✅ |
| `GET /anime/{slug}` | ✅ | ✅ | - | - |
| `GET /manga/{slug}` | - | - | ✅ | ✅ |
| `GET /watch/{slug}/{ep}` | ✅ | ✅ | - | - |
| `GET /chapter/{slug}/{ch}` | - | - | ✅ | ✅ |
| `GET /stream/{videoid}` | ✅ | - | - | - |
| `GET /popular` | ✅ | ✅ | - | - |
| `GET /movie` | ✅ | ✅ | - | - |
| `GET /genre/{name}` | ✅ | ✅ | - | - |
| `GET /new-season` | - | ✅ | - | - |

---

## 🏗 Architecture

```
anime-manga-scraper/
├── router.py                 # FastAPI unified router
├── hianime_api_internal.py   # HiAnime scraper (async)
├── animepahe.py              # AnimePahe scraper (sync)
├── maid.py                   # Maid manga scraper
├── komikpedia.py             # Komikpedia manga scraper
├── requirements.txt          # Python dependencies
├── test_all.py               # Full test suite
├── vercel.json               # Vercel config
├── railway.json              # Railway config
├── render.yaml               # Render config
├── Dockerfile                # Docker config
└── README.md
```

---

## ☁️ Deploy

### Vercel (Free)

1. Push to GitHub
2. Go to [vercel.com](https://vercel.com) → New Project → Import your repo
3. Framework: **Other**
4. Build Command: (leave empty)
5. Output Directory: (leave empty)
6. Install Command: `pip install -r requirements.txt`
7. **Important**: Add file `vercel.json` (already included)

Vercel will run the API as a serverless function.

### Railway

1. Push to GitHub
2. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub
3. Railway auto-detects Python. It will use `railway.json` (included).

### Render

1. Push to GitHub
2. Go to [render.com](https://render.com) → New Web Service
3. Connect repo, set:
   - Runtime: Python 3
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python router.py`
4. Uses `render.yaml` (included) for auto-deploy.

### Docker

```bash
docker build -t anime-scraper .
docker run -p 8888:8888 anime-scraper
```

### Any VPS (Linode, DigitalOcean, etc.)

```bash
# Install Python 3.10+
apt install python3 python3-pip
pip install -r requirements.txt

# Run as service
nohup python router.py &
# OR with systemd (see systemd/anime-scraper.service)
```

---

## 🧪 Testing

```bash
python test_all.py
# Output:
# [PASS] hianime     /home          | latest=12
# [PASS] komikpedia  /read/chapter  | images=16
# ...
# TOTAL: 25/25 passed
```

---

## 📝 Requirements

- Python 3.10+
- `pip install -r requirements.txt`

All dependencies:
```
fastapi, uvicorn, httpx, beautifulsoup4, lxml
```

---

## 🔒 Security

- No API keys required
- No authentication needed
- All scraping is server-side
- No files stored — only links returned
- Use responsibly — respect rate limits

---

## 💰 Donate

Support this project via crypto:

| Coin | Address |
|---|---|
| **BTC** | `bc1q5pkj6503rv5w80vndzf3a9h83x7xpj0va8gw3p` |
| **ETH** | `0xd1ce26cf239dcd90c31eaa8e08cb9027839a025e` |
| **LTC** | `ltc1q2p4tdtu3cy0aktvxeg9jcesjsszpccdgyj5s0s` |
| **USDT (TRC20)** | `TP4fVW3V9YzrP6DftnTLKZE7tSraWu9wxM` |

---

## 📄 License

MIT License. See [LICENSE](LICENSE).

---

Built with ❤️ for the Indonesian anime/manga community.
ty.
