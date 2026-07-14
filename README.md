# Fazrouter — Unified Anime, Manga & Movie API Router

A single REST API that unifies scraping from 8 different content providers into one consistent interface. Switch providers with `?provider=`.

---

## Providers (8)

| Provider | Type | Search | Detail | Stream |
|---|---|---|---|---|
| HiAnime | Anime | ok | ok | m3u8/HLS 1080p |
| AnimePahe | Anime | ok | ok | m3u8/HLS 1080p |
| NanimeID | Anime | ok | ok | Direct MP4 1080p |
| Anoboy | Anime | ok | ok | Embed 720p |
| AllAnime | Anime | ok | ok | GraphQL + AES |
| YesMovies | Movie/TV | ok | ok | Embed HD |
| Maid | Manga | ok | ok | imgbox CDN |
| Komikpedia | Manga | ok | ok | komiku CDN |

---

## Quick Start

```
git clone https://github.com/chuyoriko/fazrouter.git
cd fazrouter
pip install -r requirements.txt
python router.py
```
Server: http://localhost:8888 | Docs: http://localhost:8888/docs

---

## API Endpoints

```
GET  /search?q=&provider=           Search (all providers)
GET  /home?provider=                Latest releases
GET  /anime/{slug}?provider=        Detail (anime/movie/tv)
GET  /manga/{slug}?provider=        Manga detail
GET  /watch/{slug}/{ep}?provider=   Stream sources + embed URL
GET  /chapter/{slug}/{ch}?provider= Manga chapter images
GET  /servers/{slug}/{ep}?provider= Server list
GET  /stream/{videoid}?provider=    Direct m3u8 lookup
GET  /popular?provider=&page=       Popular list
GET  /movie?provider=&page=         Movie list
GET  /tvshows?provider=&page=       TV show list
GET  /genre/{name}?provider=        Browse by genre
GET  /new-season?provider=          New season (animepahe only)
```

---

## Architecture

```
fazrouter/
  router.py                 FastAPI v2.1.0
  hianime_api_internal.py   HiAnime (async)
  animepahe.py              AnimePahe
  nanimeid.py               NanimeID
  anoboy.py                 Anoboy
  allanime.py               AllAnime (GraphQL + AES)
  yesmovies.py              YesMovies (Dooplay + SuperEmbed)
  maid.py                   Maid Manga
  komikpedia.py             KomikPedia
  requirements.txt
  test_all.py
```

---

## Deploy

Vercel, Railway, Render, Docker configs included.

```
pip install -r requirements.txt
python router.py
```

---

## Requirements

Python 3.10+, fastapi, uvicorn, httpx, beautifulsoup4, lxml, pycryptodome

---

## Support

| Coin | Address |
|---|---|
| BTC | bc1q5pkj6503rv5w80vndzf3a9h83x7xpj0va8gw3p |
| ETH | 0xd1ce26cf239dcd90c31eaa8e08cb9027839a025e |
| LTC | ltc1q2p4tdtu3cy0aktvxeg9jcesjsszpccdgyj5s0s |
| USDT | TP4fVW3V9YzrP6DftnTLKZE7tSraWu9wxM |

---

## License

MIT
