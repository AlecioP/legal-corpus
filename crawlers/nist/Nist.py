from urllib.parse import urlencode
import requests
from bs4 import BeautifulSoup
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor


import uuid

def url_to_key(url):
	# Pass url as seed for random uuid . Therefore the result should be reproducible
	return uuid.uuid5(uuid.NAMESPACE_URL, url).hex

class SpiderSpider(CrawlSpider):

     lua_script = '''
          function main(splash, args)
          splash.private_mode_enabled= false
          local url = splash.args.url
          assert(splash:go(url))
          assert(splash:wait(10))
          return {
               html = splash:html(),
               png = splash:png(),
               har = splash:har(),
          }
          end
     '''

     govinfo_links = {}
     name = 'automotive'

     allow_urls = [r'.*nist\.gov/Topics/Laws-and-Regulations/laws' , r'.*govinfo\.gov.*']
     start_urls = ["https://csrc.nist.gov/Topics/Laws-and-Regulations/laws"
                  ]
     base_url = 'https://csrc.nist.gov/'


     rules = [Rule(LinkExtractor(allow=allow_urls,restrict_css='body',unique=True),
                    callback='parse_law_document', follow=True)]

     def parse_law_document(self, response):

          if "Topics/Laws-and-Regulations/laws/" in response.request.url :

               print(f"Processing {response.request.url}")

               gov_url = response.css("div#page-description a::attr(href)").get()

               url_hash = url_to_key(gov_url)

               self.govinfo_links[url_hash] = response.request.url

               print(f"Should parse {gov_url} for pdf")

          if url_to_key(response.request.url) in self.govinfo_links.keys() and "govinfo.gov" in response.request.url :
            
               splash_url = self.settings.get("SPLASH_URL") + "render.html?" + urlencode({
                                                                 'images': 1,
                                                                 'expand' : 1,
                                                                 'timeout' : 90.0,
                                                                 'url' : response.request.url,
                                                                 'wait' : 5 , 
                                                                 'lua_source' : self.lua_script})
               print(f"Should get this url to see complete page: {splash_url}")
               res = requests.get(splash_url)
               soup = BeautifulSoup(res.content.decode(),'html.parser')
               pdf_link = soup.find(id='pdf').get('href')
               #pdf_link = response.css("div#mobileDownload a")
               yield { "origin_url" : self.govinfo_links[url_to_key(response.request.url)] ,
                    "govinfo_url" : response.request.url ,
                    "pdf_url" : f"https:{pdf_link}"}
