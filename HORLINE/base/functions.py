import requests
import csv
import os
from bs4 import BeautifulSoup
import time
from fake_useragent import UserAgent
import sqlite3
import re



class BaseFunc:

    def __init__(self):
        self.conn = sqlite3.connect('DB/URLS.sqlite')
        self.cur = self.conn.cursor()
        self.dirname = '/Users/martinanikola/PycharmProjects/PROPSHT/HORLINE/HTML'
        self.cars_dirname = '/Users/martinanikola/PycharmProjects/PROPSHT/HORLINE/HTML_cars'
        self.files = os.listdir(self.dirname)
        self.cars_files = os.listdir(self.cars_dirname)
        self.dom = 'https://www.kijiji.ca'
        self.url = 'https://www.kijiji.ca/b-cars-trucks/canada/edmonton/k0c174l0'
        self.url2 = 'https://www.kijiji.ca/b-cars-trucks/canada/edmonton/page-2/k0c174l0'
        self.first_page = 1
        self.number_of_pages_with_data = 100
        self.number_of_car_links = 4445
        self.ua = UserAgent()
        self.headers = {
            "Accept": "*/*",
            "User-Agent": self.ua.random
        }



    def get_src_of_pages(self, page):
        """Download the HTML pages into a file for future use
            And return the source of page as a result

            The 'page' argument is the number of the loop
            and we use that number for generate the HTML-file name"""

        url = f"https://www.kijiji.ca/b-cars-trucks/canada/edmonton/page-{page}/k0c174l0"

        req = requests.get(url, headers=self.headers)
        src = req.text

        with open(f'HTML/page{page}.html', 'w') as file:
            file.write(src)

        return src



    def get_links_of_cars(self):
        """collecting a list of product links
        and save them in to SQLite-d.base"""

        count = 0
        links = 0

        for name_of_file in self.files:
            print(f"links from {name_of_file} is scraping...")

            with open(f"HTML/{name_of_file}", "rb") as file:

                count += 1

                src = file.read().decode(errors='replace')
                soup = BeautifulSoup(src, 'lxml')
                uri_tegs = soup.find('div', class_='col-2').find_all('div', class_='title')

                print(f"in file {name_of_file} is {len(uri_tegs)} links")
                time.sleep(2)

                for element in uri_tegs:

                    links += 1

                    url = f"{self.dom}{element.next.next['href']}"

                    self.cur.execute("INSERT INTO urls_list (url, status) VALUES(?,?)", (url, 1))
                    self.conn.commit()

        print(f"we download {links} links from {count} files")


    def get_car_url(self):
        """Get a link from DB-list on the car to collect the data"""

        sqlite_select_query = """SELECT * FROM urls_list"""
        self.cur.execute(sqlite_select_query)

        records = self.cur.fetchall()

        data = []

        for row in records:

            if row[2] != 0:

                data.append(row[1])
                sqlite_change_status = """UPDATE urls_list SET status = 0 WHERE id = ?"""
                self.cur.execute(sqlite_change_status, (row[0],))
                self.conn.commit()
                break
            else:
                continue

        return data


    def get_src_of_car_page(self, url_):

        """Download HTML pages for further data processing
            And return the source pages as a result """

        url = url_

        print(f"getting HTML-data from URL: {url[0]}")


        req = requests.get(url[0], headers=self.headers)
        src = req.text

        try:
            with open(f'HTML_cars/{url[0][-7:]}.html', 'w') as file:
                file.write(src)
            time.sleep(3)

            print('done')

        except Exception as except_mess:
            print(except_mess)

            sqlite_change_status = """UPDATE urls_list SET status = 1 WHERE url = ?"""
            self.cur.execute(sqlite_change_status, (url,))
            print(f'status of url:{url} is changed to "1"')


    def create_csv_file(self):
        """generate a csv-file with the required titles"""

        with open('data.csv', 'w') as file_csv:
            writer = csv.writer(file_csv)
            writer.writerow(
                ('URL', 'Ad', 'id', 'Title', 'Price', 'VIN', 'Posted', 'time', 'Address', 'Description', 'Includes'))


    def get_data_and_fill_csv_table(self):
        """collecting data from each page - by following links from the DB
            And filling the CSV-file"""

        for name_of_file in self.cars_files:
            print(f"Data about car is scraping from {name_of_file} file...")

            data_about_car = []

            with open(f"HTML_cars/{name_of_file}", "rb") as file:

                src = file.read().decode(errors='replace')
                soup = BeautifulSoup(src, 'lxml')
                url_teg = soup.findAll('link')
                urls = [urls for urls in url_teg]

                url = urls[24]['href']
                data_about_car.append(url)

                car_id = url[-7:]
                data_about_car.append(car_id)

                car_title = soup.find('title').text.split(' | ')[0].replace('/w', '').strip()
                data_about_car.append(car_title)

                if soup.find('span', itemprop="price") is None:
                    car_price = 'Please Contact'
                else:
                    car_price = soup.find('span', itemprop="price").text
                data_about_car.append(car_price)

                car_VIN = re.findall(r'\w[0-9A-Z]{16}', src)
                if len(car_VIN) < 4:
                    car_VIN = 'do not have VIN'
                else:
                    car_VIN = re.findall(r'\w[0-9A-Z]{16}', src)[5]
                data_about_car.append(car_VIN)

                car_posted_time = soup.find('div', itemprop='datePosted')['content']

                data_about_car.append(car_posted_time)

                car_address = soup.find('span', itemprop='address').text

                data_about_car.append(car_address)

                car_description = soup.find('div', itemprop='description').text

                data_about_car.append(car_description)

                car_includes = soup.find('div', id='AttributeList').findAll('ul')

                if car_includes:

                    if len(car_includes) < 3:
                        car_includes = 'Car has No extra includes'

                    elif len(car_includes) == 3:
                        car_includes = ''.join(' ' + c if c.isupper() else c for c in car_includes[2].text)

                    elif len(car_includes) > 3:
                        if len(car_includes[3]) != 0:
                            car_includes = ''.join(
                                ' ' + c if c.isupper() else c for c in car_includes[2].text).strip(), ''.join(
                                ' ' + c if c.isupper() else c for c in car_includes[3].text).strip()

                        else:
                            car_includes = ''.join(' ' + c if c.isupper() else c for c in car_includes[2].text).strip()

                data_about_car.append(car_includes)

                with open('data.csv', 'a') as file_cs:
                    writer = csv.writer(file_cs)
                    writer.writerow(data_about_car)