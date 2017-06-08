import re
import scrapy
from scrapy.spiders import SitemapSpider

def first_p_after_h4(header_text, add_a=False):
    return ('h4[normalize-space(text()) = "%s"]/following-sibling::p[1]'
        '%s/text()' % (header_text, '/a' if add_a else ''))

class MfaSitemapSpider(scrapy.Spider):
#class MfaSitemapSpider(SitemapSpider):
    # Internal settings.
    name = "mfa"
    #sitemap_urls = ['http://www.mfa.org/robots.txt']
    #sitemap_rules = [
    #    ('/object/', 'parse_object'),
    #]

    #start_urls = [
    #    'http://www.mfa.org/collections/object/the-ghost-of-oiwa-oiwa-san-from-the-series-one-hundred-ghost-stories-hyaku-monogatari-129277',
    #]
    with open("urls.txt", "rt") as f:
        start_urls = [url.strip() for url in f.readlines()]

    #def parse(self, response):
    #    self.logger.info('Skipping non-object url %s' % response.url)

    #def parse_object(self, response):
    def parse(self, response):
        # Save raw contents so we don't have to re-crawl.
        page = response.url.split('/')[-1]
        if len(page) > 200:
            parts = page.split('-')
            page = parts[0] + '-TRUNC-' + parts[-1]
        with open('html/' + page + '.html', 'wb') as f:
            f.write(response.body)
        self.logger.info('Saved page %s' % page)

        # TODO: put all the rest in helper fn
        # Determine whether the object is a Japanese print.
        #main = response.css('div.grid-6')
        main = response.xpath(
            'descendant-or-self::div[@class and contains(concat(" ", '
            'normalize-space(@class), " "), " grid-6 ")][3]')
        origin = main.css('p::text').extract_first()
        if not origin.startswith('Japan'):
            self.logger.info('Skipping origin %s for %s' % (origin, page))
            return

        classes = main.xpath(
            first_p_after_h4('Classifications', True)).extract_first()
        if classes.find('Prints') == -1:
            self.logger.info('Skipping class %s for %s' % (classes, page))
            return
        self.logger.info('Japanese print: %s' % page)

        # Now we have a Japanese print. Save image, even if we can't get all the
        # metadata later on.
        # Image URLs are in comments.
        comment = response.css('div.image').xpath('comment()').extract_first()
        if not comment:
            self.logger.info('No image for %s' % page)
            return
        match = re.search('src="(\S*)"', comment)
        if not match:
            self.logger.info('No image for %s' % page)
            return
        image_urls = match.groups(0)

        # Extract all interesting metadata.
        title_EN = main.css('h2::text').extract_first()
        if title_EN: title_EN = title_EN.strip()
        title_JP = main.css('h3::text').extract_first()
        if title_JP: title_JP = title_JP.strip()
        artist = main.xpath('//p[1]/a[1]/text()').extract_first()
        publisher = main.xpath('//p[1]/a[2]/text()').extract_first()

        # Date is tricky, as it can be like '1872' or 'Tenpo Era'.
        # We save the whole string and normalize it post-crawl.
        date = 'Unknown'
        blob = main.xpath('//p[1]').extract()[0]
        if blob:
            date_re = re.search('<br>(.*)<br>', blob)
            if date_re:
                date = date_re.groups(0)

        medium = main.xpath(
            first_p_after_h4('Medium or Technique')).extract_first()
        format = main.xpath(first_p_after_h4('Dimensions')).extract_first()
        acc_num = main.xpath(first_p_after_h4('Accession Number')).extract_first()

        # Information on the right side of the page.
        side = response.xpath(
            'descendant-or-self::div[@class and contains(concat(" ", '
            'normalize-space(@class), " "), " grid-6 ")][4]')
        state_info = side.css('div.body p::text').extract_first()
        mfa_dups = None
        if state_info:
            dup_re = re.search('MFA impressions: (.*)', state_info)
            if dup_re:
                mfa_dups = dup_re.groups(0)
        signed = side.xpath('h3[normalize-space(text()) = "Signed"]/'
            'following-sibling::p/text()').extract_first()
        markings = side.xpath('h3[normalize-space(text()) = "Markings"]/'
            'following-sibling::p/text()').extract_first()

        # Output.
        yield {
            'url': response.url,
            'title_EN': title_EN,
            'title_JP': title_JP,
            'artist': artist,
            'publisher': publisher,
            'date': date,
            'medium': medium,
            'format': format,
            'acc_num': acc_num,
            'mfa_dups': mfa_dups,
            'signed': signed,
            'markings': markings,
            'image_urls': image_urls  # magic field
        }
