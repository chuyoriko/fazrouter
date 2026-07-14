"""
YesMovies123 - Movie & TV Show Scraper
WordPress + Dooplay theme v2.3.3

Endpoints:
- HTML: /movies/, /tvshows/, /movies/{slug}/, /tvshows/{slug}/
- WP REST API: /wp-json/wp/v2/genres (no auth)
- Dooplay API: /wp-json/dooplay/search/
- AJAX: POST /wp-admin/admin-ajax.php (doo_player_ajax)
"""

import re
import httpx
from bs4 import BeautifulSoup

BASE_URL = "https://ww.yesmovies123.me"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
}

client = httpx.Client(headers=HEADERS, timeout=30, follow_redirects=True)


def fetch(url: str) -> str:
    return client.get(url).text


def _get_dtgonza() -> dict:
    html = fetch(BASE_URL)
    m = re.search(r'dtGonza\s*=\s*({[^}]+})', html)
    if m:
        result = {}
        for kv in re.finditer(r'"(\w+)"\s*:\s*"([^"]*)"', m.group(1)):
            result[kv.group(1)] = kv.group(2)
        return result
    return {}


def _get_nonce() -> str:
    return _get_dtgonza().get("nonce", "")


def _get_search_api() -> str:
    return _get_dtgonza().get("api", f"{BASE_URL}/wp-json/dooplay/search/")


# ---- SEARCH ----
def search(query: str, page: int = 1) -> dict:
    nonce = _get_nonce()
    results = []

    if nonce:
        api = _get_search_api()
        resp = client.get(api, params={"keyword": query, "nonce": nonce})
        if resp.status_code == 200:
            try:
                data = resp.json()
                items = []
                # Response can be dict (keyed by post ID) or list
                if isinstance(data, dict):
                    items = data.values()
                elif isinstance(data, list):
                    items = data

                for item in items:
                    if not isinstance(item, dict): continue
                    url = item.get("url", "")
                    slug = url.rstrip("/").split("/")[-1]
                    if not slug: continue
                    mtype = "tv" if "/tvshows/" in url else "movie"
                    extra = item.get("extra", {}) if isinstance(item.get("extra"), dict) else {}
                    results.append({
                        "id": slug,
                        "title": item.get("title", ""),
                        "type": mtype,
                        "image": item.get("img", ""),
                        "url": url,
                        "date": extra.get("date", ""),
                        "rating": extra.get("imdb", ""),
                    })
            except:
                pass

    if not results:
        resp = client.get(f"{BASE_URL}/wp-json/wp/v2/search", params={
            "search": query, "per_page": 20, "page": page,
            "type": "post", "subtype": "movies,tvshows"
        })
        if resp.status_code == 200:
            for item in resp.json():
                if not isinstance(item, dict): continue
                url = item.get("url", "")
                slug = item.get("slug", "")
                results.append({
                    "id": slug,
                    "title": item.get("title", ""),
                    "type": "tv" if "shows" in item.get("subtype", "") else "movie",
                    "url": url,
                    "image": "",
                    "date": "",
                    "rating": "",
                })

    return {"success": True, "query": query, "results": results}


# ---- HOME ----
def home() -> dict:
    html = fetch(BASE_URL)
    soup = BeautifulSoup(html, "html.parser")

    def _extract_articles(container_selector: str = None):
        items = []
        articles = soup.select(container_selector) if container_selector else soup.select("article.item")
        if not articles:
            articles = soup.select("article.item")

        for article in articles:
            link = article.select_one("a[href]")
            img = article.select_one("img")
            title_el = article.select_one("h3 a, h4 a, h2 a")
            if not (link and title_el): continue

            href = link.get("href", "").rstrip("/")
            mtype = "tv" if "/tvshows/" in href else "movie"

            rating = ""
            rating_el = article.select_one(".rating span, .dt_rating_vgs")
            if rating_el:
                m = re.search(r'([\d.]+)', rating_el.text)
                if m: rating = m.group(1)

            date = ""
            date_el = article.select_one(".data > span:last-child, .meta .date")
            if date_el: date = date_el.text.strip()

            items.append({
                "id": href.split("/")[-1],
                "title": title_el.text.strip(),
                "type": mtype,
                "url": href if href.startswith("http") else BASE_URL + href,
                "image": img.get("src", "") if img else "",
                "rating": rating,
                "date": date,
            })
        return items

    all_items = _extract_articles()
    movies = [i for i in all_items if i["type"] == "movie"][:30]
    tvshows = [i for i in all_items if i["type"] == "tv"][:30]

    return {"success": True, "movies": movies, "tvshows": tvshows}


# ---- MOVIES / TVSHOWS LIST ----
def movies_page(page: int = 1) -> dict:
    return _list_page("movies", page)


