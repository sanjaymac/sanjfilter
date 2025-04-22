import streamlit as st
import requests
from bs4 import BeautifulSoup
import regex as re
import pandas as pd
from urllib.parse import urljoin


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


def get_links_from_html(html: str, base_url: str, mode: str, regex_filter: str = None) -> list:
    soup = BeautifulSoup(html, 'html.parser')
    links = set()
    for a in soup.find_all('a', href=True):
        href = a['href']
        full_link = urljoin(base_url, href)

        if mode == "Episode Links Only":
            if re.search(r'-episod-\d+', href):
                links.add(full_link)
        else:  # All Links
            if regex_filter:
                try:
                    # Fuzzy match with max cost = 1 (tweak as needed)
                    if re.search(f"({regex_filter}){{e<=1}}", href, flags=re.IGNORECASE):
                        links.add(full_link)
                except Exception as e:
                    print(f"Regex error: {e}")
            else:
                links.add(full_link)
    return list(links)



def get_paginated_links(base_url: str, max_pages: int, mode: str, regex_filter: str = None) -> list:
    all_links = set()

    for page in range(1, max_pages + 1):
        if page == 1:
            paginated_url = base_url
        else:
            paginated_url = f"{base_url.rstrip('/')}/page/{page}/"

        try:
            html = fetch_page(paginated_url)
            page_links = get_links_from_html(html, base_url, mode, regex_filter)
            if not page_links:
                break
            all_links.update(page_links)
        except requests.HTTPError:
            break
        except Exception as e:
            print(f"Error on page {page}: {e}")
            break

    return sorted(list(all_links))


# --- Streamlit UI ---
st.set_page_config(page_title="Link Extractor Tool", layout="wide")
st.title("🔗 Multi-URL Link Extractor")
st.markdown("Enter base URLs (one per line). This app scrapes either **all links** or **episode-based links** from paginated content.")

urls_input = st.text_area("🌐 Enter Base URLs", placeholder="https://v-myflm4u.com/category/curang-tanpa-niat/")
mode = st.radio("🔍 What type of links do you want to extract?", ["Episode Links Only", "All Links"])
max_pages = st.slider("📄 Max Pages per URL", 1, 100, 100)

regex_filter = None
if mode == "All Links":
    regex_filter = st.text_input("🧪 Optional Regex Filter (e.g. `drive|mega|zippy`)", placeholder="Leave empty to get all links")

if st.button("🚀 Fetch Links"):
    base_urls = [url.strip() for url in urls_input.strip().splitlines() if url.strip()]
    all_results = []

    with st.spinner("Scraping all URLs..."):
        for base_url in base_urls:
            try:
                links = get_paginated_links(base_url, max_pages, mode, regex_filter)
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
