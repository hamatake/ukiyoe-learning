import re
import scrapy

class LacmaSpider(scrapy.Spider):
    # Internal settings.
    name = "lacma"

    start_urls = [
        'http://collections.lacma.org/search/site/?f[0]=im_field_classification%3A25&f[1]=im_field_curatorial_area%3A46&f[2]=bm_field_has_image%3Atrue&f[3]=sm_field_artist%3Anode%3A153821',
        'http://collections.lacma.org/search/site/?f[0]=im_field_classification%3A25&f[1]=im_field_curatorial_area%3A46&f[2]=bm_field_has_image%3Atrue&f[3]=sm_field_artist%3Anode%3A152817',
    ]

    def parse(self, response):
        # Get each object in current page of results.
        site = response.url[:response.url.find('lacma.org') + len('lacma.org')]
        links = response.css('div.search-result-data a::attr(href)').extract()
        for link in links:
            yield scrapy.Request(site + link, callback=self.parse_object)

        # Get next page of results.
        next_page = response.css('li.pager-next a::attr(href)').extract_first()
        if next_page:
            yield scrapy.Request(site + next_page, callback=self.parse)
        else:
            self.logger.info('Stopping at %s' % response.url)

    def parse_object(self, response):
        # Save raw contents so we don't have to re-crawl.
        page = response.url.split('/')[-1]
        with open('html/' + page + '.html', 'wb') as f:
            f.write(response.body)
        self.logger.info('Saved page %s' % page)

        # Save image, even if we can't get all the metadata later on.
        # Look for high-quality image first.
        site = response.url[:response.url.find('lacma.org') + len('lacma.org')]
        image_urls = None
        hi_res = response.xpath('//a[normalize-space(text()) = '
            '"Download publication quality tiff"]/@href').extract_first()
        if hi_res:
            image_urls = [site + hi_res]  # hi-res url is relative
        else:
            low_res = response.css('div.media-asset-image img::attr(src)').extract_first()
            if low_res:
                image_urls = [low_res]  # low-res url is absolute
        if not image_urls:
            self.logger.error('No image found for %s' % response.url)
            return

        # Metadata is all on the right.
        right = response.css('div.group-right')
        title_EN = right.css('h1::text').extract_first()
        artist = right.css('div.artist-name a::text').extract_first()
        if artist.find(' (Japan') > 0:
            artist = artist[:artist.find(' (Japan')]

        # Extract from generic list of fields.
        date = None
        title_JP = None
        dimensions = None
        series = None
        fields = right.css('div.field::text').extract()
        if fields:
            for field in fields:
                # Date field looks like 'Japan, 1832'.
                match = re.search('^Japan, (.*)', field)
                if match:
                    date = match.groups(0)[0].strip()

                # Sometimes fields contain multiple key:value pairs, so we
                # search for each interesting key in every field.
                match = re.search('Alternate Title:([^;]*)', field)
                if match:
                    title_JP = match.groups(0)[0].strip()
                match = re.search('Series:([^;]*)', field)
                if match:
                    series = match.groups(0)[0].strip()
                match = re.search('Paper:([^;]*)', field)
                if match:
                    dimensions = match.groups(0)[0].strip()

        # Output.
        yield {
            'url': response.url,
            'title_EN': title_EN,
            'title_JP': title_JP,
            'artist': artist,
            'date': date,
            'dimensions': dimensions,
            'image_urls': image_urls  # magic field
        }
