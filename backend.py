from flask import Flask, render_template, request, jsonify, send_file
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import os

app = Flask(__name__)

def crawl_website(url, depth, visited=None):
    if visited is None:
        visited = set()

    if depth == 0 or url in visited:
        return [], []

    visited.add(url)
    internal_links = set()
    external_links = set()

    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')

        for link in soup.find_all('a', href=True):
            href = link['href']
            full_url = urljoin(url, href)
            parsed_href = urlparse(full_url)
            parsed_url = urlparse(url)

            if parsed_href.netloc == parsed_url.netloc:
                internal_links.add(full_url)
            else:
                external_links.add(full_url)

        for link in internal_links.copy():
            i_links, e_links = crawl_website(link, depth - 1, visited)
            internal_links.update(i_links)
            external_links.update(e_links)

    except Exception as e:
        print(f"Error crawling {url}: {e}")

    return list(internal_links), list(external_links)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/crawl', methods=['POST'])
def crawl():
    data = request.get_json()
    url = data.get('url')
    depth = int(data.get('depth', 1))

    internal_links, external_links = crawl_website(url, depth)

    with open('crawled_links.txt', 'w', encoding='utf-8') as f:
        for link in internal_links + external_links:
            f.write(link + '\n')

    return jsonify({
        'internal_links': internal_links,
        'external_links': external_links
    })


@app.route('/download')
def download_file():
    if os.path.exists('crawled_links.txt'):
        return send_file('crawled_links.txt', as_attachment=True)
    return "File not found", 404


if __name__ == '__main__':
    app.run(debug=True)

