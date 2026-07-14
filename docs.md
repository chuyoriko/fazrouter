# Fazrouter API Documentation

Unified REST API for anime, manga, movies & TV from 8 content providers.
Base URL: `http://localhost:8888` | Swagger UI: `http://localhost:8888/docs`

---

## Quick Start

```
git clone https://github.com/chuyoriko/fazrouter.git
cd fazrouter
pip install -r requirements.txt
python router.py
```

All endpoints accept `?provider=` (default: `hianime`). Response format:

```json
{ "success": true, "results": [...] }
{ "success": true, "data": {...} }
```

---

## Providers

| Key | Type | Search | Detail | Stream | Notes |
|---|---|---|---|---|---|
| `hianime` | Anime | ok | ok | m3u8/HLS 1080p | Default, async |
| `animepahe` | Anime | ok | ok | m3u8/HLS 1080p | Vidmoly CDN |
| `nanimeid` | Anime | ok | ok | Direct MP4 1080p | Numeric IDs |
| `anoboy` | Anime | ok | ok | Embed 720p | WordPress AJAX |
| `allanime` | Anime | ok | ok | m3u8/HLS 1080p | GraphQL + AES |
| `yesmovies` | Movie/TV | ok | ok | Embed HD | SuperEmbed API |
| `maid` | Manga | ok | ok | imgbox CDN | Direct images |
| `komikpedia` | Manga | ok | ok | komiku CDN | Direct images |

---

## GET /

```bash
curl http://localhost:8888/
```

```json
{
  "service": "Fazrouter",
  "version": "2.1.0",
  "providers": {
    "anime": ["hianime", "animepahe", "nanimeid", "anoboy", "allanime"],
    "manga": ["maid", "komikpedia"],
    "movies": ["yesmovies"]
  }
}
```

---

## GET /search

| Param | Required | Default |
|---|---|---|
| `q` | Yes | — |
| `provider` | No | hianime |
| `page` | No | 1 |

```bash
# Anime
curl "http://localhost:8888/search?q=naruto&provider=hianime"
curl "http://localhost:8888/search?q=naruto&provider=allanime"
curl "http://localhost:8888/search?q=naruto&provider=nanimeid"

# Movie/TV
curl "http://localhost:8888/search?q=avengers&provider=yesmovies"

# Manga
curl "http://localhost:8888/search?q=one+piece&provider=maid"
```

**Response (yesmovies):**
```json
{
  "success": true,
  "query": "avengers",
  "results": [
    {
      "id": "avengers-endgame",
      "title": "Avengers: Endgame",
      "type": "movie",
      "image": "https://image.tmdb.org/t/p/w92/or06...",
      "url": "https://ww.yesmovies123.me/movies/avengers-endgame/",
      "date": "2019",
      "rating": "8.4"
    }
  ]
}
```

---

## GET /home

```bash
curl "http://localhost:8888/home?provider=hianime"
curl "http://localhost:8888/home?provider=yesmovies"
```

**Response (yesmovies):**
```json
{
  "success": true,
  "movies": [
    {
      "id": "toy-story-5",
      "title": "Toy Story 5",
      "type": "movie",
      "url": "https://...",
      "image": "https://image.tmdb.org/...",
      "rating": "",
      "date": "Jun. 17, 2026"
    }
  ],
  "tvshows": [
    {
      "id": "smoking-behind-the-supermarket-with-you",
      "title": "Smoking Behind the Supermarket with You",
      "type": "tv",
      "rating": "10",
      "date": "Jul. 09, 2026"
    }
  ]
}
```

---

## GET /anime/{slug}

Works for anime, movies, and TV shows. For yesmovies, auto-detects movie vs TV.

```bash
# Anime
curl "http://localhost:8888/anime/solo-leveling?provider=hianime"
curl "http://localhost:8888/anime/399?provider=nanimeid"
curl "http://localhost:8888/anime/solo-leveling?provider=allanime"

# Movie
curl "http://localhost:8888/anime/toy-story-5?provider=yesmovies"

# TV Show
curl "http://localhost:8888/anime/smoking-behind-the-supermarket-with-you?provider=yesmovies"
```

**Response (yesmovies - movie):**
```json
{
  "success": true,
  "data": {
    "slug": "toy-story-5",
    "title": "Toy Story 5",
    "poster": "https://image.tmdb.org/t/p/w185/gaiMtK2...",
    "description": "When Bonnie receives a Lilypad tablet...",
    "genres": ["Adventure", "Animation", "Comedy", "Family"],
    "rating": "0",
    "releaseDate": "Jun. 17, 2026",
    "year": "2026",
    "country": "USA",
    "rated": "NR",
    "servers": [
      {
        "name": "Watch Toy Story 5 Full Movie Online",
        "post": "vs",
        "nume": "vs",
        "type": "movie",
        "vs_url": "https://w28.yesmovies123.me/se_player.php?video_id=tt29355505"
      }
    ],
    "cast": [
      { "name": "Tom Hanks", "character": "Woody (voice)", "image": "https://..." }
    ],
    "type": "movie"
  }
}
```

