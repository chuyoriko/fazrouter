"""Full test suite for all 4 providers"""
import sys, json, time

def test(name, fn):
    try:
        start = time.time()
        result = fn()
        elapsed = time.time() - start
        return {"provider": name, "status": "PASS", "time": f"{elapsed:.1f}s", "data": result}
    except Exception as e:
        return {"provider": name, "status": "FAIL", "error": str(e)[:200]}

results = []

# === HI-ANIME ===
print("=== HI-ANIME ===")
import asyncio
from hianime_api_internal import HiAnimeClient

async def test_hianime():
    h = HiAnimeClient()
    await h.start()
    try:
        r = await h.home()
        results.append({"provider": "hianime", "endpoint": "/home", "status": "PASS", "detail": f"latest={len(r.get('latest',[]))}"})
    except Exception as e:
        results.append({"provider": "hianime", "endpoint": "/home", "status": "FAIL", "detail": str(e)[:100]})

    try:
        r = await h.search("slime")
        results.append({"provider": "hianime", "endpoint": "/search?q=slime", "status": "PASS", "detail": f"results={len(r.get('results',[]))}"})
    except Exception as e:
        results.append({"provider": "hianime", "endpoint": "/search", "status": "FAIL", "detail": str(e)[:100]})

    try:
        r = await h.anime_detail("that-time-i-got-reincarnated-as-a-slime-season-4")
        d = r.get("data", {})
        results.append({"provider": "hianime", "endpoint": "/anime/{slug}", "status": "PASS", "detail": f"title={d.get('title','')} eps={d.get('total_episodes',0)}"})
    except Exception as e:
        results.append({"provider": "hianime", "endpoint": "/anime/{slug}", "status": "FAIL", "detail": str(e)[:100]})

    try:
        r = await h.watch("that-time-i-got-reincarnated-as-a-slime-season-4", "ep-1")
        d = r.get("data", {})
        v = d.get("video", {})
        q = v.get("qualities", [])
        results.append({"provider": "hianime", "endpoint": "/watch/{slug}/{ep}", "status": "PASS", "detail": f"video_id={v.get('video_id','')} qualities={len(q)}"})
    except Exception as e:
        results.append({"provider": "hianime", "endpoint": "/watch/{slug}/{ep}", "status": "FAIL", "detail": str(e)[:100]})

    try:
        r = await h.stream("37086faf8067c880")
        q = r.get("qualities", [])
        results.append({"provider": "hianime", "endpoint": "/stream/{videoid}", "status": "PASS", "detail": f"qualities={len(q)}"})
    except Exception as e:
        results.append({"provider": "hianime", "endpoint": "/stream/{videoid}", "status": "FAIL", "detail": str(e)[:100]})

    try:
        r = await h.popular()
        results.append({"provider": "hianime", "endpoint": "/popular", "status": "PASS", "detail": f"results={len(r.get('results',[]))}"})
    except Exception as e:
        results.append({"provider": "hianime", "endpoint": "/popular", "status": "FAIL", "detail": str(e)[:100]})

    try:
        r = await h.movies()
        results.append({"provider": "hianime", "endpoint": "/movie", "status": "PASS", "detail": f"results={len(r.get('results',[]))}"})
    except Exception as e:
        results.append({"provider": "hianime", "endpoint": "/movie", "status": "FAIL", "detail": str(e)[:100]})

    try:
        r = await h.genre("isekai")
        results.append({"provider": "hianime", "endpoint": "/genre/isekai", "status": "PASS", "detail": f"results={len(r.get('results',[]))}"})
    except Exception as e:
        results.append({"provider": "hianime", "endpoint": "/genre/isekai", "status": "FAIL", "detail": str(e)[:100]})

    await h.stop()

asyncio.run(test_hianime())

# === ANIMEPAHE ===
print("\n=== ANIMEPAHE ===")
import animepahe as pa

