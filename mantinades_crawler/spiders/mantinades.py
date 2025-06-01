# Databricks notebook source
from bs4 import BeautifulSoup
import csv
from datetime import datetime, timezone
import json
import os
import re
import scrapy
from urllib.parse import urlencode, urljoin

from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient
from azure.core.exceptions import ResourceExistsError



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
        
        pages_nums = re.match(r'^Σελίδα\s+(\d+)\s+από\s+(\d+)$', curr_page_nums_text)

        curr_page, max_page = int(pages_nums.group(1)), int(pages_nums.group(2))
        print('MANOS ', curr_page_nums_text, 'EXTRACTED', curr_page, max_page, 'FROM', response.meta.get('root_url'))
        assert(curr_page <= max_page and curr_page >= 1)

        return curr_page, max_page



    def __remove_tags_from_text(self, text):
        new_text = re.sub('<br>', ', ', text)
        new_text = BeautifulSoup(new_text, features="lxml").get_text()
        new_text = re.sub(r'\s+', ' ', new_text)

        return new_text


    def __extract_mantinada_info(self, mantinada_footer):
        topics = []
        author = None
        date = ''

        mantinada_footer = mantinada_footer.strip()

        if 'που μας έστειλε' in mantinada_footer:
            groups = re.match(r'^Μαντινάδα στ(?:ην|ις) κατηγορ(?:ία|ίες) (.+) που μας έστειλε ο/η (.+) την (\d\d/\d\d/\d\d\d\d)',
                              mantinada_footer)

            topics = [t.strip() for t in groups.group(1).split(',')]
            author = groups.group(2)
            date   = groups.group(3)
        else:
            groups = re.match(r'^Μαντινάδα στ(?:ην|ις) κατηγορ(?:ία|ίες) (.+) που καταχωρήθηκε την (\d\d/\d\d/\d\d\d\d)',
                              mantinada_footer)

            topics = [t.strip() for t in groups.group(1).split(',')]
            date   = groups.group(2)

        return topics, author, date



    # These are the urls that we will start scraping
    def start_requests(self):
        # Currently my validation will be constrained to if
        # I parsed all the topics and all the pages from them
        # I will also return the errors if any in the future
        # using errback functions
        self.all_topics    = set()
        self.parsed_topics = set()

        self.topics_pages_num    = {}
        self.topics_pages_parsed = {}

        self.start_time = datetime.now(timezone.utc)

        start_url = 'https://www.mantinades.gr/'
        yield scrapy.Request(url=get_proxy_url(start_url), callback=self.parse,
                             meta={'root_url': start_url})




    def parse(self, response):
        if not os.path.isdir(DESTINATION_DIR):
            os.mkdir(DESTINATION_DIR)

        # Xpath needs full path without omitting anything, that's why I add the /li in between
        categories_refs = response.selector.xpath('//ul[contains(@class, "sidebar-menu")]/li/a/@href')

        categories_refs = [c.get() for c in categories_refs][:-1]
        
        categories_name = [c_ref.split('/')[-1] for c_ref in categories_refs]
        self.all_topics = set(categories_name)

        response_url = response.meta.get('root_url')

        redirect_urls = [f'{urljoin(response_url, c_ref)}?page=1' for c_ref in categories_refs]

        for url in redirect_urls:
            yield scrapy.Request(get_proxy_url(url), callback=self.parse_category,
                                 meta={'root_url': url})



    def parse_category(self, response):
        category = response.meta.get('root_url').split('/')[-1].split('?')[0]

        curr_page, max_page = self.__get_curr_page_and_max_page(response)

        self.parsed_topics.add(category)
        
        if category not in self.topics_pages_parsed.keys():
            self.topics_pages_parsed[category] = set([curr_page])
            self.topics_pages_num[category] = max_page
        else:
            self.topics_pages_parsed[category].add(curr_page)

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
            next_url = re.sub(r'page=\d+$', f'page={curr_page + 1}', response.meta.get('root_url'))
            yield scrapy.Request(get_proxy_url(next_url), callback=self.parse_category,
                                 meta={'root_url': next_url})

        return
    
    def closed(self, reason):
        # Getting the necessary information about crawling
        all_topics_num    = len(self.all_topics)
        parsed_topics_num = len(self.parsed_topics)

        not_parsed_topics = list(self.all_topics.difference(self.parsed_topics))

        per_topic_information = []

        for topic in self.parsed_topics:
            all_pages_set = set(list(range(1, self.topics_pages_num[topic] + 1)))
            not_parsed_pages = all_pages_set.difference(self.topics_pages_parsed[topic])

            topic_information_results = {
                'topic':              topic,
                'pages_num':          self.topics_pages_num[topic],
                'parsed_pages_num':   len(self.topics_pages_parsed[topic]),
                'not_parsed_pages':   sorted(list(not_parsed_pages))
            }

            per_topic_information.append(topic_information_results)
        
        crawling_info = {
            'reason':                   reason,
            'start_time':               str(self.start_time),
            'end_time':                 str(datetime.now(timezone.utc)), 
            'all_topics_num':           all_topics_num,
            'parsed_topics_num':        parsed_topics_num,
            'not_parsed_topics':        not_parsed_topics,
            'per_topic_information':    per_topic_information 
        }

        sas_token = 'sv=2024-11-04&ss=bfqt&srt=sco&sp=rwdlacupyx&se=2025-06-28T16:31:23Z&st=2025-04-28T08:31:23Z&spr=https&sig=T%2BrccqmnwUA3sqiv9DVwJ5wEFHdgk9hjOSvhUB1PDCs%3D'
        account_url = f"https://mantinadescrawleraccount.blob.core.windows.net/?{sas_token}"
        # default_credential = DefaultAzureCredential()

        # Create the BlobServiceClient object
        self.blob_service_client = BlobServiceClient(account_url)

        # The container has already been created 
        self.container_client = self.blob_service_client.get_container_client('data')

        CRAWLING_INFO_FILE_NAME = 'crawling_info.json'

        # Write the file in a temporary place
        with open(CRAWLING_INFO_FILE_NAME, 'w', encoding='utf-8') as f:
            f.write(json.dumps(crawling_info, indent=4))

        # Read it again and upload blob
        with open(CRAWLING_INFO_FILE_NAME, "rb") as data:
            self.container_client.upload_blob(name=CRAWLING_INFO_FILE_NAME, data=data, overwrite=True)

        os.remove(CRAWLING_INFO_FILE_NAME)
        return