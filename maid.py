import re
import httpx
from bs4 import BeautifulSoup

BASE_URL = "https://www.maid.my.id"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

client = httpx.Client(headers=HEADERS, timeout=30, follow_redirects=True)


def fetch(url: str) -> str:
    return client.get(url).text


def search(query: str, page: int = 1) -> dict:
    url = f"{BASE_URL}/?s={query}"
    html = fetch(url)
    soup = BeautifulSoup(html, "html.parser")
    results = []
    for a in soup.select("a[href*='/manga/']"):
        href = a.get("href", "").rstrip("/")
        slug = href.split("/manga/")[-1] if "/manga/" in href else ""
        title = a.text.strip()
        if slug and title and slug != "manga-list":
            results.append({"id": slug, "title": title, "url": href})
    return {"success": True, "query": query, "results": results}


def home() -> dict:
    html = fetch(BASE_URL)
    soup = BeautifulSoup(html, "html.parser")
    results = []
    for a in soup.select("a[href*='/manga/']"):
        href = a.get("href", "").rstrip("/")
        slug = href.split("/manga/")[-1] if "/manga/" in href else ""
        if not slug or slug == "manga-list":
            continue
        img = a.select_one("img")
        title = img.get("alt", "") if img else ""
        if not title:
            h = a.select_one("h2, h3, .title")
            title = h.text.strip() if h else a.text.strip()
        results.append({
            "id": slug,
            "title": title,
            "url": href,
            "image": img.get("data-src") or img.get("src", "") if img else "",
        })
    return {"success": True, "latest": results[:30]}


def manga_detail(slug: str) -> dict:
    url = f"{BASE_URL}/manga/{slug}/"
    html = fetch(url)
    soup = BeautifulSoup(html, "html.parser")

    title = ""
    for sel in ["h1", ".entry-title", ".anime_name h2", ".title_name h2", "title"]:
        el = soup.select_one(sel)
        if el:
            t = el.text.strip()
            if t and len(t) > 2:
                title = t
                break

    poster = ""
    for img in soup.select("img"):
        src = img.get("data-src") or img.get("src", "")
        if src and "uploads" in src and not any(x in src.lower() for x in ["icon", "avatar", "logo", "cropped", "favicon", "Maid-v2"]):
            poster = src
            break

    chapters = []
    for a in soup.select("a[href*='-bahasa-indonesia']"):
        href = a.get("href", "")
        parts = href.strip("/").split("/")
        ch_slug = parts[-1] if parts else ""
        ch_num = 1
        m = re.search(r"chapter[-\s]*(\d+)", ch_slug, re.I)
        if m:
            ch_num = int(m.group(1))
        chapters.append({
            "number": ch_num,
            "id": ch_slug,
            "title": a.text.strip(),
            "url": href,
        })

    return {
        "slug": slug,
        "title": title,
        "poster": poster,
        "total_chapters": len(chapters),
        "chapters": chapters,
    }


def chapter_read(slug: str) -> dict:
    url = f"{BASE_URL}/{slug}/"
    html = fetch(url)
    soup = BeautifulSoup(html, "html.parser")

    title = ""
    h1 = soup.select_one("h1, .entry-title")
    if h1:
        title = h1.text.strip()

    images = []
    seen = set()
    for img in soup.select("img"):
        src = img.get("data-lazy-src") or img.get("data-src") or img.get("data-original") or img.get("src", "")
        if not src or src.startswith("data:"):
            continue
        if any(x in src.lower() for x in ["icon", "avatar", "logo", "cropped", "favicon", "maid-v2", "maid-v2-gray", "gravatar"]):
            continue
        # keep imgbox (manga pages) and wp-content cover (has UUID or digits pattern)
        if "imgbox" in src or re.search(r"[a-f0-9]{8}-[a-f0-9]{4}", src):
            if src not in seen:
                seen.add(src)
                images.append(src)

    next_chap = ""
    for a in soup.select("a[href*='-bahasa-indonesia']"):
        href = a.get("href", "")
        if "next" in a.text.lower() or "next" in " ".join(a.get("class", [])):
            next_chap = href
            break

    prev_chap = ""
    for a in soup.select("a[href*='-bahasa-indonesia']"):
        if "prev" in a.text.lower() or "prev" in " ".join(a.get("class", [])):
            prev_chap = href
            break

    return {
        "title": title,
        "images": images,
        "prev_chapter": prev_chap,
        "next_chapter": next_chap,
    }
