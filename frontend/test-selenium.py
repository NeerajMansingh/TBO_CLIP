import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

options = Options()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')

try:
    driver = webdriver.Chrome(options=options)
    driver.get("http://localhost:5174")
    
    # Wait for the search box to appear
    wait = WebDriverWait(driver, 10)
    search_box = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'textarea')))
    
    # Type query
    search_box.send_keys("Rajasthan trip")
    
    # Find and click search button
    search_btn = driver.find_element(By.XPATH, "//button[contains(., 'Generate Trip')]")
    search_btn.click()
    
    time.sleep(3)
    
    # Check browser logs for React errors
    for entry in driver.get_log('browser'):
        if entry['level'] == 'SEVERE':
            print(f"BROWSER ERROR: {entry['message']}")
            
except Exception as e:
    print(f"SCRIPT ERROR: {e}")
finally:
    if 'driver' in locals():
        driver.quit()
