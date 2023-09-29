from bs4 import BeautifulSoup, Comment
import sys
import requests
from PyPDF2 import PdfReader
from io import BytesIO
from urllib.parse import urljoin,urlparse
from pathlib import Path
import cld3


from socket import gaierror
from urllib3.exceptions import MaxRetryError
from requests.exceptions import ConnectionError

start_url = "https://www.cybersecurityosservatorio.it/it/Services/documents.jsp"

USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36"

def main():
    response = requests.get(start_url)
    soup = BeautifulSoup(response.content.decode(),'html.parser')
    
    for el in soup.select("div.section > div"):
        div_id = el.get('id')
        if div_id != 'desc':
            query = ""
            if div_id == "divLeggiNorme" : 
                query = f"div#{div_id} > div > div"
                for el1 in soup.select(query):
                    query1 = f"div#{el1.get('id')} li "
                    counter = 0
                    for li in soup.select(query1):
                        link = li.find("a").get("href")
                        if link == "#" : 
                            print(f"[MISSING] : Skipping when counter is {counter}")
                            continue
                        #print(f"Found link {link} in li {counter + 1} of {div_id}")
                        counter += 1
                        txt = process_link(link)
                        if txt == "":
                            continue
                        lang = get_lang(txt)
                        domain = urlparse(link).netloc
                        filename = f"cybersecurityosservatorio_it/{lang}/{div_id}/{el1.get('id')}/{counter:02d}-{domain}"
                        file = mkdir_ifnotexist(filename)
                        file.write_text(txt)
            else :
                query = f"div#{div_id} li"
                counter = 0 
                for li in soup.select(query):
                    link = li.find("a").get("href")
                    #print(f"Found link {link} in li {counter + 1} of {div_id}")
                    counter += 1
                    txt = process_link(link)
                    if txt == "":
                            continue
                    lang = get_lang(txt)
                    domain = urlparse(link).netloc
                    filename = f"cybersecurityosservatorio_it/{lang}/{div_id}/{counter:02d}-{domain}"
                    file = mkdir_ifnotexist(filename)
                    file.write_text(txt)


def get_lang(txt):
    return cld3.get_language(txt).language

def mkdir_ifnotexist(filename):
    output_file = Path(filename)
    output_file.parent.mkdir(exist_ok=True, parents=True)
    return output_file

def pdf_to_txt(http_response : requests.Response) -> str :
    bytesio = BytesIO(http_response.content)
    pdf = PdfReader(bytesio)
    text = ""
    for page_n in range(0 , len(pdf.pages) ):
        text += pdf.pages[page_n].extract_text()
    return text

def process_link(url : str) -> str :
    #print(f"[HTTP] : Get {url}")
    try :
        _headers = {'User-Agent': USER_AGENT}
        response = requests.get(url,headers=_headers)
    except (gaierror, MaxRetryError, ConnectionError):
        print(f"[FAILURE] : Cannot HTTP/GET {url}. Maybe it doesn't exist anymore")
        return ""
    
    if (
        not response.encoding is None and 
        not response.apparent_encoding is None and 
        response.encoding.capitalize() != response.apparent_encoding.capitalize() ):
        print(f"[WARNING] : Encoding is {response.encoding} but apparent is {response.apparent_encoding}.")

    if "application/pdf" in response.headers["Content-Type"] :
        return pdf_to_txt(response)
    else : 
        soup = BeautifulSoup(response.content.decode(encoding=response.apparent_encoding),'html.parser',)
        if "eur-lex.europa.eu/legal-content/" in url and "ALL" in url:

            
            relative = soup.select_one("a#format_language_table_PDF_EN").get("href")
            link = urljoin(url,relative)
            response1 = requests.get(link)
            if not "application/pdf" in response1.headers["Content-Type"]:
                print(f"[FAILURE] : Despite further parsing cannot get pdf for {url}. Tried also to get {link}")
                return ""
            else :
                return pdf_to_txt(response1)
        elif "eur-lex.europa.eu/legal-content/" in url and "TXT/HTML" in url :
        #    return process_link(url.replace("TXT/HTML","TXT/PDF"))
            tags = soup.select_one("body").find_all(string=True)
            txt = ""
            for tag in tags :
                if isinstance(tag,Comment):
                    continue
                if tag.name == "img":
                    if not tag['alt'] is None : 
                        txt += f"{tag['alt']}"
                else:
                    txt += f"{tag}"
            return txt
        elif "eur-lex.europa.eu/legal-content/" in url and "TXT/?" in url :
            return process_link(url.replace("TXT/","TXT/PDF/"))
        elif "gazzettaufficiale.it" in url :
            
            # Grab the nav-bar element and extract iframe url
            left_iframe = soup.find(id="leftFrame")['src']
            # Fetch iframe page
            url2 = urljoin(url, left_iframe)
            #print(f"[HTTP] : Get {url2}")
            res2 = requests.get(url2)
            # Extract list of all articles of the law
            articles_tree = BeautifulSoup(res2.content.decode(),'html.parser').find(id="albero")
            items = articles_tree.find_all("li")
            article_text = ""
            # Extract title of the law 
            for txt1 in soup.find(id="testa_atto").find_all(string=True):
                article_text += f"{txt1}"
                # For each item pointing to the law's article
            for it in items :
                if not it.has_attr('class') :
                    # Extract the url of the page containing the article
                    subarticle_rel = it.find_all('a')[0]['href']
                    # Resolve relative to absolute url
                    subarticle_url = urljoin(url2,subarticle_rel)
                    # Fetch the page
                    #print(f"[HTTP] : Get {subarticle_url}")
                    res3 = requests.get(subarticle_url)
                    subarticle_soup = BeautifulSoup(res3.content.decode(),'html.parser')
                    # Extract the text and notes
                    subarticle_text = subarticle_soup.find_all("span",class_="dettaglio_atto_testo")[0].find_all(string=True)
                    for para in subarticle_text :
                        article_text += f"{para}"
            return article_text
        elif "garanteprivacy.it" in url :
            content = soup.select_one("div#div-to-print")
            if content is None :
                print(f"[FAILURE] : Content for {url} doesn't exist")
                return ""
            tags = content.find_all(string=True)
            txt = ""
            for tag in tags :
                if isinstance(tag,Comment):
                    continue
                if tag.name == "img":
                    if not tag['alt'] is None : 
                        txt += f"{tag['alt']}"
                else:
                    txt += f"{tag}"
            return txt
        elif "penale.it" in url :
            tags = soup.select_one("td.testo").find_all(string=True)
            txt = ""
            for tag in tags :
                if isinstance(tag,Comment):
                    continue
                if tag.name == "img":
                    if not tag['alt'] is None : 
                        txt += f"{tag['alt']}"
                else:
                    txt += f"{tag}"
            return txt
        else:
            print(f"[NO PDF] : {url}")
            #print(f"[NO PDF] : Content-Type is {response.headers['Content-Type']}")
            if "interlex.it" in url : 
                print(response.content.decode())
    return ""


if __name__ == "__main__":
    sys.exit(main())