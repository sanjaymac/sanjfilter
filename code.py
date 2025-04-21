import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse
import pandas as pd


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


def get_episode_links_from_html(html: str, domain: str, slug: str) -> list:
    links = set()
    soup = BeautifulSoup(html, 'html.parser')
    for a in soup.find_all('a', href=True):
        href = a['href']
        full = href if href.startswith('http') else urljoin(domain, href)
        if full.startswith(f"{domain}{slug}-"):
            links.add(full)
    return list(links)


def get_paginated_episode_links(base_url: str, max_pages: int = 100) -> list:
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
        except Exception:
            break
    return list(all_links)


# --- Streamlit UI ---
st.title("📡 Multi-URL Episode Link Extractor")
st.markdown("Enter multiple base URLs (one per line). The app will extract episode links up to 100 pages per base URL.")

urls_input = st.text_area("🔗 Enter Base URLs", placeholder="https://example.com/show1/\nhttps://example.com/show2/")
max_pages = st.slider("📄 Max Pages per URL", 1, 100, 100)

if st.button("Fetch Episode Links"):
    base_urls = [url.strip() for url in urls_input.strip().splitlines() if url.strip()]
    all_results = []

    with st.spinner("Scraping all URLs..."):
        for base_url in base_urls:
            try:
                episode_links = get_paginated_episode_links(base_url, max_pages)
                for link in episode_links:
                    all_results.append({
                        "Base URL": base_url,
                        "Fetched Link": link
                    })
            except Exception as e:
                all_results.append({
                    "Base URL": base_url,
                    "Fetched Link": f"Error: {e}"
                })

    if all_results:
        df = pd.DataFrame(all_results)
        st.subheader("🔍 Extracted Episode Links")
        st.dataframe(df, use_container_width=True)
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download CSV", data=csv, file_name="episode_links.csv", mime="text/csv")
    else:
        st.warning("No links found.")
