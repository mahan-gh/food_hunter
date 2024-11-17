import time
import random
from enum import Enum

from playwright.async_api import Page, Locator


class Days(Enum):
    SATURDAY = "شنبه"
    SUNDAY = "یکشنبه"
    MONDAY = "دوشنبه"
    TUESDAY = "سه شنبه"
    WEDNESDAY = "چهارشنبه"
    THURSDAY = "پنجشنبه"


class Meals(Enum):
    BREAKFAST = 1
    LUNCH = 2
    DINNER = 3


class Foods(Enum):
    FIRST = 0
    SECOND = 1
    EITHER = 2


settings = {}

url = "http://food.guilan.ac.ir"

# سلف علوم پایه
reserve_panel_url = "http://food.guilan.ac.ir/nurture/user/multi/reserve/showPanel.rose?selectedSelfDefId=4"


async def get_meal_el(page):
    day_text_el: Locator = page.get_by_text(settings.get("day").value)

    return await day_text_el.evaluate_handle(
        f"element => element.parentElement.querySelectorAll('tr > td[width=\"12%\"]')[{settings.get('meal').value}]")


async def meal_is_checked(page):
    meal_el = await get_meal_el(page)

    checkbox_el = await meal_el.evaluate_handle(f"element => element.querySelectorAll('input[type=checkbox]')[{settings.get('food').value}]")
    checkbox_el = checkbox_el.as_element()

    return await checkbox_el.is_checked(), checkbox_el


async def hunt_food(page):
    while True:
        confirm_btn_el = await page.query_selector("#doReservBtn")

        meal_el = await get_meal_el(page)

        food = settings.get('food')

        # sell icon <img src="/images/sell.png" ...>
        if food == Foods.EITHER:
            buy_btn_el = await meal_el.evaluate_handle("element => element.querySelectorAll('img[src=\"/images/buy.png\"]'))")
        else:
            buy_btn_el = await meal_el.evaluate_handle(
                f"element => Array.from(element.querySelectorAll('img[src=\"/images/buy.png\"]')).at({food.value})")

        buy_btn_el = buy_btn_el.as_element()

        if buy_btn_el:
            await buy_btn_el.click()
            await confirm_btn_el.click()
            checked, _ = await meal_is_checked(page)
            if checked:
                return "successfully hunt a food"
            else:
                return "cant reserve the food, probably the price is out of budget or someone hunt it first!"

        else:
            time.sleep(random.uniform(1, 3))
            try:
                await page.reload()
                continue
            except Exception as e:
                return f"cant not go to the website url: {e}"


async def login(page):
    try:
        await page.goto(url)
    except Exception as e:
        return False, f"cant not go to the website url: {e}"

    cancel_redirect = await page.wait_for_selector("#btn-redirect-cancel", timeout=1000)
    if cancel_redirect:
        await cancel_redirect.click()

    username_el = await page.query_selector("#username")
    await username_el.fill(settings.get('username'))
    password_el = await page.query_selector("#password")
    await password_el.fill(settings.get('password'))
    btn_el = await page.query_selector("#login_btn_submit")
    await btn_el.click()

    await page.wait_for_load_state()

    if "res=5" in page.url:
        return False, "username or password is incorrect"
    return True


async def run(page: Page, **kwargs):
    settings.update(**kwargs)

    successful, msg = await login(page)
    if not successful:
        return msg

    try:
        await page.goto(reserve_panel_url)
    except Exception as e:
        return f"cant not go to the reserve panel url: {e}"

    await page.wait_for_load_state()

    first_food_checked, first_food_checked_el = await meal_is_checked(page)
    if first_food_checked:
        return "you already reserved the first meal"

    meal_el = await get_meal_el(page)
    number_of_foods = await meal_el.evaluate_handle("element => element.querySelectorAll('tbody > tr').length")
    number_of_foods = int(str(number_of_foods))

    if number_of_foods > 1:
        second_food_checked, second_food_checked_el = await meal_is_checked(page)
        if second_food_checked:
            return "you already reserved the second meal"

    confirm_btn_el = await page.query_selector("#doReservBtn")

    if settings.get('food') == Foods.EITHER:
        first_disabled = await first_food_checked_el.is_disabled()

        if first_disabled:
            return await hunt_food(page)

        # we can reserve normally (random)
        if number_of_foods > 1:
            checked_el = first_food_checked_el if random.randint(
                0, 1) else second_food_checked_el
        else:
            checked_el = first_food_checked_el

        await checked_el.click()
        await confirm_btn_el.click()
        checked, checked_el = await meal_is_checked(page)

        if checked:
            return "reserved normally"
        else:
            return "cant reserve the food, probably the price is out of budget"

    else:
        meal_el = await get_meal_el(page)
        checkbox_el = await meal_el.evaluate_handle(f"element => element.querySelectorAll('input[type=checkbox]')[{settings.get('food').value}]")

        disabled = await checkbox_el.is_disabled()
        if disabled:
            return await hunt_food(page)

        # we can reserve normally
        await checkbox_el.click()
        await confirm_btn_el.click()
        checked, checkbox_el = await meal_is_checked(page)

        if checked:
            return "reserved normally"
        else:
            return "cant reserve the food, probably the price is out of budget"
