import re
import base64
import httpx
from bs4 import BeautifulSoup

BASE_URL = "https://animepahe.live"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "en-US,en;q=0.9",
}

client = httpx.Client(headers=HEADERS, timeout=30, follow_redirects=True)


def fetch(url: str) -> str:
    resp = client.get(url)
    resp.raise_for_status()
    return resp.text


def search(query: str, page: int = 1) -> dict:
    url = f"{BASE_URL}/search?keyword={query}"
    if page > 1:
        url += f"&page={page}"
    html = fetch(url)
    soup = BeautifulSoup(html, "html.parser")
    results = []
    for link in soup.select("a[href*='/anime/']"):
        href = link.get("href", "")
        if not href or href.count("/") < 2:
            continue
        slug = href.split("/anime/")[-1]
        title = link.text.strip()
        if not title or any(kw in title.lower() for kw in ["home", "genre", "watch", "season", "dub"]):
            continue
        results.append({
            "id": slug,
            "title": title,
            "url": href if href.startswith("http") else BASE_URL + href,
        })
    return {"success": True, "query": query, "page": page, "results": results}


def home() -> dict:
    html = fetch(BASE_URL)
    soup = BeautifulSoup(html, "html.parser")
    latest = []
    seen = set()
    for link in soup.select("a[href*='/anime/']"):
        href = link.get("href", "")
        slug = href.split("/anime/")[-1] if "/anime/" in href else ""
        title = link.text.strip()
        if slug and title and slug not in seen and len(title) > 2:
            seen.add(slug)
            img = link.select_one("img")
            latest.append({
                "id": slug,
                "title": title,
                "url": href if href.startswith("http") else BASE_URL + href,
                "image": img.get("src", "") if img else "",
            })
    return {"success": True, "latest": latest[:24]}


def anime_list(page: int = 1) -> dict:
    url = f"{BASE_URL}/anime?page={page}" if page > 1 else f"{BASE_URL}/anime"
    html = fetch(url)
    soup = BeautifulSoup(html, "html.parser")
    results = []
    seen = set()
    for link in soup.select("a[href*='/anime/']"):
        href = link.get("href", "")
        slug = href.split("/anime/")[-1] if "/anime/" in href else ""
        title = link.text.strip()
        if slug and title and slug not in seen and len(title) > 2:
            seen.add(slug)
            if not any(kw in title.lower() for kw in ["home", "genre", "watch", "dub"]):
                results.append({"id": slug, "title": title, "url": BASE_URL + href})
    return {"success": True, "page": page, "results": results}


def anime_detail(slug: str) -> dict:
    url = f"{BASE_URL}/anime/{slug}"
    html = fetch(url)
    soup = BeautifulSoup(html, "html.parser")

    title = ""
    title_el = soup.select_one(".anime_name h1, .title_name h2, h1")
    if title_el:
        title = title_el.text.strip()

    poster = ""
    img = soup.select_one(".anime_info img, img.poster, .anime-poster img")
    if img:
        poster = img.get("src", "")

    synopsis = ""
    syn_el = soup.select_one(".synopsis, .plot-summary, [class*=synopsis]")
    if syn_el:
        synopsis = syn_el.text.strip()

    genres = []
    genre_section = soup.select_one(".anime_info, [class*=genre], .anime-genres")
    scope = genre_section if genre_section else soup
    for gl in scope.select('a[href*="/genre/"]'):
        g = gl.text.strip()
        if g and g not in genres:
            genres.append(g)

    info = {}
    for row in soup.select(".anime_info span, .anime-info"):
        text = row.text.strip()
        if ":" in text:
            k, v = text.split(":", 1)
            info[k.strip()] = v.strip()

    episodes = []
    for link in soup.select("a[href*='/episode/']"):
        href = link.get("href", "")
        ep_slug = href.split("/episode/")[-1] if "/episode/" in href else ""
        ep_text = link.text.strip()
        if ep_slug and ep_text:
            ep_num = 1
            m = re.search(r"EP\s*(\d+)", ep_text, re.I)
            if m:
                ep_num = int(m.group(1))
            episodes.append({
                "number": ep_num,
                "id": ep_slug,
                "title": ep_text,
                "url": href if href.startswith("http") else BASE_URL + href,
            })

    return {
        "slug": slug,
        "title": title,
        "poster": poster,
        "synopsis": synopsis,
        "genres": genres,
        "info": info,
        "total_episodes": len(episodes),
        "episodes": episodes,
    }


