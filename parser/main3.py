import time

import selenium
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from peewee import *


db = SqliteDatabase('wallapop_items.db')


class BaseModel(Model):
    class Meta:
        database = db


class User(BaseModel):
    name = CharField()
    registration_date = CharField()
    sales_count = IntegerField()
    user_link = CharField()
    check_status = BooleanField(default=False)


class Item(BaseModel):
    name = CharField()
    image_link = CharField()
    stuff_url = CharField()
    last_modified = CharField()
    user = ForeignKeyField(User, backref='items')


db.connect()
db.create_tables([User, Item])


urls = ["https://it.wallapop.com", "https://es.wallapop.com", "https://uk.wallapop.com"]
test_url = "https://it.wallapop.com/app/search?category_ids=12465&filters_source=category_navigation&longitude=12.4942&latitude=41.8905"


chrome_options = Options()
driver = webdriver.Chrome(options=chrome_options)
stuff_links = []
driver.get(test_url)
time.sleep(2)
button = driver.find_element(By.ID, "onetrust-accept-btn-handler")
button.click()
driver.refresh()
time.sleep(16)
driver.execute_script("window.scrollBy(0, 5800)")
time.sleep(16)
try:
    button = driver.find_element(By.ID, "btn-load-more")
    button.click()
    print("Кнопка была успешно нажата")
except:
    print("Кнопка не нажата нажмите")
    time.sleep(15)
for _ in range(5):
    time.sleep(1)
    driver.execute_script("window.scrollBy(0, 5800)")
    print("prokrutka")

html = driver.page_source

soup = BeautifulSoup(html, 'html.parser')
links = soup.find_all("a")
for link in links:
    href = link.get("href")
    if href and "item" in href:
        stuff_links.append(href)
        print(href)
for i, stuff in enumerate(stuff_links):
    driver.get(stuff)
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    try:
        image_tags = soup.find_all('img', slot='carousel-content')
        image_links = []
        for img in image_tags:
            src = img.get('src')
            if src:
                image_links.append(src)
        print(f"Ссылка на картинку: {image_links[0]}")
    except IndexError:
        image_links = "Не найдено"
    seller_name = soup.find('h3',
                            class_='text-truncate mb-0 item-detail-header_ItemDetailHeader__text--typoMidM__VeCLc')

    if seller_name.get_text(strip=True) == "unknown":
        continue

    stuff_name = soup.find('h1', class_="item-detail_ItemDetail__title__wcPRl mt-2")
    user_link_tag = soup.find('a', rel='nofollow', attrs={'aria-label': 'Link for user info'})
    user_link = "None"
    registration_info = "None"
    registration_date = "None"
    sales_count = "None"
    modification_info = soup.find('p', string=lambda text: 'Modificato' in text if text else False)
    if modification_info:
        last_modified = modification_info.get_text(strip=True)
        print(f"Дата последней модификации: {last_modified}")
    else:
        last_modified = "Дата последней модификации не найдена"
    if user_link_tag and 'href' in user_link_tag.attrs:
        user_link = user_link_tag['href']
        print(f"User link: https://it.wallapop.com{user_link}/info")
        driver.get(f"https://it.wallapop.com{user_link}/info")
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        registration_info = soup.find('h5', class_='public-profile-more-info_PublicProfileMoreInfo__title__3AXMd mb-1',
                                      string='Membro dal')
        if registration_info:
            registration_date = registration_info.find_next_sibling('span').text.strip()
            print(f"Дата регистрации: {registration_date}")
        else:
            print("Дата регистрации не найдена.")
        sales_counter = soup.find('span', class_='mr-5', attrs={'data-testid': 'sales_counter'})
        if sales_counter:
            sales_count = sales_counter.find('span',
                                             class_='public-profile-header_PublicProfileHeader__text--counter__0CqVQ').text.strip()
            print(f"Количество сделок: {sales_count}")
        else:
            print("Количество сделок не найдено.")
    if sales_count == "0":
        user, created = User.get_or_create(
            name=seller_name.get_text(strip=True),
            user_link=f"https://it.wallapop.com{user_link}/info",
            defaults={'registration_date': registration_date, 'sales_count': sales_count}

        )

        if not created:

            user.sales_count = sales_count
            user.save()

        Item.create(
            name=stuff_name.get_text(strip=True),
            image_link=image_links[0] if image_links else "Не найдено",
            stuff_url=stuff,
            last_modified=last_modified,
            user=user
        )
    else:
        pass
time.sleep(5)
driver.quit()
