import scrapy
import re
import pymongo


class AutoYoulaSpider(scrapy.Spider):
    name = 'autoyoula'
    allowed_domains = ['auto.youla.ru']
    start_urls = ['https://auto.youla.ru/']

    def __init__(self):
        super().__init__()
        self.db_client = pymongo.MongoClient("mongodb://localhost:27017")

    def parse(self, response, *args, **kwargs):
        for sl in response.css('.blackLink'):
            link = sl.attrib.get("href")
            yield response.follow(link, callback=self.brand_parse)

    def brand_parse(self, response, *args, **kwargs):
        for sl in response.css("div.Paginator_block__2XAPy a.Paginator_button__u1e7D"):
            link = sl.attrib.get("href")
            yield response.follow(link, callback=self.brand_parse)

        for sl in response.css("div.SerpSnippet_snippetContent__d8CHK div.SerpSnippet_titleWrapper__38bZM a.blackLink"):
            link = sl.attrib.get("href")
            yield response.follow(link, callback=self.car_parse)

    @staticmethod
    def get_author(response):
        marker = 'window.transitState = decodeURIComponent'
        for script in response.css("script"):
            try:
                if marker in script.css("::text").extract_first():
                    re_pattern = re.compile(r"youlaId%22%2C%22([a-zA-Z|\d]+)%22%2C%22avatar")
                    result = re.findall(re_pattern, script.css("::text").extract_first())
                    return response.urljoin(f"/user/{result[0]}").replace("auto.", "") if result else None
            except TypeError:
                continue

    def car_parse(self, response, *args, **kwargs):
        data = {
            "title": response.css
            ("div.AdvertCard_topAdvertHeaderInfo__OiPAZ .AdvertCard_advertTitle__1S1Ak::text").extract_first(),
            "price": response.css(".AdvertCard_price__3dDCr::text").extract_first().replace("\u2009", ""),
            "char": [dict(label=resp.css(".AdvertSpecs_label__2JHnS::text").get(),
                          data=resp.css(".AdvertSpecs_data__xK2Qx::text").get() or
                               resp.css(".AdvertSpecs_data__xK2Qx a::text").get())
                     for resp in response.css(".AdvertSpecs_row__ljPcX")],
            "caption": response.css(".AdvertCard_descriptionInner__KnuRi::text").extract_first(),
            "author": self.get_author(response)
        }
        self.db_client["autoyola"][self.name].insert_one(data)
