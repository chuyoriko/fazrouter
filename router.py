"""Fazrouter - Unified Anime & Manga API Router"""

import uvicorn
import asyncio
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Anime providers
from animepahe import (
    search as pahe_search, home as pahe_home, anime_list as pahe_list,
    anime_detail as pahe_detail, episode_watch as pahe_watch,
    movies as pahe_movies, popular as pahe_popular,
    genre as pahe_genre, new_season as pahe_new_season,
)
from hianime_api_internal import HiAnimeClient
import nanimeid as nani
import anoboy as ab

# Manga providers
import maid as maid_provider
import komikpedia as kp_provider

app = FastAPI(title="Fazrouter", version="2.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

hianime = HiAnimeClient()

@app.on_event("startup")
async def startup():
    await hianime.start()

@app.on_event("shutdown")
async def shutdown():
    await hianime.stop()


@app.get("/")
async def root():
    return {
        "service": "Fazrouter",
        "version": "2.1.0",
        "providers": {
            "anime": ["hianime", "animepahe", "nanimeid", "anoboy"],
            "manga": ["maid", "komikpedia"],
        },
        "docs": "/docs",
    }

# --- SEARCH ---
@app.get("/search")
async def search(q: str = Query(...), provider: str = Query("hianime"), page: int = Query(1, ge=1)):
    if provider == "animepahe": return pahe_search(q, page)
    if provider == "nanimeid": return nani.search(q)
    if provider == "anoboy": return ab.search(q)
    if provider == "maid": return maid_provider.search(q)
    if provider == "komikpedia": return kp_provider.search(q)
    return await hianime.search(q, page)

# --- HOME ---
@app.get("/home")
async def home(provider: str = Query("hianime")):
    if provider == "animepahe": return pahe_home()
    if provider == "nanimeid": return nani.home()
    if provider == "anoboy": return ab.home()
    if provider == "maid": return maid_provider.home()
    if provider == "komikpedia": return kp_provider.home()
    return await hianime.home()

# --- ANIME DETAIL ---
@app.get("/anime/{slug}")
async def anime_detail(slug: str, provider: str = Query("hianime")):
    if provider == "nanimeid":
        try:
            anime_id = int(slug)
            return nani.anime_detail(anime_id)
        except ValueError:
            raise HTTPException(400, "nanimeid requires numeric anime ID")
    if provider == "animepahe": return {"success": True, "data": pahe_detail(slug)}
    return await hianime.anime_detail(slug)

# --- MANGA DETAIL ---
@app.get("/manga/{slug}")
async def manga_detail(slug: str, provider: str = Query("maid")):
    if provider == "komikpedia": return {"success": True, "data": kp_provider.manga_detail(slug)}
    return {"success": True, "data": maid_provider.manga_detail(slug)}

# --- WATCH ---
@app.get("/watch/{slug}/{ep}")
async def watch(slug: str, ep: str, provider: str = Query("hianime")):
    if provider == "nanimeid":
        try:
            anime_id = int(slug)
            ep_num = int(ep)
            return nani.episode_watch(anime_id, ep_num)
        except ValueError:
            raise HTTPException(400, "nanimeid requires numeric anime ID and episode number")
    if provider == "animepahe": return {"success": True, "data": pahe_watch(slug)}
    if provider == "anoboy": return {"success": True, "data": ab.episode_watch(slug)}
    return await hianime.watch(slug, ep)

# --- READ CHAPTER ---
@app.get("/chapter/{slug}/{ch}")
async def chapter_read(slug: str, ch: str, provider: str = Query("maid")):
    if provider == "komikpedia": return {"success": True, "data": kp_provider.chapter_read(slug, ch)}
    return {"success": True, "data": maid_provider.chapter_read(ch)}

# --- SERVERS ---
@app.get("/servers/{slug}/{ep}")
async def servers(slug: str, ep: str, provider: str = Query("hianime")):
    if provider == "animepahe":
        data = pahe_watch(slug)
        return {"success": True, "servers": data["servers"]}
    return await hianime.servers(slug, ep)

# --- STREAM ---
@app.get("/stream/{videoid}")
async def stream(videoid: str, provider: str = Query("hianime")):
    if provider != "hianime":
        raise HTTPException(400, f"stream endpoint only available for hianime provider")
    return await hianime.stream(videoid)

# --- POPULAR/ANIME LIST ---
@app.get("/popular")
@app.get("/anime-list")
async def popular(provider: str = Query("hianime"), page: int = Query(1, ge=1)):
    if provider == "nanimeid": return nani.anime_list(page)
    if provider == "animepahe": return pahe_popular(page)
    return await hianime.popular(page)

# --- MOVIES ---
@app.get("/movie")
async def movies(provider: str = Query("hianime"), page: int = Query(1, ge=1)):
    if provider == "animepahe": return pahe_movies(page)
    return await hianime.movies(page)

# --- GENRE ---
@app.get("/genre/{genre}")
async def genre(genre: str, provider: str = Query("hianime"), page: int = Query(1, ge=1)):
    if provider == "animepahe": return pahe_genre(genre, page)
    return await hianime.genre(genre, page)

# --- NEW SEASON ---
@app.get("/new-season")
async def new_season(provider: str = Query("hianime"), page: int = Query(1, ge=1)):
    if provider == "animepahe": return pahe_new_season(page)
    raise HTTPException(400, "new-season only available for animepahe")

if __name__ == "__main__":
    uvicorn.run("router:app", host="0.0.0.0", port=8888, reload=True)
