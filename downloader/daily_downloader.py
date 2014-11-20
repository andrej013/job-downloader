'''
Created on Oct 30, 2014

@author: Andrej
'''
import mysql.connector
from mysql.connector import errorcode

class DailyDownloader(object):
    '''
    get list of locations and job names from SQL
    '''
    
    def get_locations(self):
        locations = []
        try:
            cnx = mysql.connector.connect(user='root', password='13243546',
                                          host='127.0.0.1',
                                          database='job_analytics')
            cursor = cnx.cursor()            
            query = ("select city,state from cities order by location_id")
            cursor.execute(query)
            for city_state in cursor:
                print str(city_state[0])+', '+str(city_state[1])
                locations.append(str(city_state[0])+', '+str(city_state[1]))
            cursor.close()
            cnx.close()
            return locations
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                print("Something is wrong with your user name or password")
            elif err.errno == errorcode.ER_BAD_DB_ERROR:
                print("Database does not exists")
            else:
                print(err)
            return False
        else:
            cnx.close()
            return False
        return False
    
    def get_job_keywords(self):
        job_names=['java', 'python', 'big data', 'software engineer', 'Scala','R','Perl','SQL','C#','Ruby','C++','JavaScript','PHP','HTML5','CSS']
        return job_names
    
    def __init__(self):
        '''
        Constructor
        '''
        


        