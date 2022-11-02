from collections import defaultdict
import logging
import random
import re
import traceback
from urllib.parse import urljoin

from django.core.exceptions import MultipleObjectsReturned
from scraper_api import ScraperAPIClient
import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.exceptions import CloseSpider

from mygeo.settings import env
from world.models import PropertyListing

log = logging.getLogger(__name__)


# See also example in https://docs.scrapy.org/en/latest/topics/item-pipeline.html for more customization
class MyItemPipeline:
    def __init__(self, stats):
        self.stats = stats

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.stats)

    def process_item(self, item, spider):
        """Accept a single listing pulled from an HTML page, and save it to the PropertyListing DB table."""
        listing_fields = {k: item[k] for k in ["price", "addr", "br", "ba", "mlsid", "size"] if k in item}
        log.debug(f"Found listing: {item}")
        try:
            try:
                # Create a new entry when the price, addr or status changes on an entry
                property, created = PropertyListing.objects.get_or_create(
                    **listing_fields, status=PropertyListing.ListingStatus.ACTIVE
                )
            except MultipleObjectsReturned as e:
                # uniqueness constraint violated - price,addr,br,ba,mlsid,size,status should be a unique entry. fix it up
                listings = PropertyListing.objects.filter(
                    **listing_fields, status=PropertyListing.ListingStatus.ACTIVE
                ).order_by("founddate")
                # most likely case is the first listing has the found date we want but still has a zip code,
                # which we deprecated in the listing.
                print(f"*** WARNING *** MULTIPLE MATCHING LISTINGS IN DB for MLSID={listings[0].mlsid}")
                self.stats.inc_value("error:listing/multiple_entries_in_db")
                if len(listings) != 2:
                    print("NEED TO DEBUG THIS CASE")

                # take listings[1] as the listing going forward, patching up its found-date.
                listings[1].founddate = listings[0].founddate
                listings[1].full_clean()
                listings[1].save()
                listings[0].delete()
                property = listings[1]
                created = False

            property.thumbnail = item["thumbnail"]
            property.listing_url = item["listing_url"]
            property.neighborhood = item["neighborhood"]
            if created:
                # object with same parameters (price / etc) not found, so record this instance and include a link to
                # the most recent previous entry if it exists.
                prev_listing = (
                    PropertyListing.objects.filter(mlsid=property.mlsid)
                    .exclude(id=property.id)
                    .order_by("-seendate")
                )
                if len(prev_listing) > 0:
                    property.prev_listing = prev_listing[0]
                property.full_clean()
                property.save()
                self.stats.inc_value("info:listing/new_or_update")
            else:
                # Property WITH these parameters seen, so update the "seendate" in-place on the current entry.
                property.full_clean()
                property.save(update_fields=["seendate", "thumbnail", "listing_url", "neighborhood"])
                self.stats.inc_value("info:listing/no_change")
        except Exception as e:
            print(e)
            traceback.print_exc()
            raise CloseSpider()


