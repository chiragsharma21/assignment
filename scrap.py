import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
import re
import pymongo
client = pymongo.MongoClient("mongodb+srv://ashu200221:B3GJ8OUArQUvOsLv@cluster0.ke63ugn.mongodb.net/?retryWrites=true&w=majority")
db = client["db"]
collection = db["scrap"]
collection.delete_many({})
# setup for web viewing
def get_driver(link):
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # Run Chrome in headless mode (no GUI)
    
    driver = webdriver.Chrome(ChromeDriverManager().install())
    driver.get(link)
    
    content = driver.page_source
    
    soup = BeautifulSoup(content, 'html.parser')
    driver.quit()
    return soup

def average_sal(data):
    cur_fnd = ['₹']
    for ki in cur_fnd:
        if ki in data:
            cur_fnd = ki
            break
    if type(cur_fnd) != str:
        return ['₹', '0', 0]

    if '-' in data:
        b = data.replace(',', '').split('-')
        sal1 = ''
        sal2 = ''
        for i in b[0]:
            if i in [str(g) for g in range(0, 10)]:
                sal1 += i
        for i in b[1]:
            if i in [str(g) for g in range(0, 10)]:
                sal2 += i
        salary_xx = [int(sal1), int(sal2)]
        avg_sal = round(np.average(salary_xx))
    else:
        sal1 = ''
        b = data.replace(',', '')
        for i in b:
            if i in [str(g) for g in range(0, 10)]:
                sal1 += i
        salary_xx = [int(sal1)]
        avg_sal = round(np.average(salary_xx))

    if salary_xx == [0, 0]:
        avg_sal = 0

    if 'year' in data:
        avg_sal = avg_sal
    elif 'month' in data:
        avg_sal *= 12
    elif 'day' in data:
        avg_sal *= 365
    avg_sal2 = "{:,}".format(avg_sal)
    return [cur_fnd, avg_sal2, round(int(avg_sal))]

def scraping(page, collection):

    jobs = page.find_all("div", class_="job_seen_beacon")
    for job in jobs:
        company_name = job.find("span", class_="css-1x7z1ps eu4oa1w0").text
        company_location = job.find("div", class_="css-t4u72d eu4oa1w0").text

        # Initialize salary variables with default values
        min_salary = "0"
        max_salary = "0"
        salary = "0"

        try:
            salary_elem = job.find("div", class_="metadata salary-snippet-container")
            if salary_elem:
                salary = salary_elem.text
                cleaned_str = re.sub(r'[^\d₹.,]', '', salary)
                salary_list = cleaned_str.split('₹')
                if len(salary_list) == 2:
                    min_salary = salary_list[1]
                    max_salary = "none"
                else:
                    min_salary = salary_list[1]
                    max_salary = salary_list[2]
        except:
            pass 

        job_title = job.find("a", class_="jcs-JobTitle css-jspxzf eu4oa1w0").text

        link_tag = job.find("a", class_="jcs-JobTitle css-jspxzf eu4oa1w0")
        link_half = link_tag["href"]
        base_url = "https://in.indeed.com"
        full_url = f"{base_url}{link_half}"

        avg_salary_data = average_sal(salary)
        avg_salary = avg_salary_data[1]

        job_info = {
            "job_title": job_title,
            "min_salary": min_salary,
            "max_salary": max_salary,
            "avg_salary(Yearly)": avg_salary,
            "company_name": company_name,
            "company_location": company_location,
            "link": full_url
        }

        collection.insert_one(job_info)

for i in range(0, 50, 10):
    page_html = get_driver(f"https://in.indeed.com/jobs?q=python+developer&start={i}&vjk=74df27615b32ca3c")
    scraping(page_html, collection)
client.close()
