import datetime
import re
import time
import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import logging
from .database.db import init_db, insert_dataframe_to_db

logger = logging.getLogger(__name__)

ts = time.time()
ct = datetime.datetime.now()
print("current time:", ct)

def extract(apart, 
            type, 
            class_name, 
            extra_type = None, 
            href = False,
            image_count = False):
    if (extra_type is None) & (not href) :
        raw_value = apart.find(type, class_=class_name)
        value = raw_value.get_text().strip() if raw_value else None
    elif href:
        raw_value = apart.find(type, class_=class_name)
        value = raw_value.get('href')
    elif image_count:
        raw_value = apart.find(type, class_=class_name)
        img_tag = raw_value.find(extra_type) if raw_value else None
        label = img_tag['aria-label'] if img_tag else None
        match = re.search(r'(\d+)', label) if img_tag else None
        value = int(match.group(1)) if match else None
    else:
        raw_value = apart.find(type, class_=class_name)
        value = raw_value.find(extra_type).text.strip() if raw_value and raw_value.find(extra_type) else None
    return value


def extract_transport_info(driver, url):
    driver.get(url)

    try:
        # Check if the cookie banner is present
        cookie_buttons = driver.find_elements(By.ID, "onetrust-accept-btn-handler")
        if cookie_buttons:
            WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
            )
            cookie_buttons[0].click()
            logger.info("✅ Accepted cookies")
        else:
            logger.info("ℹ️ Cookie banner not present (already accepted?)")
    except Exception as e:
        logger.error(f"⚠️ No cookie banner or accept failed: {e}")
        return None, None

    try:
        # Click "Stations" tab
        stations_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "Stations-button"))
        )
        driver.execute_script("arguments[0].click();", stations_button)

        # Wait for panel to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "Stations-panel"))
        )

        soup = BeautifulSoup(driver.page_source, "html.parser")
        tabpanel = soup.find("div", id="Stations-panel")
        stations = tabpanel.find_all('li')

        l_name = []
        l_distance = []

        for station in stations:
            name = station.find('span', class_='cGDiWU3FlTjqSs-F1LwK4')
            distance = station.find('span', class_='_1ZY603T1ryTT3dMgGkM7Lg')
            if name and distance:
                l_name.append(name.text.strip())
                l_distance.append(distance.text.strip())

        if l_name and l_distance:
            return l_name, l_distance
        else:
            return None, None

    except Exception as e:
        logger.error(f"❌ Failed to extract station info: {e}")
        return None, None


def retry_extract_transport_info(driver, url, max_retries=3):
    for attempt in range(1, max_retries + 1):
        print(f"🔄 Attempt {attempt} for {url}")
        station, distance = extract_transport_info(driver, url)
        if station and distance:
            return station, distance
        else:
            print(f"⚠️ Failed attempt {attempt}")
            time.sleep(1)  # Wait 1 second before retrying
    return None, None


def run(url: str, 
        headers: dict,
        loc_code: str,
        l_id: list,
        l_property_type: list,
        l_rent: list,
        l_address: list,
        l_bedroom: list,
        l_bathroom: list,
        l_description: list,
        l_num_image: list,
        l_price: list,
        l_base: list,
        l_link: list,
        l_station: list,
        l_distance: list,
        l_station_2nd: list,
        l_distance_2nd: list,
        page: int,
        driver):
    
    res = requests.get(url, headers=headers) 
    # check status
    res.raise_for_status()  
    soup = BeautifulSoup(res.text, "html.parser")

    # This gets the list of apartments
    apartments = soup.find_all("div", class_="PropertyCard_propertyCardContainerWrapper__mcK1Z propertyCard-details")
    index = 1

    for apart in apartments:
        # create id: page number + item number + run time
        id = loc_code + str(page+1) + "|" + str(index) + "|" + str(ct).replace(" ","|")
        l_id.append(id)
        # extract property type
        property_type = extract(apart, "span", "PropertyInformation_propertyType__u8e76")
        l_property_type.append(property_type)
        # extract rent
        rent = extract(apart, "div", "PropertyPrice_price__VL65t")
        l_rent.append(rent)
        # extract address
        address = extract(apart, "address", "PropertyAddress_address__LYRPq")
        l_address.append(address)
        # extract number of bedroom
        bedroom = extract(apart, "span", "PropertyInformation_bedroomsCount___2b5R")
        l_bedroom.append(bedroom)
        # extract number of bathroom
        bathroom = extract(apart, "div", "PropertyInformation_bathContainer__ut8VY", extra_type="span")
        l_bathroom.append(bathroom)
        # extract full description
        description = extract(apart, "p", "PropertyCardSummary_summary__oIv57")
        l_description.append(description)
        # extract number of image
        num_image = extract(apart, "span", "PropertyDetailsLozenge_imageCount___OS_A", extra_type="img", image_count=True)
        l_num_image.append(num_image)
        # extract rent details
        match = re.search(r'\d[\d,]*', rent)
        price = int(match.group(0).replace(',', ''))
        l_price.append(price)
        l_base.append(rent[-3:])
        # extract link
        link = extract(apart, "a", "propertyCard-link", href=True)
        link = "https://www.rightmove.co.uk" + link
        l_link.append(link)

        # scrap the transport info
        station, distance = retry_extract_transport_info(driver, link)

        if (station is not None) & (distance is not None):
            l_station.append(station[0]) 
            l_distance.append(distance[0])
            l_station_2nd.append(station[1]) 
            l_distance_2nd.append(distance[1])
        else:
            l_station.append(np.nan) 
            l_distance.append(np.nan)
            l_station_2nd.append(np.nan) 
            l_distance_2nd.append(np.nan)

        index = index + 1
    return 



