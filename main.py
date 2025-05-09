from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import overpy
import concurrent.futures
import time
import os

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

def fetch_nearby_addresses(lat, lon, radius=1000):
    api = overpy.Overpass()
    query = f"""
    [out:json];
    (
      way["building"](around:{radius},{lat},{lon});
    );
    out center;
    """
    result = api.query(query)
    addresses = []
    for way in result.ways:
        tags = way.tags
        if "addr:street" in tags and "addr:housenumber" in tags:
            address = f'{tags["addr:housenumber"]} {tags["addr:street"]} Melbourne VIC'
            addresses.append(address)
    return addresses

def check_single_address(addr):
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-gpu")
    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 20)
    try:
        driver.get("https://www.telstra.com.au/internet/5g-home-internet")
        wait.until(EC.presence_of_element_located((By.ID, "tcom-sq-main-input")))
        input_box = driver.find_element(By.ID, "tcom-sq-main-input")
        input_box.clear()
        input_box.send_keys(addr)
        time.sleep(1)
        input_box.send_keys("\b\b")
        time.sleep(1)
        input_box.send_keys(addr[-2:])
        time.sleep(2)
        wait.until(EC.presence_of_all_elements_located(
            (By.CSS_SELECTOR, "#adddress-autocomplete-results li.address-option")
        ))
        suggestions = driver.find_elements(By.CSS_SELECTOR, "#adddress-autocomplete-results li.address-option")
        if suggestions:
            driver.execute_script("arguments[0].click();", suggestions[0])
            time.sleep(3)
        else:
            return (addr, False)
        result_header = wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "h3.tcom-sq__result__header__title"))
        )
        is_available = "eligible for 5G Home Internet" in result_header.text
        return (addr, is_available)
    except Exception as e:
        return (addr, False)
    finally:
        driver.quit()

def run_parallel_check(addresses, workers):
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(check_single_address, addr) for addr in addresses]
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())
    return results

@app.get("/", response_class=HTMLResponse)
async def form_page(request: Request):
    return templates.TemplateResponse("form.html", {"request": request, "results": None})

@app.post("/", response_class=HTMLResponse)
async def handle_form(request: Request, lat: float = Form(...), lon: float = Form(...), n: int = Form(...), workers: int = Form(...)):
    addresses = fetch_nearby_addresses(lat, lon)
    addresses.insert(0, "340 Lygon Street Carlton VIC")
    addresses_to_check = addresses[:n]
    results = run_parallel_check(addresses_to_check, workers)
    return templates.TemplateResponse("form.html", {"request": request, "results": results})


