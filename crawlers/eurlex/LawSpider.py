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
	allowed_domains = ['europa.eu']
	start_urls = [#'https://eur-lex.europa.eu/homepage.html',
			'https://eur-lex.europa.eu/search.html?lang=en&type=quick&SCOPE=EURLEX&text=automotive',
			'https://eur-lex.europa.eu/search.html?lang=en&type=quick&SCOPE=EURLEX&text=car',
			'https://eur-lex.europa.eu/search.html?lang=en&type=quick&SCOPE=EURLEX&text=transport']
	base_url = 'https://eur-lex.europa.eu/'
	
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
	
	rules = [Rule(LinkExtractor(allow=allowed_domains,restrict_css='body',unique=True),
                      callback='parse_law_document', follow=True)]
                      
	def parse_law_document(self, response):
	
		# Add to hashmap the pair <URL - IS_IN_TOPIC>
		
		automotive_topic = intopic(response)
		url_hash = url_to_key(response.request.url)
		
		if not self.url_uuid_to_topic.get(url_hash,None) is None :
			print("Visiting url twice")
	
		self.url_uuid_to_topic[url_hash] = automotive_topic
		
		#if automotive_topic == True :
		#	print(response.request.url + " [" + str(url_hash)+"] contains keywords")
	
		# Is a document to save
		allowed_format = False
		for t in self.allowed_mime_type :
			if t in response.headers['Content-Type']:
				allowed_format = True
				break
			
		if allowed_format :
			
			ref_url = response.request.headers.get('Referer', None)
			if (not (ref_url is None )):
				ref_url_hash = url_to_key(ref_url.decode('utf-8'))
				#print("Referer url is : " + str(ref_url) +" ["+str(ref_url_hash)+ "]")
				ref_in_topic = self.url_uuid_to_topic.get(ref_url_hash)
				# Parent page contained some relevant keyword
				#print(ref_in_topic)
				if (not ref_in_topic is None) and ref_in_topic == True:
					# Save the link and send url to pipeline to download
					if "/IT/" in response.request.url :
						yield {
						"document-url" : response.url, 
						"referer" : ref_url.decode('utf-8')}
				
		
			
