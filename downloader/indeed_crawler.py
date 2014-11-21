'''
Created on Nov 15, 2014

@author: Andrej
'''
import mechanize
import pyes
from bs4 import BeautifulSoup
import unicodedata
from datetime import datetime, timedelta
from random import randint
import threading
import urllib2

es_conn = pyes.ES('127.0.0.1:9200')
indeed = "http://www.indeed.com"
advanced_job_search_site = 'http://www.indeed.com/advanced_search'


class CompanyCityMetroState(object):
    def __init__(self, company, city, regional_center, state):
        '''
        Constructor
        '''
        self.company = company
        self.city = city
        self.regional_center = regional_center
        self.state = state
        
    def get_company(self):
        return self.company
    def get_city(self):
        return self.city
    def get_regional_center(self):
        return self.regional_center
    def get_state(self):
        return self.state
          
class Settings(object):
    def __init__(self, br, page_no, page=None, next_page_link=None):
        '''
        Constructor
        '''
        self.browser = br
        self.page_number = page_no
        self.page = page
        self.next_page_link = next_page_link
        
    def get_browser(self):
        return self.browser
    
    def get_page(self):
        return self.page
    
    def get_page_number(self):
        return self.page_number
    
    def get_next_page_link(self):
        return self.next_page_link
    
    def increment_page_number_by(self, increment_by):
        self.page_number = self.page_number + 1

class JobAd(object):
    def __init__(self, date, ad_indeed_link, real_job_link, job_title, ad_text, company, city, state, regional_center):
        '''
        Constructor
        '''
        self.date = date
        self.ad_indeed_link = ad_indeed_link
        self.real_job_link = real_job_link
        self.job_title = job_title
        self.ad_text = ad_text
        self.company = company
        self.city = city
        self.state = state
        self.regional_center = regional_center
    
# a hack, website alows up to 50 jobs per page, but this is a workaround
def set_ads_per_page_to_100(br):
    br.form.set_all_readonly(False)
    ads_per_page_control = br.form.find_control("limit")
    # add item 100, because only up to 500 exists on the website
    mechanize.Item(ads_per_page_control, {"contents": "100", "value": "100", "label": "100"})
    br.form.fixup()
    br.form["limit"] = ['100'] 

def remove_sponsored_links(html):
    '''
    remove lines with advertisement dates such as:
    <span class=sdn>Sponsored by <b>Pixured, Inc.</b></span>&nbsp;-&nbsp;<span class=date>30+ days ago</span>
    we want only 100 dates per page for 100 jobs so we remove sponsored links
    '''
    clean_html = ""
    for line in html.splitlines():
        if not("Sponsored by" in line):
            clean_html = clean_html + '\n' + line
    return clean_html

# get list of dates when job ads were posted:
def get_dates(page):
    html = page.get_data()
    clean_html = remove_sponsored_links(html)
    # parse the html
    soup = BeautifulSoup(clean_html)
    # find a list of all span elements
    spans = soup.find_all('span', {'class' : 'date'})
    ad_dates = []
    for span_date in spans:
        string_date = span_date.get_text()
        a = string_date.split(' ')
        if 'day' in string_date:
            if '+' in string_date:  # as in 30+ days ago
                days_ago = randint(30, 60)
            else:
                days_ago = int(a[0])
            ad_date = (datetime.now() - timedelta(days=days_ago)).date()
            ad_dates.append(ad_date)
        elif 'hour' in string_date:
            hours_ago = int(a[0])
            ad_date = (datetime.now() - timedelta(hours=hours_ago)).date()
            ad_dates.append(ad_date)
        else:
            print string_date
            ad_date = datetime.now().date()
            ad_dates.append(ad_date)
    if(len(ad_dates) != 100):
        print 'examine'
    return ad_dates

def get_company_city_metro_state_list(page, regional_center):
    locations_found = 0
    html = page.get_data()
    company_city_state_list = []
    for line in html.split('\n'):
        if 'jobmap[' + str(locations_found) + ']=' in line:
            company = line.split('cmp:\'')[1].split("\',", 1)[0]
            location = line.split('loc:\'')[1].split("\',", 1)[0]
            location_details_list = location.split(',')  # New York, NY  split comma to get city and state
            city = location_details_list[0]
            state = location_details_list[1][1:3]      
            locations_found = locations_found + 1
            company_city_state_list.append(CompanyCityMetroState(company, city, regional_center, state))
    return company_city_state_list


