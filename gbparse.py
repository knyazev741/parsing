import requests
import bs4
import logging

from time import sleep
from urllib.parse import urljoin
from database.db import Database

logging.basicConfig(level=logging.DEBUG)


class GBParse:
    def __init__(self, start_url, db_url):
        self.db_url = db_url
        self.start_url = start_url
        self.done_urls = set()
        self.tasks = []
        self.done_urls.add(self.start_url)

    def _get_task(self, url, callback):
        def task():
            soup = self._get_soup(url)
            return callback(url, soup)

        return task

    def _parse_feed(self, url, soup):
        ul = soup.find("ul", attrs={"class": "gb__pagination"})
        all_urls = set(urljoin(url,
                               href.attrs.get("href"))
                       for href in ul.find_all("a") if href.attrs.get("href"))
        for urls in all_urls:
            if urls not in self.done_urls:
                self.done_urls.add(urls)
                self.tasks.append(self._get_task(urls, self._parse_feed))

        div = soup.find("div", attrs={"class": "post-items-wrapper"})
        all_urls_post = set(urljoin(url,
                                    href.attrs.get("href"))
                            for href in div.find_all("a") if href.attrs.get("href"))
        for urls in all_urls_post:
            if urls not in self.done_urls:
                self.done_urls.add(urls)
                self.tasks.append(self._get_task(urls, self._parse_content))

    def _parse_content(self, url, soup):
        data = {"post_data": {
            "url": url,
            "id": soup.find("comments").attrs.get("commentable-id"),
            "title": soup.find("h1", attrs={"itemprop": "headline"}).text,
            "first_img": soup.find("img").attrs.get("src"),
            "publish_date": soup.find("div",
                                      attrs={"class": "blogpost-date-views"}).find("time").attrs.get("datetime")},
            "author": {
                "author_name": soup.find("div", attrs={"itemprop": "author"}).text,
                "author_url": urljoin(self.start_url,
                                      soup.find("div", attrs={"itemprop": "author"}).parent.attrs.get("href"))},
            "tags": [{"name": tag.text, "url": urljoin(self.start_url, tag.attrs.get("href"))}
                     for tag in soup.find_all("a", attrs={"class": "small"})],
            "comments": self._get_comments(soup)}

        return data

    @staticmethod
    def _get_comments(soup):
        params = {
            "commentable_type": "Post",
            "commentable_id": soup.find("comments").attrs.get("commentable-id"),
            "order": "desc"
        }
        resp = requests.get(url="https://geekbrains.ru/api/v2/comments?", params=params)
        if resp.json():
            comments = [{
                "post_id": soup.find("comments").attrs.get("commentable-id"),
                "author_name": element["comment"]["user"]["full_name"],
                "author_url": element["comment"]["user"]["url"],
                "text": element["comment"]["body"],
                "id": element["comment"]["id"],
                "parent_id": element["comment"]["parent_id"]
            } for element in resp.json()]
            for element in resp.json():
                try:
                    for children in element["comment"]["children"]:
                        comments.append({
                            "post_id": soup.find("comments").attrs.get("commentable-id"),
                            "author_name": children["comment"]["user"]["full_name"],
                            "author_url": children["comment"]["user"]["url"],
                            "text": children["comment"]["body"],
                            "id": children["comment"]["id"],
                            "parent_id": children["comment"]["parent_id"]
                        })
                except KeyError:
                    continue
            return comments

    @staticmethod
    def _get_response(url):
        while True:
            response = requests.get(url)
            if response.status_code == 200:
                return response
            sleep(1)

    def _get_soup(self, url):
        soup = bs4.BeautifulSoup(self._get_response(url).text, "lxml")
        return soup

    def run(self):
        self.tasks.append(self._get_task(self.start_url, self._parse_feed))
        for task in self.tasks:
            result = task()
            if isinstance(result, dict):
                Database(self.db_url).create_post(result)


if __name__ == "__main__":
    url = "https://geekbrains.ru/posts"
    db_url = "sqlite:///gbparses"
    parser = GBParse(url, db_url)
    parser.run()
