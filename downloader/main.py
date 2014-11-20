'''
Created on Oct 30, 2014

@author: Andrej
'''
import daily_downloader as d
# from jobs_parser import download_jobs
from downloader import indeed_crawler

downloader = d.DailyDownloader()
locations = downloader.get_locations()
jobs = downloader.get_job_keywords()

#locations = ['Laredo, Texas', 'Memphis, Tennessee', 'Seattle, Washington', 'Denver, Colorado', 'Washington, District of Columbia', 'Boston, Massachusetts', 'Nashville, Tennessee', 'Baltimore, Maryland', 'Oklahoma City, Oklahoma', 'Louisville, Kentucky', 'Portland, Oregon', 'Las Vegas, Nevada', 'Milwaukee, Wisconsin', 'Albuquerque, New Mexico', 'Tucson, Arizona', 'Fresno, California', 'Sacramento, California', 'Long Beach, California', 'Kansas City, Missouri', 'Mesa, Arizona', 'Virginia Beach, Virginia', 'Atlanta, Georgia', 'Colorado Springs, Colorado', 'Omaha, Nebraska']
for job in jobs:
    for location in  locations:
        indeed_crawler.download_jobs(job, location)