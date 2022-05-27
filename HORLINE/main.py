
#------------------------------------------------------------------------------------------------------------
# This script needs some more optimization and code refactoring.

# Instead of speed, I decided to choose data collection and processing reliability -
# so most of the data is processed locally and works with pre-downloaded files.

# - first we download the html-pages with the lists of represented items;
# - then we collect a list of product links and save them in SQLite-d.base;
# - then we start collecting data from each page - by following links from the DB;
# - data collection is designed in a way that if the site detects "our presence" and denies the request.
#   We will be able to continue collecting data from the link where the request was denied;

#------------------------------------------------------------------------------------------------------------



from base.functions import BaseFunc

scrap = BaseFunc()

for page in range(scrap.first_page, scrap.number_of_pages_with_data):
    # collecting pages with car lists
    scrap.get_src_of_pages(page)

# from pages with car lists - collecting links for all cars
scrap.get_links_of_cars()

# we have 4445 "car links" with data
for one_try in range(1, scrap.number_of_car_links):
    # collecting every html-page from "car links"
    scrap.get_src_of_car_page(scrap.get_car_url())

# creating of csv-file for data
scrap.create_csv_file()

# collecting data from every html-page from "car links"
# and filling the csv-file with this data
scrap.get_data_and_fill_csv_table()
