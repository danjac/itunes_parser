import re
import os
import requests

from urllib.parse import urlparse
from bs4 import BeautifulSoup

RE_PODCAST_ID = re.compile(r"id(?P<id>[0-9]+)")


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
        urls.add(href)
        feed = get_podcast_feed(href)
        if feed:
            yield feed


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
    urls = set()

    if os.path.exists("./urls.txt"):
        urls = set(
            url.strip() for url in open("./urls.txt").read().split("\n")
        )

    feeds_fp = open("./feeds.txt", "a")

    try:
        for link in soup.find_all("a", href=True):
            href = link["href"]
            if href.startswith("https://itunes.apple.com/us/genre/podcasts-"):
                for feed in parse_genre(href, urls):
                    feeds_fp.write(feed + "\r\n")
    finally:
        feeds_fp.close()

        with open("./urls.txt", "w") as urls_fp:
            for url in urls:
                urls_fp.write(url + "\r\n")


if __name__ == "__main__":
    do_parse()
