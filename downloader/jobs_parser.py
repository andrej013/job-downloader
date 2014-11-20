import mechanize
# import mysql.connector
# from mysql.connector import errorcode
# from pyes import *
import pyes
from bs4 import BeautifulSoup
import unicodedata
from datetime import datetime, timedelta
from random import randint
import threading
import urllib2

# TODO: save the name of the city from the search-bar, as regional center
    
def text_exists(url):
    return False
    # check if job ad with the url already exists

    # ad_dates_list[i], ad_website, job_title, company_city_state_list, text
def save_ads(url_text_map, regional_center):  # url_text_map[link.url] = [ad_dates_list[i], ad_website, text]
    for url in url_text_map:
        date_website_text_list = url_text_map.get(url)
        conn.index({"date":date_website_text_list[0],
                    "website_url":date_website_text_list[1],
                    "job_title": date_website_text_list[2],
                    "company": date_website_text_list[3][0],
                    "city": date_website_text_list[3][1],
                    "state": date_website_text_list[3][2],
                    "regional_center": regional_center,
                    "ad_text": date_website_text_list[4],
                    "indeed_url": url}, "skill-analyzer", "indeed-jobs", url)
    print 'saved to ES'


def get_text_from_url(url, number_retried, return_list):
    browser = mechanize.Browser()
    browser.set_handle_robots(False)
    browser.addheaders = [('User-agent', 'Firefox')]
    link = indeed + url
    try:
        page = browser.open(link)
        ad_website = browser.geturl()
        # page = browser.submit()
        html = page.get_data()
        
        # html = urlopen(link).read()
        soup = BeautifulSoup(html)
        [x.extract() for x in soup.find_all('script')]
        text = soup.get_text() 
        text = unicodedata.normalize('NFKD', text).encode('utf8', 'ignore')
    except Exception as e:  # handle 404 not found
        if number_retried < 1:
            print ('first error opening link: ' + url + '\n' + str(e))
            text, ad_website = get_text_from_url(url, 1, return_list)
        else:
            print ('second error opening link: ' + url + '\n' + str(e))
            return ["", ""]
    return_list.append(text)
    return_list.append(ad_website)
    return [text, ad_website]
    
def get_stop_words():
    with open('stop_words.txt') as f:
        content = f.readlines()
    content = [x.strip('\n') for x in content]
    return content

def get_java_words():
    with open('java_words.txt') as f:
        content = f.readlines()
    content = [x.strip('\n') for x in content]
    return content

def remove_sponsored_links(html):
    '''
    remove lines with advertisment dates such as:
    <span class=sdn>Sponsored by <b>Pixured, Inc.</b></span>&nbsp;-&nbsp;<span class=date>30+ days ago</span>
    we want only 10 dates per page for 10 jobs so we remove sponsored links
    '''
    clean_html = ""
    for line in html.splitlines():
        if not("Sponsored by" in line):
            clean_html = clean_html + '\n' + line
    return clean_html

def get_dates(page):
    html = page.get_data()
    clean_html = remove_sponsored_links(html)
    # parse the html
    soup = BeautifulSoup(clean_html)
    # find a list of all span elements
    spans = soup.find_all('span', {'class' : 'date'})
    # span_dates = spans[2:]
    ad_dates = []
    for span_date in spans:
        string_date = span_date.get_text()
        a = string_date.split(' ')
        if 'day' in string_date:
            # print 'days'
            if '+' in string_date:  # as in 30+ days ago
                days_ago = randint(30, 60)
            else:
                days_ago = int(a[0])
            ad_date = (datetime.now() - timedelta(days=days_ago)).date()
            ad_dates.append(ad_date)
        elif 'hour' in string_date:
            # print 'hours'
            hours_ago = int(a[0])
            ad_date = (datetime.now() - timedelta(hours=hours_ago)).date()
            ad_dates.append(ad_date)
        else:
            print string_date
            ad_date = datetime.now().date()
            ad_dates.append(ad_date)
    if(len(ad_dates) != 10):
        print 'examine'
    return ad_dates

