import os
import asyncio

from utils import run, Days, Meals, Foods

from dotenv import load_dotenv
from playwright import async_api
from playwright.async_api import Browser, Page

load_dotenv()

username = os.getenv("fh_USERNAME")
password = os.getenv("fh_PASSWORD")

day = Days.MONDAY
meal = Meals.DINNER
food = Foods.EITHER

settings = {
    "username": username,
    "password": password,
    "day": day,
    "meal": meal,
    "food": food,
}


async def main():
    async with async_api.async_playwright() as playwright:
        browser: Browser = await playwright.chromium.launch(headless=False)
        page: Page = await browser.new_page()

        return await run(page, **settings)

result = asyncio.run(main())
print(result)
