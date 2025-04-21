import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse


def get_player_links(html: str) -> set:
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

    return links


def get_episode_links_from_html(html: str, domain: str, slug: str) -> set:
    links = set()
    soup = BeautifulSoup(html, 'html.parser')
    for a in soup.find_all('a', href=True):
        href = a['href']
        full = href if href.startswith('http') else urljoin(domain, href)
        if full.startswith(f"{domain}{slug}-"):
            links.add(full)
    return links


def get_all_paginated_episode_links(base_url: str, max_pages: int = 10) -> set:
    parsed = urlparse(base_url)
    domain = f"{parsed.scheme}://{parsed.netloc}"
    slug = parsed.path.rstrip('/')
    all_links = set()

    for page in range(1, max_pages + 1):
        paginated_url = f"{slug}/page/{page}/"
        full_url = urljoin(domain, paginated_url)
        try:
            print(f"Fetching: {full_url}")
            html = fetch_page(full_url)
            episode_links = get_episode_links_from_html(html, domain, slug)
            if not episode_links:
                break  # Stop if no more links found
            all_links.update(episode_links)
        except requests.HTTPError as e:
            print(f"Stopped at page {page}: {e}")
            break
    return all_links


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


if __name__ == '__main__':
    base_url = 'https://nonton9.cfd/curang-tanpa-niat/'
    html = fetch_page(base_url)

    player_links = get_player_links(html)
    if player_links:
        print("Player links found:")
        for link in sorted(player_links):
            print(link)
    else:
        print("No player links found on the first page.")

    episode_links = get_all_paginated_episode_links(base_url, max_pages=10)
    if episode_links:
        print("\nAll episode links across pagination:")
        for link in sorted(episode_links):
            print(link)
    else:
        print("No episode links found across pages.")
