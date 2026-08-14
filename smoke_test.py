"""Smoke test: exercises every view and the new sidebar toggle with AppTest.

Run: python -m pytest smoke_test.py (or: python smoke_test.py)
This is a throwaway QA harness, not committed as a permanent test.
"""
import streamlit as st
from streamlit.testing.v1 import AppTest


def run():
    failures = []

    def check(cond, msg):
        if not cond:
            failures.append(msg)

    def ss(key):
        try:
            return at.session_state[key]
        except KeyError:
            return None

    # 1. Boot the app (expanded sidebar)
    at = AppTest.from_file("app.py", default_timeout=90)
    at.run()
    check(not at.exception, f"app.py raised: {at.exception}")

    # Sidebar expanded: collapse control present
    check(
        any(b.key == "cm_collapse_sidebar_btn" for b in at.button),
        "collapse sidebar button missing",
    )
    check(
        not any(b.key == "cm_expand_sidebar_btn" for b in at.button),
        "expand button should be absent while expanded",
    )

    # 2. Click collapse -> sidebar state flips to collapsed
    at.button(key="cm_collapse_sidebar_btn").click().run()
    check(not at.exception, f"app.py raised after collapse: {at.exception}")
    check(
        ss("cm_sidebar_state") == "collapsed",
        f"sidebar state not collapsed: {ss('cm_sidebar_state')}",
    )
    check(
        any(b.key == "cm_expand_sidebar_btn" for b in at.button),
        "expand button missing while collapsed",
    )

    # 3. Click expand -> back to expanded
    at.button(key="cm_expand_sidebar_btn").click().run()
    check(not at.exception, f"app.py raised after expand: {at.exception}")
    check(ss("cm_sidebar_state") == "expanded", "sidebar not re-expanded")

    # 4. Navigation radio still works
    def nav_element():
        return next((r for r in at.radio if r.label == "Navigation Menu"), None)

    check(nav_element() is not None, "navigation radio missing")
    if nav_element() is not None:
        nav_element().set_value("AI Matcher").run()
        check(not at.exception, f"app.py raised on AI Matcher: {at.exception}")
        check(ss("active_page") == "Recommend", "nav did not route to Recommend")

        nav_element().set_value("My Watchlist").run()
        check(not at.exception, f"app.py raised on Watchlist: {at.exception}")
        check(ss("active_page") == "Watchlist", "nav did not route to Watchlist")

        nav_element().set_value("Architecture Info").run()
        check(not at.exception, f"app.py raised on About: {at.exception}")
        check(ss("active_page") == "About", "nav did not route to About")

        nav_element().set_value("Home Landing").run()
        check(not at.exception, f"app.py raised back on Home: {at.exception}")

    # 5. Card actions: ADD -> SAVED -> REMOVE (watchlist state untouched in logic)
    wl_btn = next((b for b in at.button if b.key == "row_Tren_0_wl_Spider-Man: Brand New Day"), None)
    check(wl_btn is not None, "watchlist toggle button missing on first card")
    if wl_btn is not None:
        wl_btn.click().run()
        check(not at.exception, f"app.py raised after ADD: {at.exception}")
        check(len(ss("watchlist")) == 1, f"watchlist should have 1 item, has {len(ss('watchlist') or [])}")
        saved = next((b for b in at.button if b.key == "row_Tren_0_wl_Spider-Man: Brand New Day"), None)
        check(saved is not None and "SAVED" in (saved.label or ""), f"saved button state wrong: {saved and saved.label}")
        saved.click().run()
        check(len(ss("watchlist")) == 0, "watchlist should be empty after remove")

    # 6. INFO spotlight + trailer flows
    info_btn = next((b for b in at.button if b.key == "row_Tren_0_details_Spider-Man: Brand New Day"), None)
    check(info_btn is not None, "INFO button missing")
    if info_btn is not None:
        info_btn.click().run()
        check(ss("selected_movie_details") is not None, "INFO did not open spotlight")
        spotlight_close = next((b for b in at.button if b.key == "spotlight_close_btn"), None)
        check(spotlight_close is not None, "spotlight close button missing")
        if spotlight_close is not None:
            spotlight_close.click().run()
            check(ss("selected_movie_details") is None, "spotlight did not close")

    play_btn = next((b for b in at.button if b.key == "row_Tren_1_play_The Odyssey"), None)
    check(play_btn is not None, "PLAY button missing")
    if play_btn is not None:
        play_btn.click().run()
        check(ss("active_trailer_movie") is not None, "PLAY did not open trailer")
        close_video = next((b for b in at.button if b.key == "close_trailer_player"), None)
        if close_video is not None:
            close_video.click().run()
            check(ss("active_trailer_movie") is None, "video player did not close")

    print("PASS" if not failures else "FAIL")
    for f in failures:
        print(" -", f)
    return failures


if __name__ == "__main__":
    raise SystemExit(1 if run() else 0)