def episode_watch(slug: str, ep_slug: str = None) -> dict:
    if ep_slug:
        url = f"{BASE_URL}/episode/{ep_slug}"
    else:
        url = f"{BASE_URL}/episode/{slug}-episode-1"
    html = fetch(url)
    soup = BeautifulSoup(html, "html.parser")

    servers = []
    for srv in soup.select("[data-video]"):
        encoded = srv.get("data-video", "")
        name = srv.text.strip().replace("Choose this server", "").strip()
        url_decoded = ""
        if encoded:
            try:
                url_decoded = base64.b64decode(encoded).decode()
            except Exception:
                url_decoded = encoded
        servers.append({"name": name, "url": url_decoded, "encoded": encoded})

    episode_title = ""
    h1 = soup.select_one("h1, .anime_name h2")
    if h1:
        episode_title = h1.text.strip()

    related_eps = []
    for link in soup.select(".anime_video_body_episodes a, #episode_related a"):
        href = link.get("href", "")
        if "/episode/" in href:
            related_eps.append({
                "id": href.split("/episode/")[-1],
                "title": link.text.strip(),
                "url": href if href.startswith("http") else BASE_URL + href,
            })

    return {
        "episode_title": episode_title,
        "servers": servers,
        "related_episodes": related_eps,
    }


def movies(page: int = 1) -> dict:
    url = f"{BASE_URL}/movies?page={page}" if page > 1 else f"{BASE_URL}/movies"
    html = fetch(url)
    soup = BeautifulSoup(html, "html.parser")
    results = []
    seen = set()
    for link in soup.select("a[href*='/anime/']"):
        href = link.get("href", "")
        slug = href.split("/anime/")[-1] if "/anime/" in href else ""
        title = link.text.strip()
        if slug and title and slug not in seen and len(title) > 3:
            seen.add(slug)
            results.append({"id": slug, "title": title, "url": BASE_URL + href})
    return {"success": True, "page": page, "results": results}


def popular(page: int = 1) -> dict:
    url = f"{BASE_URL}/popular?page={page}" if page > 1 else f"{BASE_URL}/popular"
    html = fetch(url)
    soup = BeautifulSoup(html, "html.parser")
    results = []
    seen = set()
    for link in soup.select("a[href*='/anime/']"):
        href = link.get("href", "")
        slug = href.split("/anime/")[-1] if "/anime/" in href else ""
        title = link.text.strip()
        if slug and title and slug not in seen and len(title) > 3:
            seen.add(slug)
            results.append({"id": slug, "title": title, "url": BASE_URL + href})
    return {"success": True, "page": page, "results": results}


def genre(genre: str, page: int = 1) -> dict:
    url = f"{BASE_URL}/genre/{genre}?page={page}" if page > 1 else f"{BASE_URL}/genre/{genre}"
    html = fetch(url)
    soup = BeautifulSoup(html, "html.parser")
    results = []
    seen = set()
    for link in soup.select("a[href*='/anime/']"):
        href = link.get("href", "")
        slug = href.split("/anime/")[-1] if "/anime/" in href else ""
        title = link.text.strip()
        if slug and title and slug not in seen and len(title) > 3:
            seen.add(slug)
            results.append({"id": slug, "title": title, "url": BASE_URL + href})
    return {"success": True, "genre": genre, "page": page, "results": results}


def new_season(page: int = 1) -> dict:
    url = f"{BASE_URL}/new-season?page={page}" if page > 1 else f"{BASE_URL}/new-season"
    html = fetch(url)
    soup = BeautifulSoup(html, "html.parser")
    results = []
    seen = set()
    for link in soup.select("a[href*='/anime/']"):
        href = link.get("href", "")
        slug = href.split("/anime/")[-1] if "/anime/" in href else ""
        title = link.text.strip()
        if slug and title and slug not in seen and len(title) > 3:
            seen.add(slug)
            results.append({"id": slug, "title": title, "url": BASE_URL + href})
    return {"success": True, "page": page, "results": results}
