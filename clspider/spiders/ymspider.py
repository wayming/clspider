import os
import scrapy
from urllib.parse import urlparse, parse_qs
from scrapy.linkextractors import LinkExtractor


class YmSpider(scrapy.Spider):
    name = "ymspider"

    def __init__(self, start_url=None, *args, **kwargs):
        if start_url:
            self.start_urls = [start_url]
        else:
            self.start_urls = ['https://default.com']

    def parse(self, response):
        # Extract links using LinkExtractor
        print(self.start_urls)
        # Initialize LinkExtractor
        link_extractor = LinkExtractor()

        # Get the table(s) with class 'dc_bar2'
        tables = response.css("table.dc_bar2")
        for table in tables:
            # Extract HTML content of the table
            table_html = table.get()
            # Create a subresponse using the original response's metadata but with the table's HTML
            subresponse = response.replace(body=table_html)
            # Extract links from the subresponse
            links = link_extractor.extract_links(subresponse)
            
            # Yield the link URLs
            for link in links:
                yield response.follow(link.url, self.parse_page)

    def parse_page(self, response):
        # Get the URL to name the file (you can customize this part)
        parsed_url = urlparse(response.url)
        tid = parse_qs(parsed_url.query).get('tid', [None])[0]
        filepath = os.path.join('../output', f'{tid}.txt')  # Save to 'output' folder

        # Ensure output folder exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        # Extract content inside <pre> tags, remove '\u3000' characters
        contents = response.css('pre::text').getall()

        # Clean the contents by replacing '\u3000' with an empty string
        cleaned_content = ''.join([text.replace('\u3000', '') for text in contents])
        print(filepath)
        # Write the cleaned content to a text file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(cleaned_content)

        # Log the file saved
        self.log(f'Saved file {filepath}')

