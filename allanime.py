"""
AllAnime provider - GraphQL API scraper with AES-256-CTR decryption.
Based on the Riko-Anime frontend's stream API.
"""

import re
import json
import hashlib
import httpx
from base64 import b64decode
from Crypto.Cipher import AES

ALLANIME_API = "https://api.allanime.day/api"
ALLANIME_REFERER = "https://allmanga.to"
YOUTU_CHAN_ORIGIN = "https://youtu-chan.com"
AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0"
EPISODE_PERSISTED_QUERY_HASH = "d405d0edd690624b66baba3068e0edc3ac90f1597d898a1ec8db4e5c43c00fec"

ALLANIME_KEY = hashlib.sha256(b"Xot36i3lK3:v1").digest()

HEX_TABLE = {
    "79": "A", "7a": "B", "7b": "C", "7c": "D", "7d": "E", "7e": "F", "7f": "G",
    "70": "H", "71": "I", "72": "J", "73": "K", "74": "L", "75": "M", "76": "N", "77": "O",
    "68": "P", "69": "Q", "6a": "R", "6b": "S", "6c": "T", "6d": "U", "6e": "V", "6f": "W",
    "60": "X", "61": "Y", "62": "Z",
    "59": "a", "5a": "b", "5b": "c", "5c": "d", "5d": "e", "5e": "f", "5f": "g",
    "50": "h", "51": "i", "52": "j", "53": "k", "54": "l", "55": "m", "56": "n", "57": "o",
    "48": "p", "49": "q", "4a": "r", "4b": "s", "4c": "t", "4d": "u", "4e": "v", "4f": "w",
    "40": "x", "41": "y", "42": "z",
    "08": "0", "09": "1", "0a": "2", "0b": "3", "0c": "4", "0d": "5", "0e": "6", "0f": "7",
    "00": "8", "01": "9",
    "15": "-", "16": ".", "67": "_", "46": "~",
    "02": ":", "17": "/", "07": "?", "1b": "#",
    "63": "[", "65": "]", "78": "@", "19": "!",
    "1c": "$", "1e": "&", "10": "(", "11": ")", "12": "*", "13": "+", "14": ",",
    "03": ";", "05": "=", "1d": "%",
}

headers = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "Referer": ALLANIME_REFERER,
    "User-Agent": AGENT,
}

client = httpx.Client(headers=headers, timeout=30, follow_redirects=True)

SEARCH_GQL = (
    "query($search: SearchInput $limit: Int $page: Int $translationType: VaildTranslationTypeEnumType $countryOrigin: VaildCountryOriginEnumType) { "
    "shows(search: $search limit: $limit page: $page translationType: $translationType countryOrigin: $countryOrigin) { "
    "edges { _id malId name englishName nativeName description thumbnail banner score type status "
    "genres studios season episodeCount episodeDuration availableEpisodes prevideos popularity } } }"
)

SHOW_GQL = (
    "query($showId: String!) { "
    "show(_id: $showId) { _id malId name englishName nativeName description thumbnail banner "
    "score type status genres studios season episodeCount episodeDuration "
    "availableEpisodes availableEpisodesDetail relatedShows prevideos popularity } }"
)

EPISODE_GQL = (
    "query($showId: String!, $translationType: VaildTranslationTypeEnumType!, $episodeString: String!) { "
    "episode(showId: $showId translationType: $translationType episodeString: $episodeString) { "
    "episodeString sourceUrls } }"
)

POPULAR_GQL = (
    "query($type: VaildPopularTypeEnumType!, $size: Int!, $allowAdult: Boolean, $allowUnknown: Boolean, $dateRange: Int) { "
    "queryPopular(type: $type size: $size allowAdult: $allowAdult allowUnknown: $allowUnknown dateRange: $dateRange) { "
    "recommendations { anyCard { _id } pageStatus { showId rangeViews } } } }"
)

SHOWS_WITH_IDS_GQL = (
    "query($ids: [String!]!) { showsWithIds(ids: $ids) { _id malId name englishName nativeName "
    "description thumbnail banner score type status genres studios season episodeCount "
    "episodeDuration availableEpisodes prevideos popularity } }"
)


