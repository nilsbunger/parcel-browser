import logging
import random
import re
from collections import defaultdict
from urllib.parse import urljoin

import scrapy
from scraper_api import ScraperAPIClient
from scrapy.crawler import CrawlerProcess

from mygeo.settings import env
from world.models import PropertyListing

client = ScraperAPIClient(env('SCRAPER_API_KEY'))


# See also example in https://docs.scrapy.org/en/latest/topics/item-pipeline.html for more customization
class MyItemPipeline:

    def __init__(self, stats):
        self.stats = stats

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.stats)

    def process_item(self, item, spider):
        del item['listing_url']  # listing URL is not stable between passes, so don't consider it in get_or_creating.
        property, created = PropertyListing.objects.get_or_create(
            **item, status=PropertyListing.ListingStatus.ACTIVE
        )
        if (created):
            # object with same parameters (price / etc) not found, so record this instance
            property.clean()
            property.save()
            self.stats.inc_value('listing/new_or_update')
        else:
            # Property WITH these parameters seen, so update the "seendate" (which is automatic)
            property.save(update_fields=['seendate'])
            self.stats.inc_value('listing/no_change')


class SanDiegoMlsSpider(scrapy.Spider):
    name = 'mls'

    def __init__(self, zip_groups, localhost_mode, **kwargs):
        self.zip_groups = zip_groups
        self.localhost_mode = localhost_mode
        logger = logging.getLogger('scrapy.core.scraper')
        logger.setLevel(logging.INFO)
        super().__init__(**kwargs)

    def start_requests(self):
        headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:48.0) Gecko/20100101 Firefox/48.0'}
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_3) AppleWebKit/537.36 (KHTML, '
                                 'like Gecko) Chrome/99.0.4844.84 Safari/537.36'}
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 12_5) AppleWebKit/605.1.15 (KHTML, '
                                 'like Gecko) Version/15.6 Safari/605.1.15'}
        # yield scrapy.Request('https://slashdot.org', headers=headers)
        for zips in self.zip_groups:
            url = self.san_diego_listings_url(zips)
            orig_url = url
            if not self.localhost_mode:
                # wrap URL in cloud proxy from scraperapi.com
                url = client.scrapyGet(url)
            yield scrapy.Request(url, headers=headers, cb_kwargs={'orig_url': orig_url})

    name_subs = {
        'Beds': 'br',
        'Baths': 'ba',
        'SqFt.': 'size',
        'MLS': 'mlsid',
    }

    def parse(self, response, orig_url=None):

        for listing in response.css('div.row.results'):
            listing_data = defaultdict()
            listing_data['thumbnail'] = listing.css('.property-thumb img::attr(src)').get()
            listing_data['listing_url'] = listing.css('a::attr(href)').get()
            addr = listing.css('.address::text').get().split(',')[0]
            price = listing.css('.price::text').get().strip()
            price = int(re.sub(r'[\$,]', '', price))
            listing_data['price'] = price
            listing_data['addr'] = addr
            # extract BR, BA, MLS #, and sq ft:
            for detail in listing.css(".featured-details .detail"):
                detail_name = detail.css('.detail-title::text').get()
                detail_value = re.sub(r',', '', detail.css('.number::text').get())
                if detail_name != 'MLS':
                    detail_value = int(detail_value)
                listing_data[self.name_subs[detail_name]] = detail_value
            yield listing_data

        next_url = response.css('.pagination a[rel="next"]::attr(href)').get()
        if next_url:
            url = urljoin(orig_url, next_url)
            orig_url = url
            if not self.localhost_mode:
                # wrap URL in cloud proxy from scraperapi.com
                url = client.scrapyGet(url)
            print("*** NEW URL ***")
            print(url)

            yield scrapy.Request(url, self.parse, cb_kwargs={'orig_url': orig_url})

    def san_diego_listings_url(self, zips: [int]):
        """ Generate a URL to query listings from homesalessandiego.com in a range of zipcodres"""
        hostname = 'http://localhost:8000/' if self.localhost_mode else 'https://www.homesalessandiego.com/'
        path = 'search/results/mrys/'
        try:
            zip_string = '&'.join([f'zip={zip}' for zip in zips])
        except Exception as e:
            print(e)
            print("Uh oh")
        query_params = 'type=res&type=mul&list_price_min=50000&list_price_max=3000000&' \
                       'beds_min=1&baths_min=1&area_min=all&lot_size_range=all' \
                       '&view=all&parking_spaces_total_min=all&year_built_min=all&pool=all&stories=all&hoa=all&' \
                       'age_restriction=all&short_sale=all&foreclosure=all&elementary_school=all&middle_school=all&''' \
                       'high_school=all&terms=all'
        url = hostname + path + '?' + zip_string + '&' + query_params
        if self.localhost_mode:
            # don't cache in localhost mode, for testing
            url += "&cachebust=" + str(random.randrange(999999999))
        return url


def scrape_san_diego_listings_by_zip_groups(zip_groups, localhost_mode, cache=True):
    download_delay = 2.0 if localhost_mode else 25
    crawl_settings = {
        "ITEM_PIPELINES": {
            'lib.scraping_lib.MyItemPipeline': 100,
        },
        "COOKIES_ENABLED": False,
        'DOWNLOAD_DELAY': download_delay,  # Delay in seconds between pages (with randomized jitter)
        "HTTPCACHE_ENABLED": cache,
        "HTTPCACHE_STORAGE": 'scrapy.extensions.httpcache.FilesystemCacheStorage',
        "HTTPCACHE_POLICY": 'scrapy.extensions.httpcache.DummyPolicy',
        "MIDDLEWARE": {
            'scrapy.downloadermiddlewares.httpcache.HttpCacheMiddleware',
        },
        'AUTOTHROTTLE_ENABLED': True,
        'CONCURRENT_REQUESTS': 1,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
        'DOWNLOAD_TIMEOUT': 60
    }
    process = CrawlerProcess(settings=crawl_settings)
    crawler = process.create_crawler(SanDiegoMlsSpider)
    process.crawl(crawler, zip_groups=zip_groups, localhost_mode=localhost_mode)
    process.start(stop_after_crawl=True)
    return crawler.stats
