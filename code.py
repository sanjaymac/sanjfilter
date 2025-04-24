import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
from urllib.parse import urljoin, urlencode
from rapidfuzz import fuzz


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


def get_links_from_html(html: str, base_url: str, mode: str, fuzzy_filter: str = None) -> list:
    soup = BeautifulSoup(html, 'html.parser')
    links = set()

    # Prepare keywords for fuzzy matching
    keywords = []
    if fuzzy_filter:
        keywords = [kw.strip() for kw in re.split(r'[|,]', fuzzy_filter) if kw.strip()]

    for a in soup.find_all('a', href=True):
        href = a['href']
        full_link = urljoin(base_url, href)

        if mode == "Episode Links Only":
            if re.search(r'-episod-\d+', href):
                links.add(full_link)
        else:  # All Links
            if keywords:
                for kw in keywords:
                    score = fuzz.partial_ratio(href.lower(), kw.lower())
                    if score >= 80:
                        links.add(full_link)
                        break
            else:
                links.add(full_link)

    return list(links)


def get_paginated_links(base_url: str, max_pages: int, mode: str, fuzzy_filter: str = None) -> list:
    all_links = set()

    for page in range(1, max_pages + 1):
        if page == 1:
            paginated_url = base_url
        else:
            paginated_url = f"{base_url.rstrip('/')}/page/{page}/"

        try:
            html = fetch_page(paginated_url)
            page_links = get_links_from_html(html, base_url, mode, fuzzy_filter)
            if not page_links:
                break
            all_links.update(page_links)
        except requests.HTTPError:
            break
        except Exception as e:
            print(f"Error on page {page}: {e}")
            break

    return sorted(list(all_links))


def build_search_url(base_url: str, query: str) -> str:
    params = urlencode({'s': query})
    return f"{base_url.rstrip('/')}?{params}"


# --- Streamlit UI ---
st.set_page_config(page_title="Link Extractor Tool", layout="wide")
st.title("🔗 Multi-URL Link Extractor")
st.markdown(
    "Enter base URLs (one per line). This app scrapes either **all links**, **episode-based links**, or performs a **search** using a keyword from paginated or search result pages."
)

urls_input = st.text_area("🌐 Enter Base URLs", placeholder="https://example.com/category/curang-tanpa-niat/")
mode = st.radio(
    "🔍 What type of links do you want to extract?",
    ["Episode Links Only", "All Links", "Search with Keyword"]
)

max_pages = st.slider("📄 Max Pages per URL", 1, 100, 100)

search_query = None
fuzzy_filter = None
if mode == "Search with Keyword":
    search_query = st.text_input("🔎 Enter Search Keyword", placeholder="e.g. Honey Minta Maaf")
elif mode == "All Links":
    fuzzy_filter = st.text_input(
        "🧪 Optional Fuzzy Filter (80%+ match, e.g. `drive|mega|zippy`)",
        placeholder="Leave empty to get all links"
    )

if st.button("🚀 Fetch Links"):
    base_urls = [url.strip() for url in urls_input.strip().splitlines() if url.strip()]
    all_results = []

    with st.spinner("Scraping all URLs..."):
        for base_url in base_urls:
            try:
                # Determine which mode to use
                if mode == "Search with Keyword":
                    if not search_query:
                        st.warning("Please enter a search keyword to proceed.")
                        break
                    search_url = build_search_url(base_url, search_query)
                    html = fetch_page(search_url)
                    # Reuse 'All Links' logic for search results
                    links = get_links_from_html(html, base_url, "All Links", fuzzy_filter)
                else:
                    links = get_paginated_links(base_url, max_pages, mode, fuzzy_filter)

                for link in links:
                    all_results.append({
                        "Base URL": base_url,
                        "Link Found": link
                    })
            except Exception as e:
                all_results.append({
                    "Base URL": base_url,
                    "Link Found": f"Error: {e}"
                })

    if all_results:
        df = pd.DataFrame(all_results)
        st.subheader("📋 Extracted Links")
        st.dataframe(df, use_container_width=True)
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download CSV", data=csv, file_name="scraped_links.csv", mime="text/csv")
    else:
        st.warning("No links found.")
