
import re
import requests
from bs4 import BeautifulSoup
import numpy as np

headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.114 Safari/537.36"
    }
url = "https://www.rightmove.co.uk/property-to-rent/find.html?searchLocation=SW1V&useLocationIdentifier=true&locationIdentifier=OUTCODE%5E2510&rent=To+rent&radius=0.0&_includeLetAgreed=on"
res = requests.get(url, headers=headers) 
# check status
res.raise_for_status()  
soup = BeautifulSoup(res.text, "html.parser")
# This gets the list of apartments
apartments = soup.find_all("div", class_="PropertyCard_propertyCardContainerWrapper__mcK1Z propertyCard-details")
index = 1
apart = apartments[1]
raw_value = apart.find("span", class_="PropertyDetailsLozenge_imageCount___OS_A")
img_tag = raw_value.find('img') if raw_value else None
label = img_tag['aria-label'] if img_tag else None
match = re.search(r'(\d+)', label) if img_tag else None
image_count = int(match.group(1)) if match else np.nan

print("✅ Number of images:", image_count)