class SanDiegoMlsSpider(scrapy.Spider):
    name = "mls"

    def __init__(self, zip_groups, localhost_mode, **kwargs):
        self.zip_groups = zip_groups
        self.localhost_mode = localhost_mode
        self.client = ScraperAPIClient(env("SCRAPER_API_KEY"))

        # Need to adjust logging, scrapy is very verbose!
        log_levels = (
            ("scrapy.core.scraper", logging.INFO),
            ("scrapy.core.engine", logging.INFO),
            ("scrapy.middleware", logging.ERROR),
            ("scrapy.crawler", logging.WARNING),
            ("scrapy.extensions.telnet", logging.WARNING),
            ("scrapy.utils.log", logging.WARNING),
        )
        for logger, level in log_levels:
            logging.getLogger(logger).setLevel(level)

        super().__init__(**kwargs)

    def start_requests(self):
        headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:48.0) Gecko/20100101 Firefox/48.0"}
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_3) AppleWebKit/537.36 (KHTML, "
            "like Gecko) Chrome/99.0.4844.84 Safari/537.36"
        }
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 12_5) AppleWebKit/605.1.15 (KHTML, "
            "like Gecko) Version/15.6 Safari/605.1.15"
        }
        # yield scrapy.Request('https://slashdot.org', headers=headers)
        for zips in self.zip_groups:
            url = self.san_diego_listings_url(zips)
            orig_url = url
            log.info(f"URL to crawl: {url}")
            if not self.localhost_mode:
                # wrap URL in cloud proxy from scraperapi.com
                url = self.client.scrapyGet(url)
            log.debug(f"*** Spider requesting zips={zips}")
            yield scrapy.Request(url, headers=headers, cb_kwargs={"orig_url": orig_url})

    name_subs = {
        "Beds": "br",
        "Baths": "ba",
        "SqFt.": "size",
        "MLS": "mlsid",
    }

    def parse(self, response, orig_url=None):
        """Parse property listings from an HTML response and yield the result as a dictionary (to be processed
        by MyItemPipeline )"""
        for listing in response.css("div.row.results"):
            listing_data = defaultdict()
            listing_data["thumbnail"] = listing.css(".property-thumb img::attr(src)").get()
            listing_data["listing_url"] = listing.css("a::attr(href)").get()
            addr, neighborhood = listing.css(".address::text").get().split(",")[0:2]
            addr = addr.strip()
            neighborhood = neighborhood.strip()
            price = listing.css(".price::text").get().strip()
            price = int(re.sub(r"[\$,]", "", price))
            listing_data["price"] = price
            listing_data["addr"] = addr
            listing_data["neighborhood"] = neighborhood
            # extract BR, BA, MLS #, and sq ft:
            for detail in listing.css(".featured-details .detail"):
                detail_name = detail.css(".detail-title::text").get()
                detail_value = re.sub(r",", "", detail.css(".number::text").get())
                if detail_name != "MLS":
                    detail_value = int(detail_value)
                listing_data[self.name_subs[detail_name]] = detail_value
            yield listing_data

        next_url = response.css('.pagination a[rel="next"]::attr(href)').get()
        if next_url:
            url = urljoin(orig_url, next_url)
            orig_url = url
            log.debug(f"URL to crawl next: {url}")
            if not self.localhost_mode:
                # wrap URL in cloud proxy from scraperapi.com
                url = self.client.scrapyGet(url)

            yield scrapy.Request(url, self.parse, cb_kwargs={"orig_url": orig_url})

    def san_diego_listings_url(self, zips: [int]):
        """Generate a URL to query listings from homesalessandiego.com in a range of zipcodres"""
        hostname = "http://localhost:8000/" if self.localhost_mode else "https://www.homesalessandiego.com/"
        path = "search/results/mrys/"
        try:
            zip_string = "&".join([f"zip={zip}" for zip in zips])
        except Exception as e:
            print(e)
            print("Uh oh")
            traceback.print_exc()

        query_params = (
            "type=res&type=mul&type=lnd&list_price_min=50000&list_price_max=3000000&"
            "beds_min=all&baths_min=all&area_min=all&lot_size_range=all"
            "&view=all&parking_spaces_total_min=all&year_built_min=all&pool=all&stories=all&hoa=all&"
            "age_restriction=all&short_sale=all&foreclosure=all&elementary_school=all&middle_school=all&"
            ""
            "high_school=all&terms=all"
        )
        url = hostname + path + "?" + zip_string + "&" + query_params
        if self.localhost_mode:
            # don't cache in localhost mode, for testing
            url += "&cachebust=" + str(random.randrange(999999999))
        return url


def scrape_san_diego_listings_by_zip_groups(zip_groups, localhost_mode, cache=True):
    download_delay = 2.0 if localhost_mode else 12
    crawl_settings = {
        "ITEM_PIPELINES": {
            "lib.scraping_lib.MyItemPipeline": 100,
        },
        "COOKIES_ENABLED": False,
        "DOWNLOAD_DELAY": download_delay,  # Delay in seconds between pages (with randomized jitter)
        "HTTPCACHE_ENABLED": cache,
        "HTTPCACHE_STORAGE": "scrapy.extensions.httpcache.FilesystemCacheStorage",
        "HTTPCACHE_POLICY": "scrapy.extensions.httpcache.DummyPolicy",
        "MIDDLEWARE": {
            "scrapy.downloadermiddlewares.httpcache.HttpCacheMiddleware",
        },
        "AUTOTHROTTLE_ENABLED": True,
        "CONCURRENT_REQUESTS": 1,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 1,
        "DOWNLOAD_TIMEOUT": 60,
        "LOG_ENABLED": True,
        "LOG_LEVEL": log.getEffectiveLevel(),
    }
    logging.getLogger("scrapy.crawler").setLevel("WARNING")

    process = CrawlerProcess(settings=crawl_settings, install_root_handler=False)
    crawler = process.create_crawler(SanDiegoMlsSpider)
    process.crawl(crawler, zip_groups=zip_groups, localhost_mode=localhost_mode)
    process.start(stop_after_crawl=True)
    return crawler.stats
