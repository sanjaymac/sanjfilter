import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
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


def extract_all_links_from_html(html: str, base_url: str) -> list:
    soup = BeautifulSoup(html, 'html.parser')
    links = set()
    for a in soup.find_all('a', href=True):
        full_url = urljoin(base_url, a['href'])
        links.add(full_url)
    return list(links)


def scrape_all_paginated_links(base_url: str, max_pages: int = 100) -> list:
    all_links = set()

    for page in range(1, max_pages + 1):
        if page == 1:
            paginated_url = base_url
        else:
            paginated_url = f"{base_url.rstrip('/')}/page/{page}/"

        try:
            html = fetch_page(paginated_url)
            links = extract_all_links_from_html(html, base_url)
            if not links:
                break
            all_links.update(links)
        except requests.HTTPError:
            break
        except Exception as e:
            print(f"Error on page {page}: {e}")
            break

    return sorted(list(all_links))


# --- Streamlit UI ---
st.set_page_config(page_title="All Link Extractor", layout="wide")
st.title("🌐 All-Link Extractor from Multiple URLs")
st.markdown("Enter multiple URLs (one per line). The app will extract **all anchor links** (`<a href>`) from up to 100 pages of each URL.")

urls_input = st.text_area("🔗 Enter Base URLs", placeholder="https://example.com/page/\nhttps://another-site.com/")
max_pages = st.slider("📄 Max Pages per URL", 1, 100, 100)

if st.button("Fetch All Links"):
    base_urls = [url.strip() for url in urls_input.strip().splitlines() if url.strip()]
    all_results = []

    with st.spinner("Scraping all URLs..."):
        for base_url in base_urls:
            try:
                links = scrape_all_paginated_links(base_url, max_pages)
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
        st.subheader("🔗 All Extracted Links")
        st.dataframe(df, use_container_width=True)
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download CSV", data=csv, file_name="all_links.csv", mime="text/csv")
    else:
        st.warning("No links found.")
