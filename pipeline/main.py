import urllib.request
from urllib.parse import urljoin
import csv
from io import BytesIO
from PyPDF2 import PdfReader
from bs4 import BeautifulSoup
from bs4 import Comment

INPUT_FILE = "./norme.csv"

#url = 'http://example.com/'
#response = urllib.request.urlopen(url)
#data = response.read()      # a `bytes` object
#text = data.decode('utf-8')




def main():

	NO_PDF = 0
	PDF_TO_TXT = []
	EURLEX_FROM_HTML = []
	GAZZA_FROM_HTML = []
	UNSCR_FROM_PFD = []
	PARL_FROM_HTM = []

	# Read csv containing links to laws' documents
	with open(INPUT_FILE) as csv_file:
		csv_reader = csv.reader(csv_file,delimiter=",")
		line = 0 
		for r in csv_reader : 
			if line < 2 : 
				line += 1 
				continue

			# url is in 4th column
			url = r[3]

			if len(url) == 0 or url.isspace():
				
				pass
			
			# If column is not empty
			else :
				# Fetch document from url
				response = urllib.request.urlopen(url)
				data = response.read()
				bytes_filelike = BytesIO(data)

				# If file is just a PDF extract all text and dump it to file
				if "application/pdf" in response.info().get_content_type() :
					pdf = PdfReader(bytes_filelike)
					text = ""
					for page_n in range(0 , len(pdf.pages) ):
						text += pdf.pages[page_n].extract_text()
				
					PDF_TO_TXT.append(text)
				else :

					# If url is from eur-lex domain 
					if "eur-lex.europa.eu/legal-content/" in url and "uri" in url:

						soup = BeautifulSoup(data,'html.parser')

						# Grap Text section of the HTML page
						content_div = soup.find(id="textTabContent")
						page_txt =  ""
						 
						txt_elements = content_div.find_all(string=True)
						for t in txt_elements :

							# Filter comment tags <!-- -->
							if isinstance(t,Comment):
								continue

							# Replace images with ALT attribute content
							if t.name == "img" : 
								if not t['alt'] is None : 
									page_txt += f"{t['alt']}"
							else :
								page_txt += f"{t}"
						EURLEX_FROM_HTML.append(page_txt)

					# If url is from parlamento domain
					elif "www.parlamento.it/parlam/leggi" in url and url.endswith("htm"):
						page_soup = BeautifulSoup(data,'html.parser')

						# Just extract the text from the DOM structure of HTM file
						txt_els = page_soup.find_all("div",class_="testolegge")[0].find_all(string=True)
						parl_txt = ""
						for el in txt_els :
							if not isinstance(el,Comment):
								parl_txt += f"{el}"
						PARL_FROM_HTM.append(parl_txt)

					# If url is from unscr domain
					elif "unscr.com/en/resolutions" in url :
						page_soup = BeautifulSoup(data,'html.parser')

						# Grab the url to the pdf version of the law
						pdf_rel = page_soup.find(id="download-doc")['href']
						# Resolve relative to absolute url
						pdf_url = urljoin(url,pdf_rel)
						# Fetch the pdf
						pdf_res = urllib.request.urlopen(pdf_url)
						pdf_io = BytesIO(pdf_res.read())
						pdf1 = PdfReader(pdf_io)
						unscr_text = ""
						# Extract text from the pdf and dump it to file
						for page_n in range(0 , len(pdf1.pages) ):
							unscr_text += pdf1.pages[page_n].extract_text()
						UNSCR_FROM_PFD.append(unscr_text)

					# If url is from gazzettaufficiale domain
					elif "gazzettaufficiale.it/eli/id/" in url :
						page_soup = BeautifulSoup(data,'html.parser')

						# Grab the nav-bar element and extract iframe url
						left_iframe = page_soup.find(id="leftFrame")['src']

						# Fetch iframe page
						url2 = urljoin(url, left_iframe)
						res2 = urllib.request.urlopen(url2)
						data2 = res2.read()

						# Extract list of all articles of the law
						articles_tree = BeautifulSoup(data2,'html.parser').find(id="albero")
						items = articles_tree.find_all("li")

						article_text = ""
						# Extract title of the law 
						for txt1 in page_soup.find(id="testa_atto").find_all(string=True):
							article_text += f"{txt1}"

						# For each item pointing to the law's article
						for it in items :
							if not it.has_attr('class') :
								# Extract the url of the page containing the article
								subarticle_rel = it.find_all('a')[0]['href']
								# Resolve relative to absolute url
								subarticle_url = urljoin(url2,subarticle_rel)
								# Fetch the page
								res3 = urllib.request.urlopen(subarticle_url)
								data3 = res3.read()
								subarticle_soup = BeautifulSoup(data3,'html.parser')
								# Extract the text and notes
								subarticle_text = subarticle_soup.find_all("span",class_="dettaglio_atto_testo")[0].find_all(string=True)
								#subarticle_text = subarticle_soup.find_all("span",class_="dettaglio_atto_testo")[0].find_all("pre")[0].find_all(string=True)
								for para in subarticle_text :
									article_text += f"{para}"
						GAZZA_FROM_HTML.append(article_text)
					# If no other case matches the url than text cannot be extracted
					else :
						# Just log info of the resource
						print(url)
						print(response.info().get_content_type())
						NO_PDF += 1	
					# unknown url domain
				# if not pdf
			# if row in csv contains url column	
		# close for row in csv		
	# close with-statement

	print(f"{NO_PDF} UNKNOWN_FORMAT files found")
	print(f"{len(PDF_TO_TXT)} pdf files found")
	print(f"{len(EURLEX_FROM_HTML)} eurlex html files found")
	print(f"{len(GAZZA_FROM_HTML)} gazzetta html files found")
	print(f"{len(UNSCR_FROM_PFD)} unscr pdf files found")
	print(f"{len(PARL_FROM_HTM)} parlamento htm files found")

	# Write all extracted laws' texts to file
	list_to_file(PDF_TO_TXT,"frompdf")
	list_to_file(EURLEX_FROM_HTML,"eurlexhtml")
	list_to_file(GAZZA_FROM_HTML,"gazzettahtml")
	list_to_file(UNSCR_FROM_PFD,"unscrPDF")
	list_to_file(PARL_FROM_HTM,"parlhtm")

		
def list_to_file(text_l, name_prefix):
	for i in range( 0 , len(text_l) ):
		filename = f"output/{name_prefix}_{i}"
		with open(filename,'w') as fd:
			fd.write(text_l[i])

if __name__ == '__main__':
	main()