def get_text_from_url(url, number_retried, return_list):
    browser = mechanize.Browser()
    browser.set_handle_robots(False)
    browser.addheaders = [('User-agent', 'Firefox')]
    text = None
    ad_website = None  # initialize so that we do not get an error "ValueError: too many values to unpack" if exception is thrown after one variable is initialized but before the other one is too(other one doesnt exist yet)
    link = indeed + url
    try:
        try:
            page = browser.open(link)
            ad_website = browser.geturl()
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
                return [None, None]
        return_list.append(text)
        return_list.append(ad_website)
        return [text, ad_website]
    except Exception as e:
        print str(e)
        return [None, None]

def get_job_links(br, page_number):
    indeed_link_list = []
    next_page_link = None
    for indeed_link in br.links():            
        if 'this,jobmap[' in str(indeed_link):
            job_title = indeed_link.text
            indeed_link_list.append([indeed_link.url, job_title])
        # look for the next page. example link: /jobs?q=java+developer&l=NYC&start=10
        # or http://www.indeed.com/jobs?q=neurologist&l=nyc&start=10
        # if link with start exists, then we aren't on the last page
        if "start=" + str(page_number * 10) in str(indeed_link):
            next_page_link = indeed + indeed_link.url
    if not next_page_link:
        # end of the search
        return [indeed_link_list, None]
    return [indeed_link_list, next_page_link]

def find_not_downloaded_jobs(conn, ad_dates_list, navigationSettings, company_city_metro_state_list):
    br = navigationSettings.get_browser()
    page_number = navigationSettings.get_page_number()
    indeed_link_and_title_list, next_page_link = get_job_links(br, page_number)
    
    # if next page exists
    if next_page_link:
        navigationSettings.increment_page_number_by(1)
        navigationSettings.next_page_link = next_page_link
    else:
        navigationSettings.next_page_link = None
    # create es query to check if links already exist in es:
    match_queries = []
    for indeed_link_and_title in indeed_link_and_title_list:
        match_queries.append(pyes.MatchQuery('_id', indeed_link_and_title[0]))  # q1 = pyes.MatchQuery('_id', '/rc/clk?jk=d47b332776d1eb80')
                                                                    # q2 = pyes.MatchQuery('_id', '/rc/clk?jk=3d2ed43049102dff')
                                                                    # q = pyes.BoolQuery(should=[q1, q2])
    q = pyes.BoolQuery(should=match_queries)
    results = es_conn.search(q, size='100')  # size 100 because we can have maximally 100 ads per page
    already_downloaded_job_links_set = set()
    for r in results:
        already_downloaded_job_links_set.add(r.indeed_url)
    
    job_ad_list = []
    i = 0
    for indeed_link_and_title in indeed_link_and_title_list:
        if indeed_link_and_title[0] in already_downloaded_job_links_set:
            pass
        else:
            real_job_link = None
            ad_text = None
            job_ad_list.append(JobAd(ad_dates_list[i], indeed_link_and_title[0], real_job_link, indeed_link_and_title[1],
                                 ad_text, company_city_metro_state_list[i].get_company(),
                                 company_city_metro_state_list[i].get_city(), company_city_metro_state_list[i].get_state(),
                                 company_city_metro_state_list[i].get_regional_center()))
        i = i + 1   
    return job_ad_list
            
def download_job_ads(navigationSettings, job_ads_to_download_list):
    print 'a'
    # text, ad_website = get_text_from_url(link.url, 0)
    for jobAd in job_ads_to_download_list:
        print jobAd.ad_indeed_link
        ad = []
        t = threading.Thread(target=get_text_from_url, args=(jobAd.ad_indeed_link, 0, ad))
        t.start()
        
        number_of_seconds_to_look_for_text = 15
        t.join(number_of_seconds_to_look_for_text)
        if(len(ad) == 0):
            text = None  # text not found, list still empty
            ad_website = None
        else:
            try:
                text, ad_website = ad  # "p._target
            except Exception as e:
                print str(e)
                text, ad_website = [None, None]
        
        jobAd.real_job_link = ad_website
        jobAd.ad_text = text
        print jobAd.job_title
        
