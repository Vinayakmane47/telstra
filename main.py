from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import requests

def geocode_address(address):
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": address, "format": "json", "limit": 1}
    response = requests.get(url, params=params, headers={"User-Agent": "5G-Checker-App"})
    data = response.json()
    if data:
        return float(data[0]["lat"]), float(data[0]["lon"])
    else:
        raise ValueError("Address could not be geocoded")

# Install driver only once
driver_path = ChromeDriverManager().install()

from fastapi import FastAPI, Form, Request, WebSocket
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import overpy
import concurrent.futures
import time
import os
import asyncio
import json

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

def check_single_address(addr, driver_path):
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-setuid-sandbox")
    options.add_argument("--disable-blink-features=AutomationControlled")

    service = Service(driver_path)
    driver = webdriver.Chrome(service=service, options=options)
    
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
    except Exception:
        return (addr, False)
    finally:
        driver.quit()

@app.get("/", response_class=HTMLResponse)
async def form_page(request: Request):
    return templates.TemplateResponse("form.html", {"request": request, "results": None})

@app.post("/", response_class=HTMLResponse)
async def handle_form(request: Request, address: str = Form(...), n: int = Form(...), workers: int = Form(...), radius: int = Form(1000)):
    try:
        lat, lon = geocode_address(address)
    except ValueError as e:
        return templates.TemplateResponse("form.html", {"request": request, "results": [], "error": str(e)})

    addresses = fetch_nearby_addresses(lat, lon, radius=radius)
    addresses.insert(0, address)
    addresses_to_check = addresses[:n]
    results = run_parallel_check(addresses_to_check, workers)
    return templates.TemplateResponse("form.html", {"request": request, "results": results, "error": None})

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    data = await websocket.receive_json()
    address = data["address"]
    n = int(data["n"])
    workers = int(data["workers"])
    radius = int(data.get("radius", 1000))

    try:
        lat, lon = geocode_address(address)
    except ValueError as e:
        await websocket.send_text(json.dumps({"error": str(e)}))
        await websocket.close()
        return

    addresses = fetch_nearby_addresses(lat, lon, radius=radius)
    addresses.insert(0, address)
    addresses_to_check = addresses[:n]

    loop = asyncio.get_event_loop()
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        futures = []
        for addr in addresses_to_check:
            start_time = time.time()
            futures.append(loop.run_in_executor(executor, check_single_address, addr, driver_path))

        for future in asyncio.as_completed(futures):
            result = await future
            elapsed = round(time.time() - start_time, 2)
            await websocket.send_text(json.dumps({
                "addr": result[0],
                "available": result[1],
                "time": elapsed
            }))
    
    await websocket.close()