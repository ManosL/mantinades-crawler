# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import csv
import os
from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient
from azure.core.exceptions import ResourceExistsError

from scrapy.utils.project import get_project_settings

settings = get_project_settings()

from mantinades_crawler.spiders.mantinades import DESTINATION_DIR



class RemoveDuplicatesPipeline:
    def open_spider(self, spider):
        self.ids_seen = set()
        return



    def process_item(self, item, spider):
        item_id = item['id']

        if (item_id in self.ids_seen):
            raise DropItem(f"Item ID already seen: {item_id}")

        self.ids_seen.add(item_id)

        return item



class MantinadesCrawlerPipeline:
    def open_spider(self, spider):
        sas_token = settings.get('AZURE_BLOB_STORAGE_SAS_TOKEN')
        account_url = f"https://{settings.get('AZURE_BLOB_STORAGE_ACCOUNT_NAME')}.blob.core.windows.net/?{sas_token}"
        # default_credential = DefaultAzureCredential()

        # Create the BlobServiceClient object
        self.blob_service_client = BlobServiceClient(account_url)

        # Create the container
        try:
            self.container_client = self.blob_service_client.create_container('data')
        except ResourceExistsError:
            print('Container data already exists')
            self.container_client = self.blob_service_client.get_container_client('data')

        self.categories_files = {}
        self.header_row = ['id', 'topics', 'author', 'date', 'text']
        return



    def process_item(self, item, spider):
        item_category = item['category']

        if item_category not in self.categories_files.keys():
            category_file = open(os.path.join(DESTINATION_DIR, f'{item_category}.csv'), 'w', encoding="utf-8")
            category_writer = csv.writer(category_file, delimiter='|')

            category_writer.writerow(self.header_row)

            self.categories_files[item_category] = (category_file, category_writer)

        row_to_add = [item['id'], item['topics'], item['author'], item['date'], item['text']]
        self.categories_files[item_category][1].writerow(row_to_add)
        self.categories_files[item_category][0].flush()

        return item



    def close_spider(self, spider):
        for file, _ in self.categories_files.values():
            file.close()

        for filename in os.listdir(DESTINATION_DIR):
            # Upload file
            with open(os.path.join(DESTINATION_DIR, filename), "rb") as data:
                self.container_client.upload_blob(name=filename, data=data, overwrite=True)

            os.remove(os.path.join(DESTINATION_DIR, filename))

        os.rmdir(DESTINATION_DIR)

        return