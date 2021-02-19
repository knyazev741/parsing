import requests
import json

from pathlib import Path
from time import sleep


class Parser:
    def __init__(self, url: str, path: Path):
        self.url = url
        self.path = path

    def _get_response(self, url, params):
        while True:
            response = requests.get(url=url, params=params)
            if response.status_code == 200:
                return response
            sleep(1)

    def run(self):
        response = requests.get(self.url)
        for r in response.json():
            id = r["parent_group_code"]
            name = r["parent_group_name"]
            self._parse(id, name)


    def _parse(self, id, name):
        url = "https://5ka.ru/api/v2/special_offers/"
        params = {"records_per_page": 12,
                  "page": 1,
                  "categories": id
                  }
        response = self._get_response(url=url, params=params)
        product_list = []

        while url:
            data = response.json()
            url = data["next"]
            try:
                response = requests.get(url)
            except:
                continue
            for product in data["results"]:
                product_list.append(product)

        data = [{"name": name, "code": id, "products": product_list}]
        save_path = self.path.joinpath(f"{id}.json")
        self._save(data, save_path)

    @staticmethod
    def _save(data, save_path):
        jdata = json.dumps(data, ensure_ascii=False)
        save_path.write_text(jdata, encoding="UTF-8")


if __name__ == "__main__":
    url = "https://5ka.ru/api/v2/categories/"
    path = Path(__file__).parent.joinpath("products")
    if not path.exists():
        path.mkdir()

    parser = Parser(url, path)
    parser.run()
