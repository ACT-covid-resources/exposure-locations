import sys, os
from bs4 import BeautifulSoup
from inscriptis import get_text

# Given a CSS Rule, and a blob of HTML, return the blob of HTML that matches
def css_filter(css_filter, html_content):
  soup = BeautifulSoup(html_content, "html.parser")
  html_block = ""
  for item in soup.select(css_filter, separator=""):
    html_block += str(item)

  return html_block + "\n"

if __name__ == "__main__":


  with open('locations.html') as f:
    contents = f.read()
    print(contents)

  # Skip the headers/footers
  page_content = css_filter("#TOCScannableArea", contents)

  # Get the text-only representation of the HTML
  page_content_text = get_text(page_content)
  
  # Output to locations.txt for commit
  with open('locations.txt', 'w') as txtoutput:
    txtoutput.write(page_content_text)
    
  # Remove downloaded HTML file
  os.remove('locations.html')