def _gql(query, variables):
    resp = client.post(ALLANIME_API, json={"query": query, "variables": variables})
    resp.raise_for_status()
    data = resp.json()
    return data.get("data", {})


def _decode_hex_url(encoded):
    pairs = re.findall(r".{2}", encoded)
    return "".join(HEX_TABLE.get(p.lower(), "") for p in pairs)


def _decrypt_tobeparsed(blob):
    buf = b64decode(blob)
    iv = buf[1:13]
    ctr = iv + b"\x00\x00\x00\x02"
    ct_len = len(buf) - 13 - 16
    ciphertext = buf[13:13 + ct_len]
    cipher = AES.new(ALLANIME_KEY, AES.MODE_CTR, nonce=b"", initial_value=ctr)
    return cipher.decrypt(ciphertext).decode("utf-8")


def _infer_quality(*values):
    for v in values:
        if not v:
            continue
        match = re.search(r"(?:^|[^0-9])([1-9][0-9]{2,3})p?", v, re.IGNORECASE)
        if match:
            h = int(match.group(1))
            if 240 <= h <= 2160:
                return f"{h}p"
    return "auto"


def _resolve_clock_url(clock_path):
    """Resolve clock/apiak URLs to get direct stream links."""
    # Try multiple endpoint variations — AllAnime changes these periodically
    urls_to_try = [f"https://allanime.day{clock_path}"]

    # If it's /apivtwo/clock, also try /apiak/ variant and .json suffix
    if "/apivtwo/clock" in clock_path:
        if not clock_path.endswith(".json"):
            urls_to_try.append(f"https://allanime.day{clock_path.replace('/clock', '/clock.json')}")
        # Try apiak endpoint too
        apiak_path = clock_path.replace("/apivtwo/clock", "/apiak/sk.json").replace("?id=", "?sr=")
        urls_to_try.append(f"https://allanime.day{apiak_path}")
    elif "/apiak/" in clock_path:
        # Also try apivtwo variant
        apivtwo_path = clock_path.replace("/apiak/sk.json", "/apivtwo/clock.json").replace("?sr=", "?id=")
        urls_to_try.append(f"https://allanime.day{apivtwo_path}")

    for url in urls_to_try:
        try:
            resp = client.get(url)
            if resp.status_code != 200:
                continue
            text = resp.text
            if not text or text.strip() in ("", "error", "Not found"):
                continue
            results = []

            for m in re.finditer(r'"link":"([^"]+)"[^}]*?"resolutionStr":"([^"]+)"', text):
                link_url = m.group(1).replace("\\", "")
                quality = _infer_quality(m.group(2), link_url) or m.group(2)
                results.append({
                    "url": link_url,
                    "quality": quality,
                    "isM3U8": ".m3u8" in link_url,
                })

            for m in re.finditer(r'"hls"[^}]*?"url":"([^"]+)"', text):
                hls_url = m.group(1).replace("\\", "")
                results.append({
                    "url": hls_url,
                    "quality": _infer_quality(hls_url),
                    "isM3U8": True,
                })

            # Also try JSON parse
            if not results:
                try:
                    data = json.loads(text)
                    links = data.get("links") or []
                    for link_obj in links:
                        link_url = link_obj.get("link") or link_obj.get("url") or ""
                        if link_url:
                            link_url = link_url.replace("\\", "")
                            res_str = link_obj.get("resolutionStr") or link_obj.get("quality") or ""
                            quality = _infer_quality(res_str, link_url) or res_str or "auto"
                            results.append({
                                "url": link_url,
                                "quality": quality,
                                "isM3U8": ".m3u8" in link_url,
                            })
                    # Also check for direct hls field
                    if not results:
                        hls_url = data.get("hls") or data.get("url") or ""
                        if hls_url:
                            results.append({
                                "url": hls_url,
                                "quality": _infer_quality(hls_url),
                                "isM3U8": True,
                            })
                except (json.JSONDecodeError, AttributeError):
                    pass

            if results:
                return results
        except Exception:
            continue

    return []


