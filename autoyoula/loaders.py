from scrapy.loader import ItemLoader
from scrapy import Selector
from itemloaders.processors import TakeFirst, MapCompose


def clear_price(item):
    item = item.replace("\u2009", "")
    return item


def get_characteristics(item):
    selector = Selector(text=item)
    data = {
        "label": selector.xpath("//div[contains(@class, 'AdvertSpecs_label')]/text()").extract_first(),
        "value": selector.xpath("//div[contains(@class, 'AdvertSpecs_data')]//text()").extract_first()
    }
    return data


class AutoYoulaLoader(ItemLoader):
    default_item_class = dict
    url_out = TakeFirst()
    author_out = TakeFirst()
    title_out = TakeFirst()
    price_in = MapCompose(clear_price)
    price_out = TakeFirst()
    characteristics_in = MapCompose(get_characteristics)
    description_out = TakeFirst()


