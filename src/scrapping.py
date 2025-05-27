import datetime
import re
import time
import pandas as pd
import requests
from bs4 import BeautifulSoup
from .database.db import SessionLocal, FlatsToRent, init_db

init_db()
ts = time.time()
ct = datetime.datetime.now()
print("current time:", ct)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def reset_flats_table(session):
    try:
        session.query(FlatsToRent).delete()
        session.commit()
        print("✅ All records deleted from flats_to_rent.")
    except Exception as e:
        session.rollback()
        print("❌ Error deleting records:", e)
    finally:
        session.close()


def insert_dataframe_to_db(df):
    # session = SessionLocal()
    # reset_flats_table(session)
    session = SessionLocal()

    try:
        flats = []
        for _, row in df.iterrows():
            flat = FlatsToRent(
                unique_id=row["unique_id"],
                location=row["location"],
                property_type=row["property_type"],
                address=row["address"],
                rent=row["rent"],
                price=row["price"],
                base=row["base"],
                number_of_bedroom=int(row["number_of_bedroom"]) if pd.notnull(row["number_of_bedroom"]) else None,
                number_of_bathroom=int(row["number_of_bathroom"]) if pd.notnull(row["number_of_bathroom"]) else None,
                description=row["description"],
                link = row["link"],
                run_time=row["run_time"].date() # if isinstance(row["Run_Time"], datetime) else datetime.now().date()
            )
            flats.append(flat)

        session.bulk_save_objects(flats)
        session.commit()
        print(f"✅ Inserted {len(flats)} records into the database.")
    except Exception as e:
        session.rollback()
        print("❌ Error inserting data:", e)
    finally:
        session.close()

def extract(apart, type, class_name, extra_type = None, href = False):
    if (extra_type is None) & (not href) :
        raw_value = apart.find(type, class_=class_name)
        value = raw_value.get_text().strip() if raw_value else None
    elif href:
        raw_value = apart.find(type, class_=class_name)
        value = raw_value.get('href')
    else:
        raw_value = apart.find(type, class_=class_name)
        value = raw_value.find(extra_type).text.strip() if raw_value and raw_value.find(extra_type) else None
    return value

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
        l_price: list,
        l_base: list,
        l_link: list,
        page: int):
    
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
        # extract rent details
        match = re.search(r'\d[\d,]*', rent)
        price = int(match.group(0).replace(',', ''))
        l_price.append(price)
        l_base.append(rent[-3:])
        # extract link
        link = extract(apart, "a", "propertyCard-link", href=True)
        link = "https://www.rightmove.co.uk" + link
        l_link.append(link)

        index = index + 1
    return 



def wrapper(loc_name: str,
            loc_code: str,
            pages: int = 42):
    headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.114 Safari/537.36"
        }
    index = 0
    url_first_page = f"https://www.rightmove.co.uk/property-to-rent/find.html?&useLocationIdentifier=true&locationIdentifier=REGION%{loc_code}&rent=To+rent&radius=0.0&propertyTypes=flat&_includeLetAgreed=on&index=0&sortType=6&channel=RENT&transactionType=LETTING&displayLocationIdentifier={loc_name}"
    
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
    l_price = []
    l_base = []
    l_link = []

    for p in range(pages):
        print(f"inspecting page: {p+1}...")
        url = f"https://www.rightmove.co.uk/property-to-rent/find.html?&useLocationIdentifier=true&locationIdentifier=REGION%{loc_code}&rent=To+rent&radius=0.0&propertyTypes=flat&_includeLetAgreed=on&index={index}&sortType=6&channel=RENT&transactionType=LETTING&displayLocationIdentifier={loc_name}"
    
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
            l_price,
            l_base,
            l_link,
            p
            )
        index = index + 24
        if index >= number_of_results:
            break

    data = {"unique_id": l_id,
            "location": [loc_name for i in range(len(l_id))],
            "property_type": l_property_type,
            "address": l_address,
            "rent": l_rent,
            "price": l_price,
            "base": l_base,
            "number_of_bedroom": l_bedroom,
            "number_of_bathroom": l_bathroom,
            "description": l_description,
            "link": l_link }
    
    df_result = pd.DataFrame(data)

    length_original = len(df_result)
    df_result = df_result.drop_duplicates(subset=["location",
                                                  "property_type",
                                                  "address",
                                                  "rent",
                                                  "price",
                                                  "base",
                                                  "number_of_bedroom",
                                                  "number_of_bathroom",
                                                  "description",
                                                  "link"])
    length_dedup = len(df_result)
    if length_dedup < length_original:
        print(f"{length_original - length_dedup} duplicates found")

    df_result["run_time"] = ct

    # insert the data into local sql db
    insert_dataframe_to_db(df_result)
    return df_result

if __name__ == "__main__":
    location_name = "Elephant-and-Castle"
    location_code = "5E70312"
    df_result = wrapper(location_name, location_code, pages=3)
    df_result.to_csv(f"/Users/sqwu/property_api/property_api/files/output/result_{location_name}_{str(ct)}.csv")
