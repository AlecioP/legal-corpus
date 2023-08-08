from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
    
import numpy as np
import spacy

import uuid


nlp = spacy.load("en_core_web_lg")

def most_similar(mword,topn=10):
	ms = nlp.vocab.vectors.most_similar(
    	np.asarray([nlp.vocab.vectors[nlp.vocab.strings[mword]]]), n=topn)
	return [nlp.vocab.strings[w] for w in ms[0][0]]

keywords = most_similar("automotive", topn=10) + most_similar("car", topn=10) + most_similar("transport", topn=10)

print("The keywords related to the topic are:")
print(keywords)

def intopic(response):
	content_type = response.headers.get("Content-Type",None)
	
	#print(content_type)
	
	if (content_type is None) or (not b"text/html" in content_type):
		return False
	
	for kw in keywords:
		if kw.upper() in response.text.upper() :
			#print("Returning true here")
			return True
	return False
    
def url_to_key(url):
	# Pass url as seed for random uuid . Therefore the result should be reproducible
	return uuid.uuid5(uuid.NAMESPACE_URL, url).hex
    
class SpiderSpider(CrawlSpider):

	url_uuid_to_topic = {}

	name = 'automotive'
	allow_urls = [r'.*unece\.org.*']
	start_urls = ["https://unece.org/search_content_unece?keyword=automotive&f%5B0%5D=content_types%3Adocuments",
	"https://unece.org/search_content_unece?keyword=car&f%5B0%5D=content_types%3Adocuments",
	"https://unece.org/search_content_unece?keyword=vehicle&f%5B0%5D=content_types%3Adocuments"
			]
	base_url = 'https://unece.org/'
	
	allowed_mime_type = [
		#b'application/zip', 
		b'application/pdf'#, 
		#b'application/octet-stream', 
		#b'application/msword', 
		#b'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 
		#b'application/vnd.oasis.opendocument.text', 
		#b'application/rtf', 
		#b'text/plain'
		]
	
	rules = [Rule(LinkExtractor(allow=allow_urls,restrict_css='body',unique=True),
                      callback='parse_law_document', follow=True)]
                      
	def parse_law_document(self, response):
		content_type = response.headers.get("Content-Type",None)
		
		
	
		if "/documents/" in response.request.url and intopic(response) :
		
			print(f"Processing {response.request.url}")
			
			document_category = response.css("div#block-views-block-document-field-top-block-1 div.views-field-field-category div.field-content::text").get()
			
			if document_category is None :
				print(f"{response.request.url} has no category")
			
			if (not document_category is None) and ("Standards" in document_category) : #or "Working Documents" in document_category :
				lang_divs_list = response.css("div#block-views-block-document-field-top-block-3 ul.docslangitem li.docslang")
				LANG = "English"
				my_lang_el = None
				
				for li in lang_divs_list :
					
					listed_lang = li.css("div.views-field-field-language div.field-content::text").get()
					
					if LANG in listed_lang:
						my_lang_el = li
						break
				
				if not my_lang_el is None :
				
					# Class filename-1 should be pdf format
					doc_div = my_lang_el.css("div.views-field-filename-1")
					
					if not doc_div is None:
						pdf_url = doc_div.css("span.field-content a::attr(href)").get()
						if not pdf_url is None :
							#print(response.urljoin(pdf_url))
							yield { "origin" : response.request.url ,
								"document_url" :  response.urljoin(pdf_url)}
	
	
	
		
				
		
			
