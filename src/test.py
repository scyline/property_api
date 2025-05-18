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
    session = SessionLocal()
    reset_flats_table(session)
    try:
        flats = []
        for _, row in df.iterrows():
            flat = FlatsToRent(
                unique_id=row["Unique_Id"],
                location=row["Location"],
                property_type=row["Property_Type"],
                address=row["Address"],
                rent=row["Rent"],
                price=row["Price"],
                base=row["Base"],
                number_of_bedroom=int(row["Number_Of_Bedroom"]) if pd.notnull(row["Number_Of_Bedroom"]) else None,
                number_of_bathroom=int(row["Number_Of_Bathroom"]) if pd.notnull(row["Number_Of_Bathroom"]) else None,
                description=row["Description"],
                link = row["Link"],
                run_time=row["Run_Time"].date() # if isinstance(row["Run_Time"], datetime) else datetime.now().date()

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
        id = str(page+1) + "|" + str(index) + "|" + str(ct).replace(" ","|")
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



def wrapper(location_name: str,
            pages: int = 42):
    headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.114 Safari/537.36"
        }
    index = 0
    url_first_pqge = f"https://www.rightmove.co.uk/property-to-rent/find.html?searchLocation={location_name}+%28London+Borough%29&useLocationIdentifier=true&locationIdentifier=REGION%5E93965&rent=To+rent&radius=0.0&propertyTypes=flat&_includeLetAgreed=on&index={index}&sortType=6&channel=RENT&transactionType=LETTING&displayLocationIdentifier={location_name}"
    
    res = requests.get(url_first_pqge, headers=headers) 
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
        url = f"https://www.rightmove.co.uk/property-to-rent/find.html?searchLocation={location_name}+%28London+Borough%29&useLocationIdentifier=true&locationIdentifier=REGION%5E93965&rent=To+rent&radius=0.0&propertyTypes=flat&_includeLetAgreed=on&index={index}&sortType=6&channel=RENT&transactionType=LETTING&displayLocationIdentifier={location_name}"
        run(url, 
            headers,
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

    data = {"Unique_Id": l_id,
            "Location": [location_name for i in range(len(l_id))],
            "Property_Type": l_property_type,
            "Address": l_address,
            "Rent": l_rent,
            "Price": l_price,
            "Base": l_base,
            "Number_Of_Bedroom": l_bedroom,
            "Number_Of_Bathroom": l_bathroom,
            "Description": l_description,
            "Link": l_link }
    
    df_result = pd.DataFrame(data)

    length_original = len(df_result)
    df_result = df_result.drop_duplicates(subset=["Location",
                                                  "Property_Type",
                                                  "Address",
                                                  "Rent",
                                                  "Price",
                                                  "Base",
                                                  "Number_Of_Bedroom",
                                                  "Number_Of_Bathroom",
                                                  "Description",
                                                  "Link"])
    length_dedup = len(df_result)
    if length_dedup < length_original:
        print(f"{length_original - length_dedup} duplicates found")

    df_result["Run_Time"] = ct

    # insert the data into local sql db
    insert_dataframe_to_db(df_result)
    return df_result

if __name__ == "__main__":
    location_name = "Islington"
    df_result = wrapper(location_name)
    df_result.to_csv(f"/Users/sqwu/property_api/property_api/files/output/result_{location_name}_{str(ct)}.csv")
