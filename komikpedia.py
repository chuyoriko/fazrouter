import re
import httpx
from bs4 import BeautifulSoup

BASE_URL = "https://komikpedia.net"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

client = httpx.Client(headers=HEADERS, timeout=30, follow_redirects=True)


def fetch(url: str) -> str:
    return client.get(url).text


def search(query: str) -> dict:
    url = f"{BASE_URL}/manga?q={query}"
    html = fetch(url)
    soup = BeautifulSoup(html, "html.parser")
    results = []
    # Find manga cards on search page - they have h3 inside a link
    for link in soup.select("a[href*='/manga/']"):
        href = link.get("href", "").rstrip("/")
        slug = href.split("/manga/")[-1] if "/manga/" in href else ""
        if not slug or "genre=" in href:
            continue
        h3 = link.select_one("h3")
        img = link.select_one("img")
        if h3:
            results.append({
                "id": slug,
                "title": h3.text.strip(),
                "url": href if href.startswith("http") else BASE_URL + href,
                "image": img.get("src", "") if img else "",
            })
    return {"success": True, "query": query, "results": results}


def home() -> dict:
    url = f"{BASE_URL}/manga"
    html = fetch(url)
    soup = BeautifulSoup(html, "html.parser")
    results = []
    seen = set()
    for link in soup.select("a[href*='/manga/']"):
        href = link.get("href", "").rstrip("/")
        slug = href.split("/manga/")[-1] if "/manga/" in href else ""
        if not slug or slug in seen or "genre=" in href:
            continue
        seen.add(slug)
        img = link.select_one("img")
        h3 = link.select_one("h3")
        title = h3.text.strip() if h3 else (img.get("alt", "") if img else slug)
        results.append({
            "id": slug, "title": title,
            "url": href if href.startswith("http") else BASE_URL + href,
            "image": img.get("src", "") if img else "",
        })
    return {"success": True, "latest": results[:30]}


def manga_detail(slug: str) -> dict:
    url = f"{BASE_URL}/manga/{slug}"
    html = fetch(url)
    soup = BeautifulSoup(html, "html.parser")

    title = soup.select_one("h1") or soup.select_one("h2")
    title = title.text.strip() if title else ""

    poster = ""
    img = soup.select_one("img[alt]")
    if img:
        poster = img.get("src", "")

    synopsis = ""
    syn_el = soup.select_one("p")
    if syn_el:
        t = syn_el.text.strip()
        if len(t) > 30:
            synopsis = t

    genres = []
    for a in soup.select("a[href*='genre=']"):
        g = a.text.strip()
        if g and g not in genres:
            genres.append(g)

    chapters = []
    for a in soup.select("a[href*='/read/']"):
        href = a.get("href", "")
        parts = href.strip("/").split("/")
        ch_slug = parts[-1] if parts else ""
        num_found = re.search(r"chapter-(\d+)", ch_slug, re.I)
        ch_num = int(num_found.group(1)) if num_found else 0
        label = a.text.strip()
        if not label and ch_num:
            label = f"Chapter {ch_num}"
        chapters.append({
            "number": ch_num,
            "id": ch_slug,
            "title": label,
            "url": href if href.startswith("http") else BASE_URL + href,
        })

    return {
        "slug": slug, "title": title, "poster": poster,
        "synopsis": synopsis, "genres": genres,
        "total_chapters": len(chapters), "chapters": chapters,
    }


def chapter_read(slug: str, ch_slug: str) -> dict:
    url = f"{BASE_URL}/read/{slug}/{ch_slug}"
    html = fetch(url)
    soup = BeautifulSoup(html, "html.parser")

    title = ""
    h1 = soup.select_one("h1")
    if h1:
        title = h1.text.strip()

    images = []
    seen = set()
    for img in soup.select("img"):
        src = img.get("src", "")
        if not src or src in seen:
            continue
        if "edgeone.app" in src and "komiku.org" in src:
            # Keep the CDN proxy URL as-is — komiku blocks direct access
            if src not in seen:
                seen.add(src)
                images.append(src)
        elif "komiku.org" in src and "edgeone.app" not in src:
            if src not in seen:
                seen.add(src)
                images.append(src)

    prev_url = ""
    next_url = ""
    for a in soup.select("a[href*='/read/']"):
        h = a.get("href", "")
        if "/read/" in h:
            if not prev_url and "prev" not in a.text.lower():
                pass  # figure out from context
            if "next" in a.text.lower() or "next" in " ".join(a.get("class", [])):
                next_url = h

    return {"title": title, "images": images, "prev": prev_url, "next": next_url}