def tvshows_page(page: int = 1) -> dict:
    return _list_page("tvshows", page)


def _list_page(media_type: str, page: int = 1) -> dict:
    url = f"{BASE_URL}/{media_type}/" if page == 1 else f"{BASE_URL}/{media_type}/page/{page}/"
    html = fetch(url)
    soup = BeautifulSoup(html, "html.parser")

    results = []
    for article in soup.select("article.item"):
        link = article.select_one("a[href]")
        img = article.select_one("img")
        title_el = article.select_one("h3 a, h4 a, h2 a")
        if not (link and title_el): continue

        href = link.get("href", "").rstrip("/")
        slug = href.split("/")[-1]

        rating = ""
        rating_el = article.select_one(".rating span, .dt_rating_vgs")
        if rating_el:
            m = re.search(r'([\d.]+)', rating_el.text)
            if m: rating = m.group(1)

        date = ""
        date_el = article.select_one(".data > span:last-child, .meta .date")
        if date_el: date = date_el.text.strip()

        desc = ""
        desc_el = article.select_one(".texto, .extra, .data p")
        if desc_el: desc = desc_el.text.strip()[:200]

        genres = []
        for a in article.select("a[href*='/genre/']"):
            g = a.text.strip()
            if g and g not in genres: genres.append(g)

        results.append({
            "id": slug,
            "title": title_el.text.strip(),
            "url": href if href.startswith("http") else BASE_URL + href,
            "image": img.get("src", "") if img else "",
            "rating": rating,
            "date": date,
            "description": desc,
            "genres": genres,
        })

    return {"success": True, "page": page, "results": results, "hasNext": len(results) >= 20}


# ---- MOVIE DETAIL ----
def movie_detail(slug: str) -> dict:
    url = f"{BASE_URL}/movies/{slug}/"
    html = fetch(url)
    soup = BeautifulSoup(html, "html.parser")

    title = soup.select_one("h1").text.strip() if soup.select_one("h1") else slug.replace("-", " ").title()

    poster = ""
    img = soup.select_one(".sheader .poster img, .poster img, article img.wp-post-image")
    if img: poster = img.get("src", "")

    # Extra meta from .sheader .data .extra
    tagline = ""
    release_date = ""
    country = ""
    rated = ""
    extra_el = soup.select_one(".sheader .data .extra")
    if extra_el:
        tagline_span = extra_el.select_one(".tagline")
        date_span = extra_el.select_one(".date")
        country_span = extra_el.select_one(".country")
        rated_span = extra_el.select_one(".CNR, .rated")
        if tagline_span: tagline = tagline_span.text.strip()
        if date_span: release_date = date_span.text.strip()
        if country_span: country = country_span.text.strip()
        if rated_span: rated = rated_span.text.strip()

    # Year from date
    year = ""
    if release_date:
        m = re.search(r'(\d{4})', release_date)
        if m: year = m.group(1)

    # Rating
    rating = ""
    rating_el = soup.select_one(".dt_rating_vgs, .dt_rating_data span[itemprop='ratingValue']")
    if rating_el:
        rating = rating_el.text.strip()

    # TMDb rating (sometimes shown separately)
    tmdb_rating = ""
    tmdb_el = soup.select_one(".dt_rating_data .rating, [itemprop='ratingValue'] + span")
    if not rating:
        for el in soup.select(".starstruck-rating span"):
            txt = el.text.strip()
            m = re.search(r'([\d.]+)\s*(votes|rating)', txt, re.I)
            if m: tmdb_rating = m.group(1)

    # Genres
    genres = []
    for a in soup.select(".sgeneros a[href*='/genre/']"):
        g = a.text.strip()
        if g and g not in genres: genres.append(g)

    # Description / Synopsis
    description = ""
    synopsis_el = soup.select_one(".wp-content, .entry-content, .sbox .wp-content")
    if synopsis_el:
        for p in synopsis_el.select("p"):
            txt = p.text.strip()
            if len(txt) > 50:
                description = txt
                break

    # Duration
    duration = ""
    duration_el = soup.select_one(".runtime, [class*='runtime'], [class*='duration']")
    if duration_el:
        m = re.search(r'(\d+\s*min)', duration_el.text)
        if m: duration = m.group(1)

    # Cast
    cast = []
    for person in soup.select(".person"):
        name_el = person.select_one(".data .name a, .data .name")
        role_el = person.select_one(".caracter, .data .caracter")
        img_el = person.select_one(".img img")
        if name_el:
            cast.append({
                "name": name_el.text.strip(),
                "character": role_el.text.strip() if role_el else "",
                "image": img_el.get("src", "") if img_el else "",
            })

    # Images / Backdrops
    images = []
    for img_el in soup.select(".screencap img, .gallery img, .sheader .poster img"):
        src = img_el.get("src", "")
        if src and src not in images:
            images.append(src)

    # Server options from player HTML
    servers = _extract_servers(soup)

    return {
        "slug": slug,
        "title": title,
        "poster": poster,
        "description": description or tagline,
        "genres": genres,
        "rating": rating or tmdb_rating,
        "releaseDate": release_date,
        "year": year,
        "duration": duration,
        "country": country,
        "rated": rated,
        "images": images,
        "servers": servers,
        "cast": cast,
        "type": "movie",
        "url": url,
    }