#         if text != "":  # it is empty if the page cant be opened - we get 404 not found
#             print link.url + " " + str(len(ad_dates_list)) + " " + str(len(company_city_metro_state_list))
#             try:
#                 url_text_map[link.url] = [ad_dates_list[i], ad_website, job_title, company_city_metro_state_list[i], text]
#             except Exception as e:
#                 print e
    
    
def save_ads_to_es(job_ads_to_download_list):  # url_text_map[link.url] = [ad_dates_list[i], ad_website, text]
    for job in job_ads_to_download_list:
        # date_website_text_list = url_text_map.get(url)
        es_conn.index({"date":job.date,
                    "website_url":job.real_job_link,
                    "job_title": job.job_title,
                    "company": job.company,
                    "city": job.city,
                    "state": job.state,
                    "regional_center": job.regional_center,
                    "ad_text": job.ad_text,
                    "indeed_url": job.ad_indeed_link}, "skill-analyzer", "indeed-jobs", job.ad_indeed_link)
    print 'saved to ES'

def open_next_page(navigationSettings):
    br = navigationSettings.get_browser()
    next_page_link = navigationSettings.get_next_page_link()
    if next_page_link:
        try:
            next_page = br.open(next_page_link)  # see common errors for this
        except urllib2.URLError as e:
            print str(e)
            print 'retry:'
            try:
                next_page = br.open(next_page_link)
            except urllib2.URLError as e:
                print 'failed again'
                print str(e)
                # if it fails twice, go to the next city (maybe save the city name to the file for future) 
                navigationSettings.page = None
                navigationSettings.next_page_link = None
                return
        navigationSettings.page = next_page  # if we are on page 1, we opened page 2, but still do not have link for page 3 (in this case, next page link)
    else:  # it was the end of the results,next page doesnt exist so start searching the results for the next city
        navigationSettings.page = None    

def download_jobs(job_title, location):
    # set settings for browser
    br = mechanize.Browser()
    br.set_handle_robots(False)
    br.addheaders = [('User-agent', 'Firefox')]
    
    try:
        br.open(advanced_job_search_site)
    except Exception as e:  #catch urllib2.URLError: <urlopen error [Errno 11001] getaddrinfo failed>
        print str(e)
        #retry 
        try:
            br.open(advanced_job_search_site)
        except Exception as e:
            print str(e)
            print job_title+' '+location
            return
        
    br.select_form('sf')
    br.form[ 'as_ttl' ] = job_title
    br.form[ 'l' ] = location
    
    set_ads_per_page_to_100(br)
    try:
        page = br.submit()
    except Exception as e:
        print str(e)
        return
    
    regional_center = location.split(',')[0]  # aka city
    page_number = 1
    navigationSettings = Settings(br=br, page_no=page_number, page=page)
    while True:  # for i in range(1,20):
        print job_title + " " + location + ", page number: " + str(navigationSettings.get_page_number())
        print 'get dates'
        dates = get_dates(navigationSettings.get_page())
        print 'get comapny city and state list'
        company_city_metro_state_list = get_company_city_metro_state_list(navigationSettings.get_page(), regional_center)
        if len(company_city_metro_state_list) == 0:
            break
        print 'get job ads that need to be downloaded'
        job_ads_to_download_list = find_not_downloaded_jobs(es_conn, dates, navigationSettings, company_city_metro_state_list)
        print 'number of jobs that needs to be downloaded: ' + str(len(job_ads_to_download_list))
        download_job_ads(navigationSettings, job_ads_to_download_list)
        print 'save to ES'
        save_ads_to_es(job_ads_to_download_list)
        print 'open next page'
        open_next_page(navigationSettings)
        print '\n'
        if(navigationSettings.page is None):
            print 'end'
            break


    