def wrapper(postcode: str,
            loc_code: str,
            pages: int = 42):
    headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.114 Safari/537.36"
        }
    index = 0
    url_first_page = f"https://www.rightmove.co.uk/property-to-rent/find.html?searchLocation={postcode}&useLocationIdentifier=true&locationIdentifier=OUTCODE%{loc_code}&radius=0.0&_includeLetAgreed=on&index=0&sortType=6&channel=RENT&transactionType=LETTING&displayLocationIdentifier={postcode}].html"
    res = requests.get(url_first_page, headers=headers) 
    # check status
    res.raise_for_status()  
    soup = BeautifulSoup(res.text, "html.parser")
    raw = soup.find("div", class_="ResultsCount_resultsCount__Kqeah")
    number_of_results = raw.find("span").text.strip() if raw and raw.find("span") else None
    number_of_results = int(number_of_results.replace(",", ""))

    l_id = []
    l_property_type = []
    l_address = []
    l_rent = []
    l_bedroom = []
    l_bathroom = []
    l_description = []
    l_num_image = []
    l_price = []
    l_base = []
    l_link = []
    l_station = []
    l_distance = []
    l_station_2nd = []
    l_distance_2nd = []
    driver = webdriver.Safari()

    for p in range(pages):
        print(f"inspecting page: {p+1}...")
        url = f"https://www.rightmove.co.uk/property-to-rent/find.html?searchLocation={postcode}&useLocationIdentifier=true&locationIdentifier=OUTCODE%{loc_code}&radius=0.0&_includeLetAgreed=on&index={index}&sortType=6&channel=RENT&transactionType=LETTING&displayLocationIdentifier={postcode}].html"
    
        run(url, 
            headers,
            loc_code,
            l_id,
            l_property_type,
            l_rent,
            l_address,
            l_bedroom,
            l_bathroom,
            l_description,
            l_num_image,
            l_price,
            l_base,
            l_link,
            l_station,
            l_distance,
            l_station_2nd,
            l_distance_2nd,
            p,
            driver
            )
        index = index + 24
        if index >= number_of_results:
            break
    
    driver.quit()
    
    data = {"unique_id": l_id,
            "postcode": [postcode for i in range(len(l_id))],
            "property_type": l_property_type,
            "address": l_address,
            "rent": l_rent,
            "price": l_price,
            "base": l_base,
            "number_of_bedroom": l_bedroom,
            "number_of_bathroom": l_bathroom,
            "description": l_description,
            "num_image": l_num_image,
            "link": l_link,
            "nearest_station": l_station,
            "distance_to_station": l_distance,
            "second_nearest_station": l_station_2nd,
            "distance_to_second_station": l_distance_2nd,}
    
    df_result = pd.DataFrame(data)

    length_original = len(df_result)
    df_result = df_result.drop_duplicates(subset=["postcode",
                                                  "property_type",
                                                  "address",
                                                  "rent",
                                                  "price",
                                                  "base",
                                                  "number_of_bedroom",
                                                  "number_of_bathroom",
                                                  "description",
                                                  "link",])
    length_dedup = len(df_result)
    if length_dedup < length_original:
        print(f"{length_original - length_dedup} duplicates found")

    df_result["run_time"] = ct

    # score properties
    # df_result = sc.combined_score(df_result,
    #                               "price",
    #                               "number_of_bedroom",
    #                               "number_of_bathroom")

    # insert the data into local sql db
    insert_dataframe_to_db(df_result)
    return df_result

if __name__ == "__main__":
    from sqlalchemy import inspect
    from .database.db import engine
    inspector = inspect(engine)
    print(f"Tables in DB: {inspector.get_table_names()}")
    if "flats_to_rent" not in inspector.get_table_names():
        init_db()
    # location_name = "Elephant-and-Castle"
    # location_code = "5E70312"
    # location_name = "Richmond-Upon-Thames"
    # location_code = "5E61415"
    # location_name = "Islington"
    # location_code = "5E93965"
    postcode = "E14"
    location_code = "5E749"
    df_result = wrapper(postcode, location_code, pages=1)
    df_result.to_csv(f"/Users/sqwu/property_api/property_api/files/output/result_{postcode}_{str(ct)}.csv")


