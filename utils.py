from lxml import html
import requests
from time import sleep
import csv
import random
from selenium import webdriver
from selenium.common.exceptions import TimeoutException



def scrape_proxies():
    #response = requests.get('http://free-proxy.cz/en/proxylist/main/')
    #page = html.fromstring(response.content)

    #for i in range(0,2):
    #    response = requests.get('http://free-proxy.cz/en/proxylist/main/%d' % i)
    #    sleep(4)
    #    page = html.fromstring(response.content)

    for j in range(0,26)  :  
        #table_row = page.xpath('/html/body/div[2]/div[2]/table/tbody/tr[%d]//text()' % j)
        table_row = ['1','hello', 'whatsup']
        parsed_table_row = table_row[1:]
        print(table_row)

        with open('proxy_list.csv', 'a', newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter = ',', quotechar = '"', quoting=csv.QUOTE_MINIMAL)
            writer.writerow(parsed_table_row)

def generate_random_proxy(filepath):
    list_of_proxies = []

    with open(filepath) as proxy_file:
        for i in proxy_file:
            line = proxy_file.readline()
            list_of_proxies.append(line.strip())
    return random.choice(list_of_proxies)

def filter_proxies(input_path, output_path):
    with open(input_path) as proxy_file:

        counter = 0
        proxies = []

        for line in proxy_file.readlines():
            #l = proxy_file.readline()
            proxies.append(line.strip())

        print(len(proxies))

        print(len(proxies))



        for line in proxies:
            
            try:
                ip = line
                options = webdriver.ChromeOptions()
                options.add_argument('--proxy-server={}'.format(ip))
                options.add_argument('headless')
                driver = webdriver.Chrome('assets/chromedriver2', options=options)
                driver.set_page_load_timeout(5)
                driver.get('https://whatismyipaddress.com/')

                if check_exists_by_xpath(driver, "//div[@id = 'ipv4']"):
                    filtered_ip_list_file = open(output_path, 'a+')
                    filtered_ip_list_file.write(ip)
                    filtered_ip_list_file.write('\n')
                    filtered_ip_list_file.close()
                    print("ip works: %s - Iteration number: %d" % (ip, counter))

                else:
                    print("Page Has Failed To Load")

                counter += 1
                driver.quit()

            except TimeoutException as x:
                print("Taking Too Long: Iteration number %s" %counter)
                counter += 1
                driver.quit()

def check_exists_by_xpath(browser, xpath):
    try:
        browser.find_element_by_xpath(xpath)
    except:
        return False
    return True

def check_exists_by_class_name(browser, class_name):
    try:
        browser.find_elements_by_class_name(class_name)
    except:
        return False
    return True

def sort_and_remove_duplicates_from_list(input_list):
    

    input_list = sorted(input_list)
    output_list = []
    i = 0

    while i < len(input_list) -1:
        if (input_list[i] == input_list[i+1]):
            del input_list[i+1]
            i -= 1
        i += 1

    for item in input_list:
        output_list.append(item)
    return output_list

