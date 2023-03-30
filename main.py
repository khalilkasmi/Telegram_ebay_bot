import requests
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from datetime import datetime
import time

EBAY_KLEINANZEIGEN_URLS = [
    "https://www.ebay-kleinanzeigen.de/s-wohnung-mieten/berlin/anzeige:angebote/preis::1000/c203l3331r10+wohnung_mieten.swap_s:nein+wohnung_mieten.verfuegbarm_i:5%2C+wohnung_mieten.verfuegbary_i:2023%2C+wohnung_mieten.zimmer_d:2%2C+options:wohnung_mieten.built_in_kitchen_b",
    "https://www.ebay-kleinanzeigen.de/s-wohnung-mieten/halle/anzeige:angebote/preis::500/c203l2409r5+wohnung_mieten.swap_s:nein+wohnung_mieten.verfuegbarm_i:5%2C+wohnung_mieten.verfuegbary_i:2023%2C+wohnung_mieten.zimmer_d:2%2C+options:wohnung_mieten.built_in_kitchen_b"
]
TELEGRAM_BOT_TOKEN = "<TELEGRAM_BOT_KEY>"
CHAT_ID = "<TELEGRAM_CHAT_ID>"
DELAY = 60  # Check for new ads every 60 seconds

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "TE": "Trailers",
}


async def send_telegram_message(ad_info):
    async with aiohttp.ClientSession() as session:
        message_text = f"New apartment ad:\n\n{ad_info}"
        payload = {
            "chat_id": CHAT_ID,
            "text": message_text
        }

        telegram_api_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        async with session.post(telegram_api_url, data=payload) as response:
            if response.status == 200:
                print(f"[{datetime.now()}] Sent message: {message_text}")
            else:
                print(f"[{datetime.now()}] Failed to send message: {message_text}")


def get_apartment_ads(soup):
    ads = soup.find_all("article", class_="aditem")
    apartment_ads = []

    for ad in ads:
        link = ad.find("a", class_="ellipsis")
        if link:
            url = f'https://www.ebay-kleinanzeigen.de{link["href"]}'
            title = link.text.strip()

            location_element = ad.find("div", class_="aditem-main--top--left")
            if location_element:
                location = location_element.text.strip()
            else:
                location = "N/A"

            ad_post_time = ad.find("div", class_="aditem-main--top--right")
            if ad_post_time:
                time = ad_post_time.text.strip()
            else:
                time = "N/A"

            size_and_rent_element = ad.find("p", class_="text-module-end")
            if size_and_rent_element:
                size_and_rent = size_and_rent_element.text.strip()
            else:
                size_and_rent = "N/A"

            apartment_ads.append((url, title, location, time, size_and_rent))

    return apartment_ads


def fetch_html(url):
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.text
    else:
        raise Exception(f"Failed to fetch HTML from {url}")


async def main():
    seen_apartment_ads = set()

    print(f"[{datetime.now()}] Starting main loop")

    while True:
        for url in EBAY_KLEINANZEIGEN_URLS:
            try:
                print(f"[{datetime.now()}] Fetching HTML from {url}")
                html_content = fetch_html(url)
                soup = BeautifulSoup(html_content, "html.parser")
                apartment_ads = get_apartment_ads(soup)

                for ad in apartment_ads:
                    if ad[0] not in seen_apartment_ads:
                        ad_info = f"Title: {ad[1]}\nLocation: {ad[2]}\nTime: {ad[3]}\nSize and Rent: {ad[4]}\nURL: {ad[0]}"
                        await send_telegram_message(ad_info)
                        seen_apartment_ads.add(ad[0])

                print(f"[{datetime.now()}] Finished processing {len(apartment_ads)} apartment ads")
                time.sleep(DELAY)
            except Exception as e:
                print(f"[{datetime.now()}] Error: {e}")
                time.sleep(DELAY)


if __name__ == "__main__":
    asyncio.run(main())


