from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)

def extract_transport_info(driver, url):
    driver.get(url)

    try:
        # Check if the cookie banner is present
        cookie_buttons = driver.find_elements(By.ID, "onetrust-accept-btn-handler")
        if cookie_buttons:
            WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
            )
            cookie_buttons[0].click()
            print("✅ Accepted cookies")
        else:
            print("ℹ️ Cookie banner not present (already accepted?)")
    except Exception as e:
        print("⚠️ Cookie handling failed:", e)

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
                print(f"{name.text.strip()} - {distance.text.strip()}")

        if l_name and l_distance:
            return l_name, l_distance
        else:
            return None, None

    except Exception as e:
        # print("❌ Failed to extract station info:", e)
        logger.error(f"❌ Failed to extract station info: {e}")
        return None, None



if __name__ == "__main__":
    driver = webdriver.Safari()
    url = "https://www.rightmove.co.uk/properties/117605504#/?channel=RES_LET"
    extract_transport_info(driver, url)
    driver.quit()