def _resolve_sources(source_urls):
    streams = []
    sorted_sources = sorted(source_urls or [], key=lambda s: s.get("priority", 0), reverse=True)
    for src in sorted_sources:
        raw = src.get("sourceUrl", "") or ""
        name = src.get("sourceName", "") or ""

        if raw.startswith("--"):
            hex_str = raw[2:]
            decoded = _decode_hex_url(hex_str)

            if "tools.fast4speed.rsvp" in decoded:
                streams.append({
                    "url": decoded,
                    "quality": _infer_quality(name, decoded),
                    "isM3U8": ".m3u8" in decoded,
                })
                continue

            if "/clock" in decoded and not decoded.endswith(".json"):
                decoded = decoded.replace("/clock", "/clock.json")

            if decoded.startswith("/"):
                clock_results = _resolve_clock_url(decoded)
                streams.extend(clock_results)
                continue

            if decoded.startswith("http"):
                streams.append({
                    "url": decoded,
                    "quality": _infer_quality(name, decoded),
                    "isM3U8": ".m3u8" in decoded,
                })
                continue

            if decoded.startswith("//"):
                full_url = "https:" + decoded
                streams.append({
                    "url": full_url,
                    "quality": _infer_quality(name, full_url),
                    "isM3U8": ".m3u8" in full_url,
                })
                continue

        elif raw.startswith("//"):
            full_url = "https:" + raw
            streams.append({
                "url": full_url,
                "quality": _infer_quality(name, full_url),
                "isM3U8": ".m3u8" in full_url,
            })

        elif raw.startswith("http"):
            # Check if this is an allanime.day clock/apiak URL that needs resolution
            if "allanime.day" in raw and ("/clock" in raw or "/apiak/" in raw):
                try:
                    parsed_url = raw.replace("https://allanime.day", "")
                    clock_results = _resolve_clock_url(parsed_url)
                    streams.extend(clock_results)
                except Exception:
                    pass
                continue
            streams.append({
                "url": raw,
                "quality": _infer_quality(name, raw),
                "isM3U8": False,
            })

    return streams


def _parse_show(show):
    if not show or not show.get("_id"):
        return None
    sid = show["_id"]
    title = (show.get("englishName") or show.get("name") or show.get("nativeName") or "Untitled").strip()
    thumb = show.get("thumbnail") or ""
    if thumb and not thumb.startswith("http"):
        thumb = f"https://allanime.day{thumb}" if thumb.startswith("/") else f"https://allanime.day/{thumb}"
    banner = show.get("banner") or thumb
    if banner and not banner.startswith("http"):
        banner = f"https://allanime.day{banner}" if banner.startswith("/") else f"https://allanime.day/{banner}"

    ep_count = show.get("availableEpisodes") or {}
    episodes = ep_count.get("sub", 0) or show.get("episodeCount", 0) or 0
    try:
        episodes = int(episodes)
    except (ValueError, TypeError):
        episodes = 0

    genres = show.get("genres") or []
    studios = show.get("studios") or []
    season = show.get("season") or {}
    season_year = season.get("year")

    # Status mapping
    status_raw = (show.get("status") or "").lower()
    if "finish" in status_raw or "complete" in status_raw:
        status = "Completed"
    elif "upcoming" in status_raw or "not yet" in status_raw:
        status = "Upcoming"
    else:
        status = "Airing"

    # Type mapping
    type_raw = (show.get("type") or "").lower()
    if "movie" in type_raw:
        anime_type = "Movie"
    elif "ova" in type_raw:
        anime_type = "OVA"
    else:
        anime_type = "TV"

    return {
        "id": sid,
        "title": title,
        "altTitle": show.get("name") if show.get("name") != title else (show.get("nativeName") or ""),
        "description": (show.get("description") or "").replace("<br>", "\n").replace("<i>", "").replace("</i>", "")[:500],
        "poster": thumb or f"https://picsum.photos/seed/{sid}/600/900",
        "banner": banner or f"https://picsum.photos/seed/{sid}b/1920/1080",
        "score": show.get("score"),
        "type": anime_type,
        "status": status,
        "genres": genres,
        "studios": studios,
        "year": season_year,
        "episodes": episodes,
        "malId": show.get("malId"),
    }


