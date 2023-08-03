python3 -m venv venv
source venv/bin/activate
python3 -m pip install -r requirements.txt
python3 -m spacy download en_core_web_lg
scrapy startproject automotive
cp LawSpider.py automotive/automotive/spiders
rm automotive/automotive/settings.py
cp settings.py automotive/automotive/settings.py
