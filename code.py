import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse
import pandas as pd


def get_player_links(html: str) -> list:
    links = set()
    soup = BeautifulSoup(html, 'html.parser')

    for iframe in soup.find_all('iframe'):
        src = iframe.get('src')
        if src:
            links.add(src)

    for video in soup.find_all('video'):
        for source in video.find_all('source'):
            src = source.get('src')
            if src:
                links.add(src)

    for pattern in [r"https?://[^\s'\"]+\.m3u8", r"https?://[^\s'\"]+\.mp4"]:
        for match in re.findall(pattern, html):
            links.add(match)

    return list(links)


def get_episode_links_from_html(html: str, domain: str, slug: str) -> list:
    links = set()
    soup = BeautifulSoup(html, 'html.parser')
    for a in soup.find_all('a', href=True):
        href = a['href']
        full = href if href.startswith('http') else urljoin(domain, href)
        if full.startswith(f"{domain}{slug}-"):
            links.add(full)
    return list(links)


def get_all_paginated_episode_links(base_url: str, max_pages: int = 10) -> list:
    parsed = urlparse(base_url)
    domain = f"{parsed.scheme}://{parsed.netloc}"
    slug = parsed.path.rstrip('/')
    all_links = set()

    for page in range(1, max_pages + 1):
        paginated_url = f"{slug}/page/{page}/"
        full_url = urljoin(domain, paginated_url)
        try:
            html = fetch_page(full_url)
            episode_links = get_episode_links_from_html(html, domain, slug)
            if not episode_links:
                break
            all_links.update(episode_links)
        except requests.HTTPError:
            break
    return list(all_links)


def fetch_page(url: str, timeout: int = 10) -> str:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/115.0.0.0 Safari/537.36"
        )
    }
    resp = requests.get(url, headers=headers, timeout=timeout)
    resp.raise_for_status()
    return resp.text


# --- Streamlit App ---
st.title("🎬 Streaming Page Scraper")
st.markdown("Enter a streaming page URL to extract player and episode links.")

base_url = st.text_input("🔗 Base URL", "https://nonton9.cfd/curang-tanpa-niat/")
max_pages = st.slider("📄 Max Pages to Search", 1, 20, 10)

if st.button("Scrape"):
    try:
        with st.spinner("Fetching base page..."):
            html = fetch_page(base_url)

        # Player links from first page
        player_links = get_player_links(html)
        st.subheader("📺 Player Links (First Page)")
        if player_links:
            st.dataframe(pd.DataFrame(player_links, columns=["Player Link"]))
        else:
            st.info("No player links found.")

        # Episode links across pagination
        episode_links = get_all_paginated_episode_links(base_url, max_pages)
        st.subheader("🎞️ Episode Links (Paginated)")
        if episode_links:
            st.dataframe(pd.DataFrame(episode_links, columns=["Episode Link"]))
        else:
            st.info("No episode links found.")

    except Exception as e:
        st.error(f"Error: {e}")
