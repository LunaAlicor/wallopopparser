import time
import traceback
import selenium
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from peewee import *
import re
import os
import logging
from datetime import datetime


def parsing(count, d, r='1'):
    try:
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
            user = ForeignKeyField(User, backref='items')
            update_time = CharField(null=True)


        db.connect()
        db.create_tables([User, Item])


        urls = ["https://it.wallapop.com", "https://es.wallapop.com", "https://uk.wallapop.com"]
        test_url = "https://it.wallapop.com/app/search?category_ids=12465&filters_source=category_navigation&longitude=12.4942&latitude=41.8905"
        catalogs = None
        if r == '1':
            catalogs = {"1": "https://it.wallapop.com/app/search?filters_source=category_navigation&longitude=12.4942&latitude=41.8905",
                        "2": "https://it.wallapop.com/moto",
                        "3":"https://it.wallapop.com/motori-e-accessori",
                        "4": "https://it.wallapop.com/tv-audio-e-fotocamere",
                        "5": "https://it.wallapop.com/telefonia-e-accessori",
                        "6": "https://it.wallapop.com/sport-e-tempo-libero",
                        "7": "https://it.wallapop.com/bambini-e-neonati",
                        "8": "https://it.wallapop.com/industria-e-agricoltura",
                        "9": "https://it.wallapop.com/app/search?category_ids=12465&filters_source=category_navigation&longitude=12.4942&latitude=41.8905",
                        "10": "https://it.wallapop.com/app/search?filters_source=quick_filters&longitude=12.4942&latitude=41.8905&condition=new",
                        "11": "https://it.wallapop.com/app/search?category_ids=12465&filters_source=quick_filters&longitude=12.4942&latitude=41.8905&condition=new",
                        "12": "https://it.wallapop.com/app/search?category_ids=12579&filters_source=quick_filters&longitude=12.4942&latitude=41.8905&condition=new",
            }
        elif r == '2':
            catalogs = {
                "1": "https://es.wallapop.com/app/search?filters_source=category_navigation&longitude=-3.69196&latitude=40.41956",
                "2": "https://es.wallapop.com/motos",
                "3": "https://es.wallapop.com/motor-y-accesorios",
                "4": "https://es.wallapop.com/tv-audio-foto",
                "5": "https://es.wallapop.com/moviles-telefonos",
                "6": "https://es.wallapop.com/deporte-y-ocio",
                "7": "https://es.wallapop.com/ninos-y-bebes",
                "8": "https://es.wallapop.com/industria-agricultura",
                "9": "https://es.wallapop.com/moda-y-complementos",
                "10": "https://es.wallapop.com/app/search?filters_source=quick_filters&longitude=-3.69196&latitude=40.41956&condition=new",
                "11": "https://es.wallapop.com/app/search?category_ids=12465&filters_source=quick_filters&longitude=-3.69196&latitude=40.41956&condition=new",
                "12": "https://es.wallapop.com/app/search?category_ids=12579&filters_source=quick_filters&longitude=-3.69196&latitude=40.41956&condition=new",
                }
        elif r == '4':
            catalogs = {
                "1": "https://pt.wallapop.com/app/search?filters_source=category_navigation&longitude=-9.142685&latitude=38.736946",
                "2": "https://pt.wallapop.com/moto",
                "3": "https://pt.wallapop.com/motores-e-acessorios",
                "4": "https://pt.wallapop.com/tv-audio-fotografia",
                "5": "https://pt.wallapop.com/telemoveis-e-acessorios",
                "6": "https://pt.wallapop.com/desporto-e-lazer",
                "7": "https://pt.wallapop.com/criancas-e-bebes",
                "8": "https://pt.wallapop.com/industria-e-agricultura",
                "9": "https://pt.wallapop.com/app/search?category_ids=12465&filters_source=category_navigation&longitude=-9.142685&latitude=38.736946",
                "10": "https://pt.wallapop.com/app/search?filters_source=quick_filters&longitude=-9.142685&latitude=38.736946&condition=new",
                "11": "https://pt.wallapop.com/app/search?category_ids=12465&filters_source=quick_filters&longitude=-9.142685&latitude=38.736946&condition=new",
                "12": "https://pt.wallapop.com/app/search?category_ids=12579&filters_source=quick_filters&longitude=-9.142685&latitude=38.736946&condition=new",
                }
        elif r == '5':
            catalogs = {
                "1": "https://fr.wallapop.com/app/search?filters_source=category_navigation&longitude=-0.118092&latitude=51.509865",
                "2": "https://fr.wallapop.com/motos",
                "3": "https://fr.wallapop.com/app/search?category_ids=12800&filters_source=category_navigation&longitude=-0.118092&latitude=51.509865",
                "4": "https://fr.wallapop.com/image-et-son",
                "5": "https://fr.wallapop.com/telephonie",
                "6": "https://fr.wallapop.com/app/search?category_ids=12579&filters_source=category_navigation&longitude=-0.118092&latitude=51.509865",
                "7": "https://fr.wallapop.com/app/search?category_ids=12461&filters_source=category_navigation&longitude=-0.118092&latitude=51.509865",
                "8": "https://fr.wallapop.com/app/search?category_ids=20000&filters_source=category_navigation&longitude=-0.118092&latitude=51.509865",
                "9": "https://fr.wallapop.com/app/search?category_ids=12465&filters_source=category_navigation&longitude=-0.118092&latitude=51.509865",
                "10": "https://fr.wallapop.com/app/search?filters_source=quick_filters&longitude=-0.118092&latitude=51.509865&condition=new",
                "11": "https://fr.wallapop.com/app/search?category_ids=12465&filters_source=quick_filters&longitude=-0.118092&latitude=51.509865&condition=new",
                "12": "https://fr.wallapop.com/app/search?category_ids=12579&filters_source=quick_filters&longitude=-0.118092&latitude=51.509865&condition=new",
                }

        test_url = catalogs[d]

        chrome_options = Options()
        chrome_options.add_argument("--headless")
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
        for _ in range(count):
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
            try:
                driver.get(stuff)
                WebDriverWait(driver, 10).until(
                    lambda driver: driver.execute_script('return document.readyState') == 'complete'
                )
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
                try:
                    if seller_name.get_text(strip=True) == "unknown":
                        continue
                except AttributeError:
                    continue

                stuff_name = soup.find('h1', class_="item-detail_ItemDetail__title__wcPRl mt-2")
                # html_text = '''твой HTML код'''
                # Найдём тег, содержащий текст "Modificato"

                user_link_tag = soup.find('a', rel='nofollow', attrs={'aria-label': 'Link for user info'})
                user_link = "None"
                registration_info = "None"
                registration_date = "None"
                sales_count = "None"
                # Найти элемент с классом, содержащим информацию о времени последней модификации
                modification_info = soup.find('span', class_="item-detail-stats_ItemDetailStats__description__vjz96")

                # Проверить, найден ли элемент и получить текст
                if modification_info:
                    last_modified = modification_info.get_text(strip=True)
                    if "giorno" in last_modified:
                        last_modified = last_modified.replace("giorno", "дней назад").replace("fa", "")
                    elif "minuti" in last_modified:
                        last_modified = last_modified.replace("minuti", "минут(у) назад").replace("fa", "")
                    elif "ore" in last_modified:
                        last_modified = last_modified.replace("ore", "час(ов) назад").replace("fa", "")
                    print(f"Дата последней активности: {last_modified}")
                else:
                    last_modified = "Дата последней активности не найдена"
                    print(last_modified)

                if user_link_tag and 'href' in user_link_tag.attrs:
                    user_link = user_link_tag['href']
                    print(f"User link: https://it.wallapop.com{user_link}/info")
                    driver.get(f"https://it.wallapop.com{user_link}/info")
                    WebDriverWait(driver, 10).until(
                        lambda driver: driver.execute_script('return document.readyState') == 'complete'
                    )
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
                    try:
                        Item.create(
                            name=stuff_name.get_text(strip=True),
                            image_link=image_links[0] if image_links else "Не найдено",
                            stuff_url=stuff,
                            update_time=last_modified.replace("Modificato ", "")+" "+datetime.now().strftime("%d/%m/%Y %H:%M"),
                            user=user
                        )
                    except Exception:
                        Item.create(
                            name="Не найдено",
                            image_link="Не найдено",
                            stuff_url="Не найдено",
                            update_time="Не найдено",
                            user="Не найдено"
                        )
            except Exception:
                continue
            else:
                pass
        time.sleep(5)
        driver.quit()
    except Exception as e:
        log_dir = 'logs'
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        log_file = os.path.join(log_dir, 'log.txt')
        logging.basicConfig(filename=log_file, level=logging.ERROR,
                            format='%(asctime)s - %(levelname)s - %(message)s')
        logging.error("Произошла ошибка", exc_info=True)


if __name__ == "__main__":
    parsing(1, d="9", r='1')
