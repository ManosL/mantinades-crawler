from bs4 import BeautifulSoup
import csv
import os
import re
import scrapy
from urllib.parse import urlencode, urljoin



DESTINATION_DIR = './data'

# TODO: MAKE IT INCREMENTAL
# LAST_RUN_DATE = '25/01/2025'

API_KEY = 'e0b9a5cba3d5e32766a578bc0c1e7c99'

def get_proxy_url(url):
    payload = {'api_key': API_KEY, 'url': url, 'country_code': 'eu'}
    proxy_url = 'https://api.scraperapi.com/?' + urlencode(payload)
    return proxy_url



class MantinadesSpider(scrapy.Spider):
    name = 'mantinades'
    # allowed_domains = ['mantinades.gr']
    # start_urls = ['https://mantinades.gr/']

    def __get_curr_page_and_max_page(self, response):
        curr_page = 1
        max_page = 160

        page_div = response.selector.css(".text-center")[-1]
        curr_page_nums_text = page_div.xpath('.//div[1]/text()').get()

        if curr_page_nums_text is None:
            return 1, 1

        curr_page_nums_text = curr_page_nums_text.strip()

        pages_nums = re.match('^Σελίδα\s+(\d+)\s+από\s+(\d+)$', curr_page_nums_text)

        curr_page, max_page = int(pages_nums.group(1)), int(pages_nums.group(2))

        assert(curr_page <= max_page and curr_page >= 1)

        return curr_page, max_page



    def __remove_tags_from_text(self, text):
        new_text = re.sub('<br>', ', ', text)
        new_text = BeautifulSoup(new_text, features="lxml").get_text()
        new_text = re.sub('\s+', ' ', new_text)

        return new_text


    def __extract_mantinada_info(self, mantinada_footer):
        topics = []
        author = None
        date = ''

        mantinada_footer = mantinada_footer.strip()

        if 'που μας έστειλε' in mantinada_footer:
            groups = re.match('^Μαντινάδα στ(?:ην|ις) κατηγορ(?:ία|ίες) (.+) που μας έστειλε ο/η (.+) την (\d\d/\d\d/\d\d\d\d)',
                              mantinada_footer)

            topics = [t.strip() for t in groups.group(1).split(',')]
            author = groups.group(2)
            date   = groups.group(3)
        else:
            groups = re.match('^Μαντινάδα στ(?:ην|ις) κατηγορ(?:ία|ίες) (.+) που καταχωρήθηκε την (\d\d/\d\d/\d\d\d\d)',
                              mantinada_footer)

            topics = [t.strip() for t in groups.group(1).split(',')]
            date   = groups.group(2)

        return topics, author, date



    # These are the urls that we will start scraping
    def start_requests(self):
        start_url = 'https://www.mantinades.gr/'
        yield scrapy.Request(url=get_proxy_url(start_url), callback=self.parse,
                             meta={'root_url': start_url})




    def parse(self, response):
        if not os.path.isdir(DESTINATION_DIR):
            os.mkdir(DESTINATION_DIR)

        # Xpath needs full path without omitting anything, that's why I add the /li in between
        categories_refs = response.selector.xpath('//ul[contains(@class, "sidebar-menu")]/li/a/@href')

        categories_refs = [c.get() for c in categories_refs][:-1]

        response_url = response.meta.get('root_url')

        redirect_urls = [f'{urljoin(response_url, c_ref)}?page=1' for c_ref in categories_refs]

        for url in redirect_urls:
            yield scrapy.Request(get_proxy_url(url), callback=self.parse_category,
                                 meta={'root_url': url})



    def parse_category(self, response):
        category = response.meta.get('root_url').split('/')[-1].split('?')[0]

        curr_page, max_page = self.__get_curr_page_and_max_page(response)

        full_box_divs = response.css('.disableselect')

        mantinades = []

        assert(len(full_box_divs) > 0)

        for curr_div in full_box_divs:
            mantinada_id = curr_div.attrib.get('id')
            mantinada_div = curr_div.css('.manti')

            text_div = mantinada_div.xpath('.//div').get()
            text_div = self.__remove_tags_from_text(text_div)

            info_div = mantinada_div.xpath('.//h5').get()
            info_div = self.__remove_tags_from_text(info_div)

            topics, author, date = self.__extract_mantinada_info(info_div)

            curr_item = {
                'category': category,
                'id': mantinada_id,
                'topics': topics,
                'author': author,
                'date': date,
                'text': text_div
            }

            yield curr_item

        if curr_page < max_page:
            next_url = re.sub(f'page=\d+$', f'page={curr_page + 1}', response.meta.get('root_url'))
            yield scrapy.Request(get_proxy_url(next_url), callback=self.parse_category,
                                 meta={'root_url': next_url})

        return