**Response (yesmovies - TV):**
```json
{
  "success": true,
  "data": {
    "slug": "smoking-behind-the-supermarket-with-you",
    "title": "Smoking Behind the Supermarket with You",
    "poster": "https://image.tmdb.org/...",
    "description": "Meet Sasaki, an overworked...",
    "genres": ["Animation", "Comedy", "Drama"],
    "rating": "10",
    "date": "Jul. 09, 2026",
    "seasons": [
      {
        "name": "Season 1 Jul. 09, 2026",
        "episodes": [
          {
            "id": "smoking-behind-the-supermarket-with-you-1x1",
            "number": "1",
            "title": "Episode 1"
          }
        ]
      }
    ],
    "cast": [...],
    "type": "tv"
  }
}
```

---

## GET /watch/{slug}/{ep}

Get streaming sources. For yesmovies, the `{ep}` parameter is the server nume (usually `"vs"` for the default server).

```bash
# Anime
curl "http://localhost:8888/watch/solo-leveling/1?provider=hianime"
curl "http://localhost:8888/watch/399/1?provider=nanimeid"
curl "http://localhost:8888/watch/solo-leveling/1?provider=allanime"

# Movie
curl "http://localhost:8888/watch/toy-story-5/vs?provider=yesmovies"
```

**Response (anime - HiAnime):**
```json
{
  "success": true,
  "data": {
    "number": 1,
    "title": "Episode 1",
    "qualities": [
      { "quality": "1080p", "url": "https://.../master.m3u8" },
      { "quality": "720p", "url": "https://.../720p.m3u8" }
    ],
    "servers": [{ "name": "Server 1", "url": "https://..." }]
  }
}
```

**Response (anime - NanimeID):**
```json
{
  "success": true,
  "data": {
    "number": 1,
    "title": "Episode 1",
    "duration": 1446,
    "qualities": [
      { "quality": "1080p", "url": "https://.../1080p.mp4" },
      { "quality": "720p", "url": "https://.../720p.mp4" }
    ],
    "prev_episode": null,
    "next_episode": { "nomor_episode": 2, "judul_episode": "..." }
  }
}
```

**Response (yesmovies):**
```json
{
  "success": true,
  "data": {
    "title": "Toy Story 5",
    "slug": "toy-story-5",
    "streamUrl": "https://w28.yesmovies123.me/se_player.php?video_id=tt29355505",
    "embedUrl": "https://streamingnow.mov/?play=...",
    "videoId": "tt29355505",
    "servers": [
      {
        "name": "Watch Toy Story 5 Full Movie Online",
        "post": "vs",
        "nume": "vs",
        "type": "movie",
        "vs_url": "https://w28.yesmovies123.me/se_player.php?video_id=tt29355505"
      }
    ],
    "type": "movie"
  }
}
```

**YesMovies watch fields:**

| Field | Description |
|---|---|
| `streamUrl` | Raw `se_player.php` URL |
| `embedUrl` | Resolved via `getsuperembed.link` API — use in `<iframe>` for browser playback |
| `videoId` | IMDb ID (e.g. `tt29355505`) |

---

## GET /manga/{slug}

```bash
curl "http://localhost:8888/manga/one-piece?provider=maid"
curl "http://localhost:8888/manga/one-piece?provider=komikpedia"
```

```json
{
  "success": true,
  "data": {
    "id": "one-piece",
    "title": "One Piece",
    "image": "https://...",
    "author": "Eiichiro Oda",
    "status": "Ongoing",
    "chapters": [
      { "id": "one-piece-1162", "title": "Chapter 1162" }
    ]
  }
}
```

---

## GET /chapter/{slug}/{ch}

Read manga — returns direct image URLs from CDN.

```bash
curl "http://localhost:8888/chapter/one-piece/one-piece-chapter-1162?provider=maid"
```

```json
{
  "success": true,
  "data": {
    "title": "One Piece Chapter 1162",
    "images": [
      "https://images2.imgbox.com/98/fe/abc123.jpg",
      "https://images2.imgbox.com/5e/cb/def456.jpg"
    ]
  }
}
```

---

## GET /servers/{slug}/{ep}

Server list only (no stream URLs).

