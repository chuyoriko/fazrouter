"""
HiAnime scraper - class-based client for the router.
Extracted from hianime_api.py for reusability.
"""

import re
import httpx
from bs4 import BeautifulSoup

BASE_URL = "https://hianime.ad"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "en-US,en;q=0.9",
}


class HiAnimeClient:
    def __init__(self):
        self.client = None

    async def start(self):
        self.client = httpx.AsyncClient(headers=HEADERS, timeout=30, follow_redirects=True)

    async def stop(self):
        if self.client:
            await self.client.aclose()

    async def _fetch(self, url: str) -> str:
        resp = await self.client.get(url)
        resp.raise_for_status()
        return resp.text

    def _parse_cards(self, html: str) -> list:
        soup = BeautifulSoup(html, "html.parser")
        results = []
        for item in soup.select(".flw-item"):
            link = item.select_one("a.film-poster-ahref")
            img = item.select_one("img.film-poster-img")
            title = item.select_one(".film-name a")
            if not link or not title:
                continue
            sub = item.select_one(".tick-sub")
            dub = item.select_one(".tick-dub")
            dtype = []
            if sub: dtype.append("SUB")
            if dub: dtype.append("DUB")
            href = link.get("href", "")
            results.append({
                "id": href.split("/")[-1],
                "title": title.text.strip(),
                "url": BASE_URL + href,
                "image": img.get("data-src") or img.get("src", "") if img else "",
                "type": ",".join(dtype) if dtype else "TV",
                "data_jp": link.get("data-jp", ""),
            })
        return results

    async def search(self, q: str, page: int = 1):
        url = f"{BASE_URL}/filter?keyword={q}"
        if page > 1: url += f"&page={page}"
        html = await self._fetch(url)
        return {"success": True, "query": q, "page": page, "results": self._parse_cards(html)}

    async def home(self):
        html = await self._fetch(f"{BASE_URL}/home")
        soup = BeautifulSoup(html, "html.parser")
        trending = []
        for item in soup.select("#trending-home .swiper-slide"):
            link = item.select_one("a.item-qtip")
            img = item.select_one("img")
            name = item.select_one(".anime-slide-name") or item.select_one("h3 a")
            if link and name:
                trending.append({
                    "id": link.get("href", "").split("/")[-1],
                    "title": name.text.strip(),
                    "image": img.get("data-src") or img.get("src", "") if img else "",
                    "url": BASE_URL + link.get("href", ""),
                })
        return {"success": True, "trending": trending, "latest": self._parse_cards(html)}

    async def anime_detail(self, slug: str):
        html = await self._fetch(f"{BASE_URL}/anime/{slug}")
        soup = BeautifulSoup(html, "html.parser")

        title_el = soup.select_one("h2.film-name")
        title_jp = soup.select_one(".anisc-info .item.item-title .name")
        synopsis = soup.select_one(".film-description .text")
        poster = soup.select_one(".anisc-poster img")

        info = {}
        for row in soup.select(".anisc-info .item"):
            label = row.select_one(".item-head")
            val = row.select_one(".name")
            if label and val:
                info[label.text.strip(" :")] = val.text.strip()

        related = self._parse_cards(html)

        episodes = []
        try:
            ep_html = await self._fetch(f"{BASE_URL}/watch/{slug}/ep-1")
            esoup = BeautifulSoup(ep_html, "html.parser")
            for a in esoup.select(".ss-list-min a.ep-item"):
                num = a.get("data-num", "")
                href = a.get("href", "")
                name_el = a.select_one(".ep-name")
                episodes.append({
                    "number": int(num) if num and num.isdigit() else len(episodes) + 1,
                    "id": href.split("/")[-1] if href else "",
                    "title": name_el.text.strip() if name_el else a.get("title", f"Ep {num}"),
                    "url": BASE_URL + href if href else "",
                })
        except Exception:
            pass

        return {
            "success": True,
            "data": {
                "slug": slug,
                "title": title_el.text.strip() if title_el else "",
                "title_japanese": title_jp.text.strip() if title_jp else "",
                "synopsis": synopsis.text.strip() if synopsis else "",
                "poster": poster.get("src", "") if poster else "",
                "info": info,
                "related": related,
                "total_episodes": len(episodes),
                "episodes": episodes,
            },
        }

    async def watch(self, slug: str, ep: str):
        html = await self._fetch(f"{BASE_URL}/watch/{slug}/{ep}")
        soup = BeautifulSoup(html, "html.parser")

        servers = {}
        for tab in soup.select(".ps_-block"):
            tab_id = tab.get("data-id", "unknown")
            svlist = []
            for sv in tab.select(".server-items a.server-video"):
                svlist.append({
                    "name": sv.text.strip(),
                    "url": sv.get("data-video", ""),
                    "default": "default" in sv.get("class", []),
                })
            if svlist:
                servers[tab_id] = svlist

        data = {"servers": servers}
        for tab_servers in servers.values():
            for sv in tab_servers:
                u = sv["url"]
                if u and "vivibebe.site" in u:
                    try:
                        vhtml = await self._fetch(u)
                        m = re.search(r'const src = "(https://[^"]+/master\.m3u8)"', vhtml) or \
                            re.search(r"const src = '(https://[^']+/master\.m3u8)'", vhtml)
                        if m:
                            master = m.group(1)
                            vid_match = re.search(r"/([a-f0-9]+)/master\.m3u8", master)
                            data["video"] = {
                                "video_id": vid_match.group(1) if vid_match else "",
                                "master_m3u8": master,
                            }
                            m3u8 = await self._fetch(master)
                            qualities = []
                            for qm in re.finditer(
                                r'#EXT-X-STREAM-INF:BANDWIDTH=(\d+),RESOLUTION=(\d+x\d+),NAME="([^"]+)"\n(.+?)(?:\n|$)',
                                m3u8,
                            ):
                                bw, res, name, path = qm.groups()
                                qualities.append({
                                    "quality": name, "resolution": res,
                                    "bandwidth": int(bw),
                                    "url": master.rsplit("/", 1)[0] + "/" + path,
                                })
                            data["video"]["qualities"] = qualities
                    except Exception:
                        pass
                    break
            if "video" in data:
                break

        return {"success": True, "data": data}

    async def servers(self, slug: str, ep: str):
        result = await self.watch(slug, ep)
        return {"success": True, "slug": slug, "episode": ep, "servers": result["data"]["servers"]}

    async def stream(self, videoid: str):
        base = f"https://vivibebe.site/public/stream/{videoid}"
        master = f"{base}/master.m3u8"
        m3u8 = await self._fetch(master)
        qualities = []
        for m in re.finditer(
            r'#EXT-X-STREAM-INF:BANDWIDTH=(\d+),RESOLUTION=(\d+x\d+),NAME="([^"]+)"\n(.+?)(?:\n|$)',
            m3u8,
        ):
            bw, res, name, path = m.groups()
            qualities.append({
                "quality": name, "resolution": res, "bandwidth": int(bw),
                "url": master.rsplit("/", 1)[0] + "/" + path,
            })
        return {"success": True, "video_id": videoid, "master_m3u8": master, "qualities": qualities}

    async def popular(self, page: int = 1):
        url = f"{BASE_URL}/most-popular?page={page}"
        html = await self._fetch(url)
        return {"success": True, "page": page, "results": self._parse_cards(html)}

    async def movies(self, page: int = 1):
        url = f"{BASE_URL}/movie?page={page}"
        html = await self._fetch(url)
        return {"success": True, "page": page, "results": self._parse_cards(html)}

    async def genre(self, genre: str, page: int = 1):
        url = f"{BASE_URL}/genres/{genre}?page={page}"
        html = await self._fetch(url)
        return {"success": True, "genre": genre, "page": page, "results": self._parse_cards(html)}
