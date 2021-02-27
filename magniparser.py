import requests
import bs4
import pymongo
import time

from urllib.parse import urljoin
import datetime as dt

MONTHS = {
    "янв": 1,
    "фев": 2,
    "мар": 3,
    "апр": 4,
    "май": 5,
    "мая": 5,
    "июн": 6,
    "июл": 7,
    "авг": 8,
    "сен": 9,
    "окт": 10,
    "ноя": 11,
    "дек": 12,
}


class MagnitParse:
    def __init__(self, start_url, db_client):
        self.start_url = start_url
        self.db = db_client["magnit"]

    @staticmethod
    def _get_response(url):
        response = requests.get(url)
        if response.status_code == 200:
            return response
        time.sleep(0.5)

    def _get_soup(self, url):
        response = self._get_response(url)
        soup = bs4.BeautifulSoup(response.text, "lxml")
        return soup

    def _template(self):
        return {
            "url": lambda a: urljoin(self.start_url, a.attrs.get("href")),
            "promo_name": lambda a: a.find("div", attrs={"class": "card-sale__header"}).text,
            "product_name": lambda a: a.find("div", attrs={"class": "card-sale__title"}).text,
            "old_price": lambda a: float(".".join(
                item for item in a.find("div", attrs={"class": "label__price_old"}).text.split())),
            "new_price": lambda a: float(".".join(
                item for item in a.find("div", attrs={"class": "label__price_new"}).text.split())
            ),
            "image_url": lambda a: urljoin(self.start_url, a.find("img").attrs.get("data-src")),
            "date_from": lambda a: self.__get_date(a.find("div", attrs={"class": "card-sale__date"}).text)[0],
            "date_to": lambda a: self.__get_date(a.find("div", attrs={"class": "card-sale__date"}).text)[1]

        }

    def run(self):
        soup = self._get_soup(self.start_url)
        catalog = soup.find("div", attrs={"class": "сatalogue__main"})
        for product_a in catalog.find_all("a", recursive=False):
            product_data = self._parse(product_a)
            self.save(product_data)

    def _parse(self, product_a) -> dict:
        product_data = {}
        for key, funk in self._template().items():
            try:
                product_data[key] = funk(product_a)
            except (AttributeError, ValueError, KeyError):
                pass
        return product_data

    def __get_date(self, product_date: str) -> list:
        split_date = product_date.replace("с ", "").replace("\n", "").split("до ")
        date_list = []
        try:
            if MONTHS[split_date[1].split()[1][:3]] < dt.datetime.now().month:
                year = dt.datetime.now().year - 1
            else:
                year = dt.datetime.now().year
        except IndexError:
            year = dt.datetime.now().year
        try:
            if MONTHS[split_date[0].split()[1][:3]] > MONTHS[split_date[1].split()[1][:3]]:
                start_year = dt.datetime.now().year - 1
            else:
                start_year = dt.datetime.now().year
        except KeyError:
            start_year = dt.datetime.now().year

        count = 0

        for date in split_date:
            count += 1
            date = date.split()
            date_list.append(
                dt.datetime(
                    year=start_year if count == 1 else year,
                    month=MONTHS[date[1][:3]],
                    day=int(date[0])
                            )
            )

        return date_list

    def save(self, data: dict):
        collection = self.db["magnit"]
        collection.insert_one(data)


if __name__ == "__main__":
    start_url = "https://magnit.ru/promo/"
    db_client = pymongo.MongoClient("mongodb://localhost:27017")
    parser = MagnitParse(start_url, db_client)
    parser.run()