```bash
curl "http://localhost:8888/servers/solo-leveling/1?provider=hianime"
curl "http://localhost:8888/servers/solo-leveling/1?provider=allanime"
```

---

## GET /stream/{videoid}

Direct stream URL from video ID. **HiAnime only.**

```bash
curl "http://localhost:8888/stream/37086faf8067c880?provider=hianime"
```

---

## GET /popular

Popular/trending content.

```bash
curl "http://localhost:8888/popular?provider=hianime&page=1"
curl "http://localhost:8888/popular?provider=allanime&page=1"
curl "http://localhost:8888/popular?provider=yesmovies&page=1"
```

---

## GET /movie

Movie catalog.

```bash
# Anime movies
curl "http://localhost:8888/movie?provider=hianime&page=1"
curl "http://localhost:8888/movie?provider=allanime&page=1"

# Live-action
curl "http://localhost:8888/movie?provider=yesmovies&page=1"
```

**Response (yesmovies):**
```json
{
  "success": true,
  "page": 1,
  "results": [
    {
      "id": "toy-story-5",
      "title": "Toy Story 5",
      "image": "https://image.tmdb.org/...",
      "rating": "",
      "date": "Jun. 17, 2026",
      "description": "When Bonnie receives...",
      "genres": ["Adventure", "Animation"]
    }
  ],
  "hasNext": true
}
```

---

## GET /tvshows

TV show listing. **YesMovies only.**

```bash
curl "http://localhost:8888/tvshows?provider=yesmovies&page=1"
```

```json
{
  "success": true,
  "page": 1,
  "results": [
    {
      "id": "smoking-behind-the-supermarket-with-you",
      "title": "Smoking Behind the Supermarket with You",
      "rating": "10",
      "genres": ["Animation", "Comedy", "Drama"]
    }
  ],
  "hasNext": true
}
```

---

## GET /genre/{name}

Browse by genre.

```bash
curl "http://localhost:8888/genre/action?provider=hianime&page=1"
curl "http://localhost:8888/genre/horror?provider=yesmovies&page=1"
```

```json
{
  "success": true,
  "genre": "action",
  "page": 1,
  "results": [
    { "id": "...", "title": "...", "image": "..." }
  ]
}
```

---

## GET /new-season

New season releases. **AnimePahe only.**

```bash
curl "http://localhost:8888/new-season?provider=animepahe&page=1"
```

---

## Provider Details

### HiAnime (`hianime`)
- Default async provider. Returns m3u8/HLS.
- Multi-server: HSUB, SUB, DUB tabs.

### AnimePahe (`animepahe`)
- HTML scraping, vidmoly CDN. m3u8/HLS output.
- Base64-encoded embed URLs for all servers.

### NanimeID (`nanimeid`)
- **Numeric IDs only** (get from `/search`).
- Returns **direct MP4 URLs** — 360p/480p/720p/1080p.
- Includes episode thumbnail, duration, prev/next nav.

### Anoboy (`anoboy`)
- WordPress AJAX search. Blogger Video embed streams.
- Base64 mirror selectors.

### AllAnime (`allanime`)
- **GraphQL API** with persisted query hashes.
- **AES-256-CTR decryption** for `tobeparsed` payloads.
- Multi-endpoint CDN fallback (Clock/APIak resolution).
- Both direct sources (HLS/MP4) and embed servers.
- Requires `pycryptodome` (`Crypto.Cipher.AES`).

### YesMovies (`yesmovies`)
- WordPress + Dooplay theme v2.3.3.
- Images from **TMDb** CDN. Genres via WP REST API.
- Player resolution: `getsuperembed.link` API → `streamingnow.mov`.
- Return `embedUrl` for iframe playback (Cloudflare Turnstile in browser).
- Auto-detects movie vs TV when using `/anime/{slug}`.

### Maid (`maid`)
- Direct imgbox.com CDN image URLs.

### KomikPedia (`komikpedia`)
- Komiku CDN (EdgeOne proxy).

---

## Errors

```json
{ "detail": "Error message" }
```

- `400` — Invalid param (non-numeric ID for nanimeid)
- `400` — Provider not available for endpoint
- `400` — Missing `q` param for search

---

## Requirements

```
fastapi>=0.115.0
uvicorn>=0.32.0
httpx>=0.28.0
beautifulsoup4>=4.12.0
lxml>=5.3.0
pycryptodome>=3.20.0
```

Python 3.10+.

---

## Deploy

Vercel, Railway, Render, Docker — config files included.

```bash
pip install -r requirements.txt
python router.py &
```

---

## Test

```bash
python test_all.py
```

---

## License

MIT