def test_pahe():
    try:
        r = pa.search("slime")
        results.append({"provider": "animepahe", "endpoint": "/search?q=slime", "status": "PASS", "detail": f"results={len(r.get('results',[]))}"})
    except Exception as e:
        results.append({"provider": "animepahe", "endpoint": "/search", "status": "FAIL", "detail": str(e)[:100]})

    try:
        r = pa.home()
        results.append({"provider": "animepahe", "endpoint": "/home", "status": "PASS", "detail": f"latest={len(r.get('latest',[]))}"})
    except Exception as e:
        results.append({"provider": "animepahe", "endpoint": "/home", "status": "FAIL", "detail": str(e)[:100]})

    try:
        r = pa.anime_detail("demon-slayer-kimetsu-no-yaiba")
        results.append({"provider": "animepahe", "endpoint": "/anime/{slug}", "status": "PASS", "detail": f"title={r.get('title','')} eps={r.get('total_episodes',0)}"})
    except Exception as e:
        results.append({"provider": "animepahe", "endpoint": "/anime/{slug}", "status": "FAIL", "detail": str(e)[:100]})

    try:
        r = pa.episode_watch("demon-slayer-kimetsu-no-yaiba")
        results.append({"provider": "animepahe", "endpoint": "/watch/{slug}", "status": "PASS", "detail": f"servers={len(r.get('servers',[]))}"})
    except Exception as e:
        results.append({"provider": "animepahe", "endpoint": "/watch/{slug}", "status": "FAIL", "detail": str(e)[:100]})

    for ep in ["/popular", "/movie", "/genre/isekai"]:
        fn_map = {"/popular": pa.popular, "/movie": pa.movies, "/genre/isekai": lambda: pa.genre("isekai")}
        try:
            r = fn_map[ep]()
            results.append({"provider": "animepahe", "endpoint": ep, "status": "PASS", "detail": f"results={len(r.get('results',[]))}"})
        except Exception as e:
            results.append({"provider": "animepahe", "endpoint": ep, "status": "FAIL", "detail": str(e)[:100]})

    try:
        r = pa.anime_list()
        results.append({"provider": "animepahe", "endpoint": "/anime-list", "status": "PASS", "detail": f"results={len(r.get('results',[]))}"})
    except Exception as e:
        results.append({"provider": "animepahe", "endpoint": "/anime-list", "status": "FAIL", "detail": str(e)[:100]})

    try:
        r = pa.new_season()
        results.append({"provider": "animepahe", "endpoint": "/new-season", "status": "PASS", "detail": f"results={len(r.get('results',[]))}"})
    except Exception as e:
        results.append({"provider": "animepahe", "endpoint": "/new-season", "status": "FAIL", "detail": str(e)[:100]})

test_pahe()

# === MAID ===
print("\n=== MAID ===")
import maid as md

for ep in [
    ("/search?q=one+piece", lambda: md.search("one piece")),
    ("/home", md.home),
    ("/manga/one-piece", lambda: md.manga_detail("one-piece")),
    ("/chapter/one-piece-1162", lambda: md.chapter_read("one-piece-chapter-1162-bahasa-indonesia")),
]:
    name, fn = ep
    try:
        r = fn()
        detail = ""
        if "results" in r:
            detail = f"results={len(r['results'])}"
        elif "latest" in r:
            detail = f"latest={len(r['latest'])}"
        elif "chapters" in r:
            detail = f"title={r.get('title','')[:30]} ch={r.get('total_chapters',0)}"
        elif "images" in r:
            detail = f"title={r.get('title','')[:30]} images={len(r['images'])}"
        results.append({"provider": "maid", "endpoint": name, "status": "PASS", "detail": detail})
    except Exception as e:
        results.append({"provider": "maid", "endpoint": name, "status": "FAIL", "detail": str(e)[:100]})

# === KOMIKPEDIA ===
print("\n=== KOMIKPEDIA ===")
import komikpedia as kp

for ep in [
    ("/search?q=one+piece", lambda: kp.search("one piece")),
    ("/home", kp.home),
    ("/manga/one-piece", lambda: kp.manga_detail("komik-one-piece-indo")),
    ("/read/chapter", lambda: kp.chapter_read("komik-one-piece-indo", "one-piece-chapter-1188")),
]:
    name, fn = ep
    try:
        r = fn()
        detail = ""
        if "results" in r:
            detail = f"results={len(r['results'])}"
        elif "latest" in r:
            detail = f"latest={len(r['latest'])}"
        elif "chapters" in r:
            detail = f"title={r.get('title','')} ch={r.get('total_chapters',0)}"
        elif "images" in r:
            detail = f"title={r.get('title','')[:30]} images={len(r['images'])}"
        results.append({"provider": "komikpedia", "endpoint": name, "status": "PASS", "detail": detail})
    except Exception as e:
        results.append({"provider": "komikpedia", "endpoint": name, "status": "FAIL", "detail": str(e)[:100]})

# === PRINT REPORT ===
print("\n" + "="*80)
print("FINAL TEST REPORT")
print("="*80)
total = len(results)
passed = sum(1 for r in results if r["status"] == "PASS")
failed = total - passed

for r in results:
    icon = "PASS" if r["status"] == "PASS" else "FAIL"
    print(f"[{icon}] {r['provider']:12s} {r['endpoint']:25s} | {r.get('detail','')}")

print(f"\nTOTAL: {passed}/{total} passed, {failed} failed")

with open("test_report.json", "w") as f:
    json.dump({"total": total, "passed": passed, "failed": failed, "results": results}, f, indent=2)

print("Report saved to test_report.json")