def search(query, page=1):
    data = _gql(SEARCH_GQL, {
        "search": {"allowAdult": False, "allowUnknown": False, "query": query},
        "limit": 24,
        "page": page,
        "translationType": "sub",
        "countryOrigin": "ALL",
    })
    edges = (data.get("shows") or {}).get("edges") or []
    results = [_parse_show(s) for s in edges]
    results = [r for r in results if r]
    return {"success": True, "query": query, "page": page, "results": results}


def home():
    data = _gql(SEARCH_GQL, {
        "search": {"allowAdult": False, "allowUnknown": False, "query": ""},
        "limit": 30,
        "page": 1,
        "translationType": "sub",
        "countryOrigin": "JP",
    })
    edges = (data.get("shows") or {}).get("edges") or []
    results = [_parse_show(s) for s in edges]
    results = [r for r in results if r]
    return {"success": True, "latest": results}


def anime_detail(slug):
    show_data = _gql(SHOW_GQL, {"showId": slug})
    show = show_data.get("show")
    if not show:
        return {"success": False, "error": "Anime not found"}
    parsed = _parse_show(show)
    if not parsed:
        return {"success": False, "error": "Failed to parse anime"}

    # Get episode list (cap at 200)
    ep_detail = show.get("availableEpisodesDetail") or {}
    sub_eps = ep_detail.get("sub") or []
    ep_list = []
    if sub_eps:
        ep_list = sorted(set(int(e) for e in sub_eps if str(e).isdigit() and int(e) > 0))
    else:
        total = parsed.get("episodes", 0)
        if total > 0:
            ep_list = list(range(1, min(total, 5000) + 1))
    ep_list = ep_list[:200]

    # Related shows
    related_raw = show.get("relatedShows") or []
    related = []
    for rel in related_raw[:10]:
        rid = rel.get("showId")
        relation = rel.get("relation") or "related"
        if rid:
            related.append({"id": rid, "relation": relation.replace("_", " ").title()})

    # Trailer
    prevideos = show.get("prevideos") or []
    trailer = None
    if prevideos:
        vid = prevideos[0]
        if re.match(r"^[a-zA-Z0-9_-]{8,15}$", vid):
            trailer = f"https://www.youtube.com/watch?v={vid}"

    parsed["episodeList"] = ep_list
    parsed["relatedShows"] = related
    parsed["trailerUrl"] = trailer

    return {"success": True, "data": parsed}


def _extract_tobeparsed_sources(payload):
    """Extract sourceUrls from a payload that may have top-level or nested tobeparsed."""
    d = payload.get("data") or {}
    
    # Direct episode data
    ep = d.get("episode") or {}
    if ep.get("sourceUrls"):
        return ep["sourceUrls"]
    
    # tobeparsed in data
    tp = d.get("tobeparsed")
    if tp:
        try:
            plain = _decrypt_tobeparsed(tp)
            parsed = json.loads(plain)
            tp_ep = (parsed.get("episode") or {})
            if tp_ep.get("sourceUrls"):
                return tp_ep["sourceUrls"]
        except Exception:
            pass
    
    # Check full response as string
    raw = json.dumps(payload)
    if '"tobeparsed"' in raw:
        match = re.search(r'"tobeparsed":"([^"]+)"', raw)
        if match:
            try:
                plain = _decrypt_tobeparsed(match.group(1))
                parsed = json.loads(plain)
                tp_ep = (parsed.get("episode") or {})
                if tp_ep.get("sourceUrls"):
                    return tp_ep["sourceUrls"]
            except Exception:
                pass
    
    return []


def _normalize_title(value):
    """Normalize title for comparison."""
    import re as _re
    return _re.sub(r'\s+', ' ', _re.sub(r'[^a-z0-9\s]', ' ', value.lower())).strip()


def _title_score(query_normalized, candidate_name):
    """Score how well a candidate matches the search query."""
    candidate = _normalize_title(candidate_name)
    if candidate == query_normalized:
        return 100
    if query_normalized in candidate:
        return 80
    if candidate in query_normalized:
        return 70
    query_tokens = set(query_normalized.split())
    candidate_tokens = set(candidate.split())
    overlap = len(query_tokens & candidate_tokens)
    return round((overlap / max(len(query_tokens), 1)) * 50)