# ---- TV SHOW DETAIL ----
def tv_detail(slug: str) -> dict:
    url = f"{BASE_URL}/tvshows/{slug}/"
    html = fetch(url)
    soup = BeautifulSoup(html, "html.parser")

    title = soup.select_one("h1").text.strip() if soup.select_one("h1") else slug.replace("-", " ").title()

    poster = ""
    img = soup.select_one(".sheader .poster img, .poster img")
    if img: poster = img.get("src", "")

    tagline = ""
    date = ""
    country = ""
    extra_el = soup.select_one(".sheader .data .extra")
    if extra_el:
        tl = extra_el.select_one(".tagline")
        dt = extra_el.select_one(".date")
        ct = extra_el.select_one(".country")
        if tl: tagline = tl.text.strip()
        if dt: date = dt.text.strip()
        if ct: country = ct.text.strip()

    rating = ""
    rating_el = soup.select_one(".dt_rating_vgs")
    if rating_el: rating = rating_el.text.strip()

    genres = []
    for a in soup.select(".sgeneros a[href*='/genre/']"):
        g = a.text.strip()
        if g and g not in genres: genres.append(g)

    description = ""
    synopsis_el = soup.select_one(".wp-content, .entry-content")
    if synopsis_el:
        for p in synopsis_el.select("p"):
            txt = p.text.strip()
            if len(txt) > 50:
                description = txt
                break

    # Seasons (from episode list)
    seasons = _extract_seasons(soup, slug)

    # Cast
    cast = []
    for person in soup.select(".person"):
        name_el = person.select_one(".data .name a, .data .name")
        role_el = person.select_one(".caracter, .data .caracter")
        img_el = person.select_one(".img img")
        if name_el:
            cast.append({
                "name": name_el.text.strip(),
                "character": role_el.text.strip() if role_el else "",
                "image": img_el.get("src", "") if img_el else "",
            })

    servers = _extract_servers(soup)

    return {
        "slug": slug,
        "title": title,
        "poster": poster,
        "description": description or tagline,
        "genres": genres,
        "rating": rating,
        "date": date,
        "country": country,
        "seasons": seasons,
        "servers": servers,
        "cast": cast,
        "type": "tv",
        "url": url,
    }


# ---- WATCH ----
EMBED_API = "https://getsuperembed.link/"


def _resolve_embed(vs_url: str, media_type: str = "movie") -> dict:
    """Resolve vs_url (se_player.php) to actual embed URL via getsuperembed.link"""
    result = {"embedUrl": "", "streamUrl": ""}

    # Extract video_id from vs_url
    m = re.search(r'video_id=([a-zA-Z0-9]+)', vs_url)
    if not m:
        result["streamUrl"] = vs_url
        return result

    video_id = m.group(1)
    result["videoId"] = video_id

    # Call getsuperembed.link API
    resp = client.get(EMBED_API, params={
        "video_id": video_id,
        "tmdb": "0",
        "season": "0",
        "episode": "0" if media_type == "movie" else "1",
    })
    if resp.status_code == 200 and resp.text.startswith("http"):
        result["embedUrl"] = resp.text.strip()
    else:
        result["embedUrl"] = f"{EMBED_API}?video_id={video_id}&tmdb=0"

    result["streamUrl"] = vs_url
    return result