def get_company_city_state_list(page):
    locations_found = 0
    html = page.get_data()
    company_city_state_list = []
    for line in html.split('\n'):
        if 'jobmap[' + str(locations_found) + ']=' in line:
            company = line.split('cmp:\'')[1].split("\',", 1)[0]
            location = line.split('loc:\'')[1].split("\',", 1)[0]
            location_details_list = location.split(',')  # New York, NY  split comma to get city and state
            print company
            city = location_details_list[0]
            state = location_details_list[1][1:3]      
            locations_found = locations_found + 1
            company_city_state_list.append([company, city, state])
    return company_city_state_list

def find_ads(conn, ad_dates_list, br, page_number, company_city_state_list):
    i = 0
    url_text_map = {}
    for link in br.links():            
        if 'this,jobmap[' in str(link):
            job_title = link.text
            text = text_exists(link.url)
            if not text:
                # text, ad_website = get_text_from_url(link.url, 0)
                ad=[]
                t = threading.Thread(target=get_text_from_url, args=(link.url, 0, ad))
                t.start()
                
                number_of_seconds_to_look_for_text = 10
                t.join(number_of_seconds_to_look_for_text)
                if(len(ad)==0):
                    text=""     #text not found, list still empty
                else:
                    text, ad_website = ad#"p._target
                
                if text != "":  # it is empty if the page cant be opened - we get 404 not found
                    print link.url + " " + str(len(ad_dates_list)) + " " + str(len(company_city_state_list))
                    try:
                        url_text_map[link.url] = [ad_dates_list[i], ad_website, job_title, company_city_state_list[i], text]
                    except Exception as e:
                        print e
                i = i + 1
        # look for the next page. example link: /jobs?q=java+developer&l=NYC&start=10
        # or http://www.indeed.com/jobs?q=neurologist&l=nyc&start=10
        if "start=" + str(page_number * 10) in str(link):
            next_page_link = indeed + link.url
            try:
                next_page = br.open(next_page_link) #see common errors for this
            except urllib2.URLError as e:
                print str(e)
                print 'retry:'
                try:
                    next_page = br.open(next_page_link)
                except urllib2.URLError as e:
                    print 'failed again'
                    print str(e)
                    #if it fails twice, go to the next city (maybe save the city name to the file for future) 
                    return [br, page_number, url_text_map, "end_of_search"]
            page_number = page_number + 1
            return [br, page_number, url_text_map, next_page]
    # this is the end of the search, there is no next page if we get here
    return [br, page_number, url_text_map, "end_of_search"]


conn = pyes.ES('127.0.0.1:9200')
indeed = "http://www.indeed.com"

def download_jobs(job_name, location):
    br = mechanize.Browser()
    br.set_handle_robots(False)
    br.addheaders = [('User-agent', 'Firefox')]
    
    br.open(indeed)
    br.select_form('jobsearch')
    br.form[ 'q' ] = job_name
    br.form[ 'l' ] = location
    page = br.submit()
    
    regional_center = location.split(',')[0]  # aka city
    page_number = 1
    settings = [br, page_number]
    while True:  # for i in range(1,20):
        print job_name+" "+location
        try:
            try:
                dates = get_dates(page)
            except Exception as e:
                print '1'+str(e)
            try:
                company_city_state_list = get_company_city_state_list(page)
            except Exception as e:
                print '2'+str(e)
            try:
                settings = find_ads(conn, dates, settings[0], settings[1], company_city_state_list)
            except Exception as e:
                print '3'+str(e)
            try:
                save_ads(settings[2], regional_center)
            except Exception as e:
                print '4'+str(e)
        except:
            break;
        page = settings[3]
        print str(settings[1])
        if(settings[3] == 'end_of_search'):
            print 'end'
            break


class Settings(object):

    def __init__(self, br, page_no, url_txt_map, next_pg):
        '''
        Constructor
        '''
        browser = br
        page_number = page_no
        url_text_map = url_txt_map
        next_page = next_pg
        
    def get_browser(self):
        return self.browser
    
    def get_next_page(self):
        return self.next_page
    
    def get_page_number(self):
        return self.page_number
    
    def get_url_text_map(self):
        return self.url_text_map
    
    