def _rank_candidates(search_query, episode_num, edges):
    """Rank search result candidates by relevance and episode coverage."""
    query_normalized = _normalize_title(search_query)

    special_tokens = {
        'movie', 'film', 'special', 'ova', 'ona', 'recap', 'log',
        'digest', 'preview', 'summary', 'compilation', 'omake', 'short',
    }

    def get_sub_count(edge):
        ep = edge.get("availableEpisodes") or {}
        sub = ep.get("sub", 0)
        try:
            return int(sub)
        except (ValueError, TypeError):
            return 0

    sub_counts = sorted([get_sub_count(e) for e in edges if get_sub_count(e) > 0], reverse=True)
    max_sub = sub_counts[0] if sub_counts else 0
    second_max = sub_counts[1] if len(sub_counts) > 1 else 0
    has_dominant = max_sub >= 50 and (second_max == 0 or max_sub >= second_max * 3)

    ranked = []
    for i, edge in enumerate(edges):
        display_name = (edge.get("englishName") or edge.get("name") or "").strip()
        sub_count = get_sub_count(edge)
        has_coverage = sub_count >= episode_num

        order_bonus = max(0, 20 - i)
        availability_bonus = min(sub_count, 300) / 5
        coverage_bonus = 30 if has_coverage else -20

        name_lower = _normalize_title(display_name)
        special_penalty = -35 if any(t in name_lower.split() for t in special_tokens) else 0
        dominant_bonus = 80 if (has_dominant and sub_count == max_sub) else 0

        score = (_title_score(query_normalized, display_name)
                + order_bonus + availability_bonus + coverage_bonus
                + special_penalty + dominant_bonus)

        ranked.append({"edge": edge, "score": score})

    ranked.sort(key=lambda x: x["score"], reverse=True)
    return ranked


def _fetch_episode_sources(show_id, ep_num):
    """Fetch episode sources with persisted query + GQL fallback."""
    source_urls = []

    variables = {"showId": show_id, "translationType": "sub", "episodeString": str(ep_num)}
    extensions = {"persistedQuery": {"version": 1, "sha256Hash": EPISODE_PERSISTED_QUERY_HASH}}

    # Try persisted query (uses youtu-chan origin for better source access)
    try:
        pq_headers = {
            "Accept": "application/json",
            "User-Agent": AGENT,
            "Origin": YOUTU_CHAN_ORIGIN,
            "Referer": YOUTU_CHAN_ORIGIN + "/",
        }
        resp = httpx.get(ALLANIME_API, params={
            "variables": json.dumps(variables),
            "extensions": json.dumps(extensions),
        }, headers=pq_headers, timeout=30, follow_redirects=True)
        if resp.status_code == 200:
            payload = resp.json()
            source_urls = _extract_tobeparsed_sources(payload)
            if source_urls:
                return source_urls
    except Exception as e:
        import traceback
        traceback.print_exc()

    # Fallback to regular GQL
    try:
        resp = client.post(ALLANIME_API, json={
            "query": EPISODE_GQL,
            "variables": variables,
        })
        if resp.status_code == 200:
            payload = resp.json()
            source_urls = _extract_tobeparsed_sources(payload)
            if not source_urls:
                d = payload.get("data", {})
                ep_data = d.get("episode") or {}
                source_urls = ep_data.get("sourceUrls") or []
    except Exception:
        pass

    return source_urls


