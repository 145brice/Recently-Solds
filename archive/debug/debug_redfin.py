import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options

options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

url = "https://www.redfin.com/city/nashville-tn"
driver.get(url)
time.sleep(5)  # Let page load

print(f"Page title: {driver.title}")

# Find all elements containing 'Sold'
elements = driver.find_elements(By.XPATH, "//*[contains(text(),'Sold')]")
print(f"Found {len(elements)} elements with 'Sold'")
for elem in elements:
    xpath = driver.execute_script("""
function gPt(e) {
    if (e.id) return "id(" + e.id + ")";
    if (e.className) return "//*[contains(@class,'" + e.className + "')]";
    var n = e.tagName.toLowerCase();
    if (e.parentNode && e.parentNode.children.length == 1) return gPt(e.parentNode) + "/" + n;
    return gPt(e.parentNode) + "/" + n + "[" + (Array.prototype.indexOf.call(e.parentNode.children, e) + 1) + "]";
}
return gPt(arguments[0]);
""", elem)
    print(f"Tag: {elem.tag_name}, Text: '{elem.text}', XPath: {xpath}")

# Also find all buttons
buttons = driver.find_elements(By.TAG_NAME, "button")
print(f"Found {len(buttons)} buttons")
for btn in buttons[:10]:  # First 10
    if 'sold' in btn.text.lower():
        print(f"Button text: '{btn.text}'")

driver.quit()