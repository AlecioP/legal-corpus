import re
import csv
from PyPDF2 import PdfReader

REGEX = "https?:\\/\\/(?:www\\.)?[-a-zA-Z0-9@:%._\\+~#=]{1,256}\\.[a-zA-Z0-9()]{1,6}\\b(?:[-a-zA-Z0-9()@:%_\\+.~#?&\\/=]*)"

FILE1 = "2023_Vehicle Data Collection A Privacy Policy Analysis and Comparison.pdf"
FILE2 = "COSCA___Plos_One.pdf"

def main():
	reader = PdfReader(FILE2)

	page_n = 0
	for page in reader.pages :
		page_n += 1
		page_txt = page.extract_text()
		matches = re.findall(REGEX,page_txt)
		if len(matches) > 0 :
			print(f"Page {page_n}")
			print(matches)

if __name__ == '__main__':
	main()