import re
import os
import requests

from urllib.parse import urlparse
from bs4 import BeautifulSoup

RE_PODCAST_ID = re.compile(r"id(?P<id>[0-9]+)")
URLS_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "urls.txt"
)
FEEDS_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "feeds.txt"
)


def read_data_from_file(filename):
    if os.path.exists(filename):
        return set(line.strip() for line in open(filename).readlines())
    return set()


def write_data_to_file(filename, data):
    with open(filename, "w") as fp:
        fp.writelines("\n".join(data))


def parse_genre(genre_link, urls):
    print("GENRE", genre_link)
    content = requests.get(genre_link).text
    soup = BeautifulSoup(content, "lxml")

    hrefs = set(
        [
            link["href"]
            for link in soup.find_all("a", href=True)
            if link["href"].startswith("https://itunes.apple.com/us/podcast/")
            and link["href"] not in urls
        ]
    )

    print(len(hrefs), "new podcast links found")

    for href in hrefs:
        feed = get_podcast_feed(href)
        if feed:
            yield feed, href


def get_podcast_feed(url):
    path = urlparse(url).path.split("/")[-1]
    match = RE_PODCAST_ID.search(path)
    if match is None:
        return None
    podcast_id = match.group("id")
    data_url = "https://itunes.apple.com/lookup?id=" + podcast_id
    response = requests.get(data_url)
    if response.ok:
        json = response.json()
        for result in json.get("results", []):
            if "feedUrl" in result:
                return result["feedUrl"]
    return None


def do_parse():
    content = requests.get(
        "https://itunes.apple.com/us/genre/podcasts/id26?mt=2"
    ).text
    soup = BeautifulSoup(content, "lxml")
    urls = read_data_from_file(URLS_FILE)
    feeds = read_data_from_file(FEEDS_FILE)

    try:
        for link in soup.find_all("a", href=True):
            href = link["href"]
            if href.startswith("https://itunes.apple.com/us/genre/podcasts-"):
                for feed, url in parse_genre(href, urls):
                    feeds.add(feed)
                    urls.add(url)
    finally:

        write_data_to_file(URLS_FILE, urls)
        write_data_to_file(FEEDS_FILE, feeds)


if __name__ == "__main__":
    do_parse()
