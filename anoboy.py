import re
import base64
import httpx
from bs4 import BeautifulSoup

BASE_URL = "https://anoboy.id"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

client = httpx.Client(headers=HEADERS, timeout=30, follow_redirects=True)


def fetch(url: str) -> str:
    return client.get(url).text


def search(query: str) -> dict:
    import urllib.parse
    ajax_url = f"{BASE_URL}/wp-admin/admin-ajax.php"
    data = f"action=ts_ac_do_search&ts_ac_query={urllib.parse.quote(query)}"
    h = {**HEADERS, "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
         "X-Requested-With": "XMLHttpRequest"}
    resp = client.post(ajax_url, content=data, headers=h)
    resp.raise_for_status()
    body = resp.json()

    results = []
    for series_group in body.get("series", []):
        for item in series_group.get("all", []):
            href = item.get("post_link", "").rstrip("/")
            slug = href.split("/series/")[-1] if "/series/" in href else ""
            results.append({
                "id": slug, "title": item.get("post_title", ""),
                "url": href, "image": item.get("post_image", ""),
                "genres": item.get("post_genres", ""),
                "type": item.get("post_type", ""), "status": item.get("post_status", ""),
                "latest_ep": item.get("post_latest", ""),
            })
    return {"success": True, "query": query, "results": results}


def home() -> dict:
    html = fetch(BASE_URL)
    soup = BeautifulSoup(html, "html.parser")
    results, seen = [], set()
    for item in soup.select(".serieslist li"):
        link = item.select_one("h4 a.series")
        img = item.select_one("img")
        if link:
            href = link.get("href", "").rstrip("/")
            slug = href.split("/series/")[-1] if "/series/" in href else ""
            if slug and slug not in seen:
                seen.add(slug)
                results.append({
                    "id": slug, "title": link.text.strip(),
                    "url": href if href.startswith("http") else BASE_URL + href,
                    "image": img.get("src", "") if img else "",
                })
    return {"success": True, "latest": results[:30]}


def series_detail(slug: str) -> dict:
    url = f"{BASE_URL}/series/{slug}/"
    html = fetch(url)
    soup = BeautifulSoup(html, "html.parser")

    title = ""
    h1 = soup.select_one("h1, .entry-title")
    if h1: title = h1.text.strip()

    poster = ""
    img = soup.select_one(".thumb img, .series-thumb img, img.wp-post-image")
    if img: poster = img.get("src", "")

    info = {}
    for span in soup.select(".spe span, .info span"):
        text = span.text.strip()
        if ":" in text:
            k, v = text.split(":", 1)
            info[k.strip()] = v.strip()

    genres = []
    for a in soup.select("a[href*='/genres/']"):
        g = a.text.strip()
        if g and g not in genres: genres.append(g)

    episodes = []
    for ep in soup.select(".eplister li a, a[href*='episode']"):
        href = ep.get("href", "")
        if "episode" in href.lower():
            m = re.search(r"episode[-\s]*(\d+)", href, re.I)
            ep_num = int(m.group(1)) if m else 1
            episodes.append({
                "number": ep_num,
                "id": href.strip("/").split("/")[-1],
                "title": ep.text.strip() or f"Episode {ep_num}",
                "url": href if href.startswith("http") else BASE_URL + href,
            })
    return {
        "slug": slug, "title": title, "poster": poster,
        "info": info, "genres": genres,
        "total_episodes": len(episodes), "episodes": episodes,
    }


def episode_watch(slug: str) -> dict:
    url = f"{BASE_URL}/{slug}/"
    html = fetch(url)
    soup = BeautifulSoup(html, "html.parser")

    title = ""
    h1 = soup.select_one("h1, .entry-title")
    if h1: title = h1.text.strip()

    iframe = soup.select_one("#pembed iframe, .player-embed iframe, .video-content iframe")
    video_url = iframe.get("src", "") if iframe else ""

    mirrors = []
    for opt in soup.select("select.mirror option"):
        val = opt.get("value", "").strip()
        name = opt.text.strip()
        if not val: continue
        if not name: name = f"Mirror {len(mirrors)+1}"
        try:
            decoded = base64.b64decode(val).decode()
            m = re.search(r'src="([^"]+)"', decoded)
            mirrors.append({"name": name, "url": m.group(1) if m else decoded})
        except:
            mirrors.append({"name": name, "url": val})

    prev_ep, next_ep = "", ""
    for a in soup.select(".naveps a, .prevnext a"):
        txt = a.text.strip().lower()
        href = a.get("href", "")
        if "prev" in txt: prev_ep = href
        elif "next" in txt: next_ep = href

    return {
        "title": title, "player": video_url, "mirrors": mirrors,
        "prev_episode": prev_ep, "next_episode": next_ep,
    }


def genres_list() -> dict:
    html = fetch(f"{BASE_URL}/genres/")
    soup = BeautifulSoup(html, "html.parser")
    genres = []
    for a in soup.select("a[href*='/genres/']"):
        g = a.text.strip()
        if g and g not in genres and len(g) < 30: genres.append(g)
    return {"success": True, "genres": genres}


def genre_browse(genre: str, page: int = 1) -> dict:
    url = f"{BASE_URL}/genres/{genre}/"
    if page > 1: url += f"page/{page}/"
    html = fetch(url)
    soup = BeautifulSoup(html, "html.parser")
    results = []
    for item in soup.select(".serieslist li"):
        link = item.select_one("h4 a.series")
        img = item.select_one("img")
        if link:
            href = link.get("href", "").rstrip("/")
            slug = href.split("/series/")[-1] if "/series/" in href else ""
            if slug:
                results.append({
                    "id": slug, "title": link.text.strip(),
                    "url": href if href.startswith("http") else BASE_URL + href,
                    "image": img.get("src", "") if img else "",
                })
    return {"success": True, "genre": genre, "page": page, "results": results}
