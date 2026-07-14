"""
NanimeID API Wrapper
REST API: mainappsv1.nanimeid.xyz/2.1.0/
"""

import httpx

API_BASE = "https://mainappsv1.nanimeid.xyz/2.1.0"
CDN_BASE = "https://cdn-stable.nanimeid.xyz"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

client = httpx.Client(headers=HEADERS, timeout=30)


def search(query: str, limit: int = 10) -> dict:
    resp = client.get(f"{API_BASE}/anime/live-search", params={"q": query, "limit": limit})
    resp.raise_for_status()
    data = resp.json()
    results = []
    for item in data.get("data", []):
        results.append({
            "id": item["id"],
            "title": item["nama_anime"],
            "image": item["gambar_anime"],
            "genres": item.get("genre_anime", []),
            "status": item.get("status_anime", ""),
            "rating": item.get("rating_anime", ""),
            "studio": item.get("studio_anime", []),
            "aliases": [a["alias"] for a in item.get("aliases", [])],
        })
    return {"success": True, "query": query, "results": results}


def home() -> dict:
    resp = client.get(f"{API_BASE}/anime/latest", params={"limit": 30, "type": "ANIME"})
    resp.raise_for_status()
    data = resp.json()
    results = []
    for item in data.get("items", []):
        ep = item.get("last_episode", {})
        results.append({
            "id": item["id"],
            "title": item["nama_anime"],
            "image": item["gambar_anime"],
            "genres": item.get("genre_anime", []),
            "status": item.get("status_anime", ""),
            "rating": item.get("rating_anime", ""),
            "synopsis": item.get("sinopsis_anime", ""),
            "last_episode": ep.get("nomor_episode", ""),
            "last_episode_title": ep.get("judul_episode", ""),
        })
    return {"success": True, "latest": results, "total": data.get("total", 0)}


def anime_list(page: int = 1, limit: int = 24) -> dict:
    resp = client.get(f"{API_BASE}/anime", params={"page": page, "limit": limit, "sortBy": "id", "order": "desc"})
    resp.raise_for_status()
    data = resp.json()
    results = []
    for item in data.get("data", []):
        results.append({
            "id": item["id"],
            "title": item["nama_anime"],
            "image": item["gambar_anime"],
            "genres": item.get("genre_anime", []),
            "status": item.get("status_anime", ""),
            "rating": item.get("rating_anime", ""),
            "views": item.get("view_anime", ""),
            "label": item.get("label_anime", ""),
        })
    return {
        "success": True, "page": page, "limit": limit,
        "total": data.get("meta", {}).get("total", 0),
        "results": results,
    }


def anime_detail(anime_id: int) -> dict:
    resp = client.get(f"{API_BASE}/anime/{anime_id}")
    resp.raise_for_status()
    item = resp.json()["data"]

    episodes = []
    for ep in item.get("episodes", []):
        qualities = []
        for q in ep.get("qualities", []):
            qualities.append({
                "quality": q["nama_quality"],
                "url": q["source_quality"],
            })
        episodes.append({
            "id": ep["id"],
            "number": ep["nomor_episode"],
            "title": ep["judul_episode"],
            "thumbnail": ep.get("thumbnail_episode", ""),
            "duration": ep.get("durasi_episode", 0),
            "views": ep.get("view_episode", 0),
            "qualities": qualities,
        })

    return {"success": True, "data": {
        "id": item["id"],
        "title": item["nama_anime"],
        "image": item["gambar_anime"],
        "genres": item.get("genre_anime", []),
        "status": item.get("status_anime", ""),
        "rating": item.get("rating_anime", ""),
        "views": item.get("view_anime", ""),
        "synopsis": item.get("sinopsis_anime", ""),
        "studio": item.get("studio_anime", []),
        "aliases": [a["alias"] for a in item.get("aliases", [])],
        "total_episodes": item.get("episodes_count", 0),
        "episodes": episodes,
    }}


def episode_watch(anime_id: int, ep_num: int) -> dict:
    resp = client.get(f"{API_BASE}/episode/anime/{anime_id}/episode/{ep_num}")
    resp.raise_for_status()
    data = resp.json()["data"]

    ep = data["episode"]
    anime = data.get("anime", {})
    nav = data.get("navigation", {})

    qualities = []
    for q in ep.get("qualities", []):
        qualities.append({
            "quality": q["nama_quality"],
            "url": q["source_quality"],
        })

    return {"success": True, "data": {
        "id": ep["id"],
        "anime_id": anime_id,
        "number": ep["nomor_episode"],
        "title": ep["judul_episode"],
        "thumbnail": ep.get("thumbnail_episode", ""),
        "duration": ep.get("durasi_episode", 0),
        "qualities": qualities,
        "anime_title": anime.get("nama_anime", ""),
        "prev_episode": nav.get("previousEpisode"),
        "next_episode": nav.get("nextEpisode"),
        "total_episodes": nav.get("totalEpisodes", 0),
    }}


def leaderboard(page: int = 1, limit: int = 10) -> dict:
    resp = client.get(f"{API_BASE}/leaderboard/weekly", params={"page": page, "limit": limit})
    resp.raise_for_status()
    return {"success": True, "data": resp.json()}


def related_anime(anime_id: int) -> dict:
    resp = client.get(f"{API_BASE}/anime/{anime_id}/related")
    resp.raise_for_status()
    data = resp.json()
    results = []
    for item in data.get("data", []):
        results.append({
            "id": item["id"],
            "title": item.get("nama_anime", ""),
            "image": item.get("gambar_anime", ""),
        })
    return {"success": True, "data": results}