def watch(slug: str, server_nume: str = "vs", media_type: str = "movie") -> dict:
    """Get streaming player for a movie or TV episode.
    For 'vs' type servers (direct URLs), returns the vs_url from detail page.
    For other servers, posts to admin-ajax.php to get the iframe.
    """
    if media_type == "movie":
        detail_url = f"{BASE_URL}/movies/{slug}/"
    else:
        detail_url = f"{BASE_URL}/tvshows/{slug}/"

    html = fetch(detail_url)
    soup = BeautifulSoup(html, "html.parser")

    # Find the server with matching nume
    player_url = ""
    for opt in soup.select(".dooplay_player_option"):
        nume = opt.get("data-nume", "")
        stype = opt.get("data-type", "movie")
        vs_url = opt.get("data-vs", "")

        if server_nume == "vs" and vs_url:
            player_url = vs_url
            break
        elif nume == server_nume or not server_nume:
            if vs_url:
                player_url = vs_url
            break

    # Fallback: use admin-ajax if not a vs server
    if not player_url and server_nume != "vs":
        post_id = server_nume if server_nume != "vs" else "vs"
        data = f"action=doo_player_ajax&post={post_id}&nume={server_nume}&type={media_type}"
        resp = client.post(
            f"{BASE_URL}/wp-admin/admin-ajax.php",
            content=data,
            headers={**HEADERS, "X-Requested-With": "XMLHttpRequest",
                      "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                      "Referer": detail_url, "Origin": BASE_URL}
        ).text
        iframe_match = re.search(r'<iframe[^>]+src=["\']([^"\']+)["\']', resp)
        if iframe_match:
            player_url = iframe_match.group(1)

    # Get all available servers
    servers = _extract_servers(soup)
    title = soup.select_one("h1").text.strip() if soup.select_one("h1") else slug

    # Resolve embed URL
    embed_info = _resolve_embed(player_url, media_type) if player_url else {"embedUrl": "", "streamUrl": ""}

    return {
        "success": True,
        "title": title,
        "slug": slug,
        "streamUrl": embed_info.get("streamUrl", player_url),
        "embedUrl": embed_info.get("embedUrl", ""),
        "videoId": embed_info.get("videoId", ""),
        "servers": servers,
        "type": media_type,
    }


def episode_watch(slug: str, episode_num: str) -> dict:
    return watch(slug, "vs", "tv")


# ---- GENRES ----
def genre_list() -> dict:
    resp = client.get(f"{BASE_URL}/wp-json/wp/v2/genres", params={"per_page": 50})
    genres = []
    if resp.status_code == 200:
        for g in resp.json():
            if isinstance(g, dict) and g.get("count", 0) > 0:
                genres.append({
                    "id": g.get("id"),
                    "name": g.get("name", ""),
                    "slug": g.get("slug", ""),
                    "count": g.get("count", 0),
                })
    return {"success": True, "genres": genres}


def genre_browse(genre_slug: str, page: int = 1, media_type: str = "movies") -> dict:
    url = f"{BASE_URL}/genre/{genre_slug}/"
    if page > 1:
        url += f"page/{page}/"
    html = fetch(url)
    soup = BeautifulSoup(html, "html.parser")

    results = []
    for article in soup.select("article.item"):
        link = article.select_one("a[href]")
        img = article.select_one("img")
        title_el = article.select_one("h3 a, h4 a, h2 a")
        if not (link and title_el): continue

        href = link.get("href", "").rstrip("/")
        slug = href.rstrip("/").split("/")[-1]

        results.append({
            "id": slug,
            "title": title_el.text.strip(),
            "url": href if href.startswith("http") else BASE_URL + href,
            "image": img.get("src", "") if img else "",
        })

    return {"success": True, "genre": genre_slug, "page": page, "results": results}


# ---- HELPER: Extract Server Options ----
def _extract_servers(soup: BeautifulSoup) -> list:
    servers = []
    for opt in soup.select(".dooplay_player_option"):
        post_id = opt.get("data-post", "vs")
        nume = opt.get("data-nume", "1")
        stype = opt.get("data-type", "movie")
        vs_url = opt.get("data-vs", "")

        title_span = opt.select_one(".title")
        server_span = opt.select_one(".server")
        name = title_span.text.strip() if title_span else (server_span.text.strip() if server_span else f"Server {nume}")

        servers.append({
            "name": name,
            "post": post_id,
            "nume": nume,
            "type": stype,
            "vs_url": vs_url if vs_url else None,
        })

    return servers


# ---- HELPER: Extract Seasons ----
def _extract_seasons(soup: BeautifulSoup, show_slug: str) -> list:
    seasons = []
    se_containers = soup.select(".se-c, .temporada, [class*='season']")

    for sc in se_containers:
        sname_el = sc.select_one("h2, h3, h4, .title, .se-title")
        season_name = sname_el.text.strip() if sname_el else f"Season {len(seasons)+1}"

        episodes = []
        for link in sc.select("a[href*='episodes/'], a[href*='tvshows/']"):
            href = link.get("href", "").rstrip("/")
            ep_text = link.text.strip()

            ep_num = ""
            m = re.search(r'[Ee]pisode\s*(\d+)', ep_text)
            if m:
                ep_num = m.group(1)
            else:
                ep_match = re.search(r'(\d+)', href.split("/")[-1])
                if ep_match: ep_num = ep_match.group(1)

            episodes.append({
                "id": href.split("/")[-1],
                "number": ep_num,
                "title": ep_text,
                "url": href if href.startswith("http") else BASE_URL + href,
            })

        if episodes:
            seasons.append({"name": season_name, "episodes": episodes})

    return seasons