def watch(slug, ep):
    ep_num = int(ep)

    # Step 1: Try direct showId
    show_id = slug
    source_urls = _fetch_episode_sources(show_id, ep_num)

    # Step 2: If no sources, try candidate resolution
    if not source_urls:
        # Get anime name for search
        search_query = slug
        try:
            show_data = _gql(SHOW_GQL, {"showId": slug})
            show = show_data.get("show")
            if show:
                search_query = (show.get("englishName") or show.get("name") or slug).strip()
        except Exception:
            pass

        # Search for candidates
        try:
            search_data = _gql(SEARCH_GQL, {
                "search": {"allowAdult": False, "allowUnknown": False, "query": search_query},
                "limit": 40,
                "page": 1,
                "translationType": "sub",
                "countryOrigin": "ALL",
            })
            edges = (search_data.get("shows") or {}).get("edges") or []

            if edges:
                ranked = _rank_candidates(search_query, ep_num, edges)

                for candidate in ranked:
                    cid = candidate["edge"].get("_id", "")
                    if cid == show_id:
                        continue  # Already tried this one

                    # Check episode coverage
                    sub_count = (candidate["edge"].get("availableEpisodes") or {}).get("sub", 0)
                    try:
                        sub_count = int(sub_count)
                    except (ValueError, TypeError):
                        sub_count = 0

                    if sub_count < ep_num:
                        continue  # Not enough episodes

                    source_urls = _fetch_episode_sources(cid, ep_num)
                    if source_urls:
                        show_id = cid
                        break
        except Exception:
            pass

    # Step 3: Resolve sources
    streams = _resolve_sources(source_urls)
    seen = set()
    unique_streams = []
    for s in streams:
        if s["url"] not in seen:
            seen.add(s["url"])
            unique_streams.append(s)

    # Sort: HLS first, then direct files, then embeds
    def _stream_sort_key(s):
        url = s["url"].lower()
        if s.get("isM3U8") or ".m3u8" in url:
            type_order = 0
        elif url.endswith(".mp4") or "mp4" in url.split("/")[-1]:
            type_order = 1
        else:
            type_order = 2
        q = s.get("quality", "auto")
        try:
            q_num = int(''.join(c for c in q if c.isdigit()) or '0')
        except ValueError:
            q_num = 0
        return (type_order, -q_num)

    unique_streams.sort(key=_stream_sort_key)

    return {
        "success": True,
        "slug": slug,
        "showId": show_id,
        "episode": ep_num,
        "sources": unique_streams,
        "streamUrl": unique_streams[0]["url"] if unique_streams else None,
        "isM3U8": unique_streams[0]["isM3U8"] if unique_streams else False,
    }


def popular(page=1):
    trend_key = min(7, (page - 1) % 4 + 1) if page > 1 else 7
    try:
        data = _gql(POPULAR_GQL, {
            "type": "anime",
            "size": 50,
            "allowAdult": False,
            "allowUnknown": False,
            "dateRange": 30 if page > 1 else trend_key,
        })
        recs = (data.get("queryPopular") or {}).get("recommendations") or []
        show_ids = list(set(
            r.get("pageStatus", {}).get("showId") or r.get("anyCard", {}).get("_id")
            for r in recs
            if (r.get("pageStatus", {}).get("showId") or r.get("anyCard", {}).get("_id"))
        ))

        if show_ids:
            shows_data = _gql(SHOWS_WITH_IDS_GQL, {"ids": show_ids[:50]})
            shows = shows_data.get("showsWithIds") or []
            results = [_parse_show(s) for s in shows]
            results = [r for r in results if r]
            return {"success": True, "page": page, "results": results[:24]}

        # Fallback
        search_data = _gql(SEARCH_GQL, {
            "search": {"allowAdult": False, "allowUnknown": False, "query": ""},
            "limit": 24,
            "page": page,
            "translationType": "sub",
            "countryOrigin": "JP",
        })
        edges = (search_data.get("shows") or {}).get("edges") or []
        results = [_parse_show(s) for s in edges]
        results = [r for r in results if r]
        return {"success": True, "page": page, "results": results}
    except Exception:
        return {"success": True, "page": page, "results": []}


def movies(page=1):
    data = _gql(SEARCH_GQL, {
        "search": {"allowAdult": False, "allowUnknown": False, "query": "movie"},
        "limit": 24,
        "page": page,
        "translationType": "sub",
        "countryOrigin": "ALL",
    })
    edges = (data.get("shows") or {}).get("edges") or []
    results = [_parse_show(s) for s in edges if s.get("type", "").lower() == "movie"]
    results = [r for r in results if r]
    return {"success": True, "page": page, "results": results}


def genre(genre_name, page=1):
    return search(genre_name, page)


def servers(slug, ep):
    result = watch(slug, ep)
    if result.get("success"):
        return {"success": True, "servers": result.get("sources", [])}
    return result
