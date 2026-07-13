# Fazrouter Documentation

## Quick Start

```bash
git clone https://github.com/chuyoriko/fazrouter.git
cd fazrouter
pip install -r requirements.txt
python router.py
# Server: http://localhost:8888
# Docs:   http://localhost:8888/docs
```

## Providers

Switch provider with `?provider=`. Default: `hianime`.

| Provider | Type | Quality |
|---|---|---|
| `hianime` | Anime | m3u8/HLS (1080p) |
| `animepahe` | Anime | m3u8/HLS (1080p) |
| `nanimeid` | Anime | Direct MP4 (1080p) |
| `anoboy` | Anime | Blogger embed |
| `maid` | Manga | imgbox CDN images |
| `komikpedia` | Manga | komiku CDN images |

## API Reference

### `GET /`

Root endpoint — returns provider list and version.

```bash
curl http://localhost:8888/
```

**Response:**
```json
{
  "service": "Fazrouter",
  "version": "2.1.0",
  "providers": {
    "anime": ["hianime", "animepahe", "nanimeid", "anoboy"],
    "manga": ["maid", "komikpedia"]
  }
}
```

---

### `GET /search`

Search anime or manga.

```bash
curl "http://localhost:8888/search?q=one+piece&provider=hianime"
curl "http://localhost:8888/search?q=one+piece&provider=nanimeid"
curl "http://localhost:8888/search?q=one+piece&provider=maid"
```

**Response:**
```json
{
  "success": true,
  "query": "one piece",
  "results": [
    {
      "id": "one-piece",
      "title": "One Piece",
      "url": "https://...",
      "image": "https://..."
    }
  ]
}
```

---

### `GET /home`

Latest releases homepage.

```bash
curl "http://localhost:8888/home?provider=nanimeid"
```

**Response (nanimeid):**
```json
{
  "success": true,
  "latest": [
    {
      "id": 399,
      "title": "5-toubun no Hanayome",
      "image": "https://...",
      "genres": ["Romance", "Harem"],
      "status": "Completed",
      "last_episode": 12
    }
  ],
  "total": 2083
}
```

---

### `GET /anime/{slug}`

Anime detail — includes episode list.

```bash
# HiAnime/AnimePahe — use slug
curl "http://localhost:8888/anime/one-piece?provider=hianime"

# NanimeID — use numeric ID
curl "http://localhost:8888/anime/399?provider=nanimeid"
```

**Response (nanimeid):**
```json
{
  "success": true,
  "data": {
    "id": 399,
    "title": "5-toubun no Hanayome",
    "genres": ["Romance", "Harem", "Comedy"],
    "status": "Completed",
    "rating": "7.6",
    "synopsis": "Fuutarou Uesugi adalah siswa SMA yang...",
    "studio": ["Tezuka Productions"],
    "total_episodes": 12,
    "episodes": [
      {
        "number": 1,
        "title": "Lima Serangkai yang Sempurna",
        "thumbnail": "https://cdn...",
        "duration": 1446,
        "views": 709,
        "qualities": [
          {"quality": "360p", "url": "https://cdn.../360p.mp4"},
          {"quality": "480p", "url": "https://cdn.../480p.mp4"},
          {"quality": "720p", "url": "https://cdn.../720p.mp4"},
          {"quality": "1080p", "url": "https://cdn.../1080p.mp4"}
        ]
      }
    ]
  }
}
```

---

### `GET /watch/{slug}/{ep}`

Get streaming sources for a specific episode.

```bash
# NanimeID — numeric ID + episode number
curl "http://localhost:8888/watch/399/1?provider=nanimeid"

# HiAnime — slug + episode
curl "http://localhost:8888/watch/one-piece/ep-1?provider=hianime"
```

**Response (nanimeid):**
```json
{
  "success": true,
  "data": {
    "number": 1,
    "title": "Lima Serangkai yang Sempurna",
    "duration": 1446,
    "qualities": [
      {"quality": "1080p", "url": "https://cdn.../1080p.mp4"},
      {"quality": "720p", "url": "https://cdn.../720p.mp4"}
    ],
    "prev_episode": null,
    "next_episode": {"nomor_episode": 2, "judul_episode": "Pengakuan Di Atap"},
    "total_episodes": 12
  }
}
```

---

### `GET /manga/{slug}`

Manga detail with chapter list.

```bash
curl "http://localhost:8888/manga/one-piece?provider=maid"
curl "http://localhost:8888/manga/komik-one-piece-indo?provider=komikpedia"
```

---

### `GET /chapter/{slug}/{ch}`

Read manga chapter — returns page image URLs.

```bash
curl "http://localhost:8888/chapter/one-piece/one-piece-chapter-1162-bahasa-indonesia?provider=maid"
```

**Response:**
```json
{
  "success": true,
  "data": {
    "title": "One Piece Chapter 1162",
    "images": [
      "https://images2.imgbox.com/98/fe/A8cp9QiC_o.jpg",
      "https://images2.imgbox.com/5e/cb/hWN0GkvF_o.jpg"
    ]
  }
}
```

---

### `GET /popular`

Popular anime listing.

```bash
curl "http://localhost:8888/popular?provider=hianime&page=1"
curl "http://localhost:8888/anime-list?provider=nanimeid&page=1"
```

---

### `GET /movie`

Movie catalog.

```bash
curl "http://localhost:8888/movie?provider=hianime"
```

---

### `GET /genre/{name}`

Browse by genre.

```bash
curl "http://localhost:8888/genre/isekai?provider=hianime"
```

---

### `GET /stream/{videoid}`

Direct stream ID lookup (HiAnime only).

```bash
curl "http://localhost:8888/stream/37086faf8067c880?provider=hianime"
```

---

## Provider Notes

### NanimeID
- Uses **numeric anime IDs**, not slugs. Get IDs from `/search`.
- Returns **direct MP4 URLs** — no m3u8/HLS, no embed.
- Quality: 360p, 480p, 720p, 1080p.
- Includes episode thumbnails, duration, views, prev/next navigation.

### HiAnime
- Returns **m3u8/HLS master playlists** with quality tiers.
- Servers: HSUB/SUB/DUB tabs with multiple mirrors.
- Direct video IDs supported via `/stream/{videoid}`.

### AnimePahe
- Returns **m3u8/HLS** from vidmoly CDN (first server auto-fetched).
- Also returns base64-encoded embed URLs for all servers.
- Quality: 1080p, 480p.

### Anoboy
- Returns **Blogger Video** embed player URL.
- Also decodes base64 mirror selectors.
- Quality varies by upload.

### Maid / KomikPedia
- Manga readers return **direct image URLs** from CDN.
- Maid: imgbox.com CDN.
- KomikPedia: komiku.org CDN (via EdgeOne proxy).

---

## Deployment

### Vercel
```bash
vercel --prod
```
Uses `vercel.json` — auto-detected.

### Railway
Push to GitHub → connect repo → auto-deploys with `railway.json`.

### Render
Push to GitHub → new Web Service → uses `render.yaml` for auto-config.

### Docker
```bash
docker build -t fazrouter .
docker run -p 8888:8888 fazrouter
```

### Manual VPS
```bash
pip install -r requirements.txt
python router.py &
```

---

## Testing

```bash
python test_all.py
# Output: TOTAL: 25/25 passed
```

---

## License

MIT — free to use, modify, distribute.

## Support

BTC: `bc1q5pkj6503rv5w80vndzf3a9h83x7xpj0va8gw3p`
ETH: `0xd1ce26cf239dcd90c31eaa8e08cb9027839a025e`
