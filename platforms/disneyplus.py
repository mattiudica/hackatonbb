import sys
import os
import time
from handle.replace                 import _replace
from datetime import datetime
import json
from common import config
from typing import Counter
path = os.path.abspath('.')
sys.path.insert(1, path)
import db_conection
import requests
from common import config

class DisneyPlus():
    def __init__(self, ott_site_uid, ott_site_country, type):
        self._config              = config()['ott_sites'][ott_site_uid]
        self.insert_many_to_db    = db_conection.insertMany
        self.insert_one_to_db     = db_conection.insert
        self._created_at          = time.strftime("%Y-%m-%d")
        self.country_code         = ott_site_country
        self._platform_code       = self._config['countries'][ott_site_country]
        self.email                = 'support@bb.vision'
        self.password             = 'KLM2012a'
        self.main_url             = 'https://www.disneyplus.com'
        self.payloads             = []
        self._config            = config()['ott_sites'][ott_site_uid]
        self.mongo = mongo()   
        self.titanTopMovies = config()['mongo']['collections']['topMovies']
        self.titanTopSeries = config()['mongo']['collections']['topSeries']

        if type == 'testing':
            self.scraping()

    def scraping(self):

        apis_data = [
        {
            'api' :'https://disney.content.edge.bamgrid.com/svc/content/CuratedSet/version/5.1/region/AR/audience/false/maturity/1499/language/en/setId/8d771d26-3b8d-482d-b797-d580d6fea8da/pageSize/30/page/1',
            'key' :'program',
            'type':'movie'
        },
        {
            'api' :'https://disney.content.edge.bamgrid.com/svc/content/CuratedSet/version/5.1/region/AR/audience/false/maturity/1499/language/en/setId/4d7d6d7f-4b4e-4323-af03-38bc07703ebb/pageSize/30/page/1',
            'key' :'series',
            'type':'series'
        }
        ]

        for data in apis_data:
            api = data['api']
            movie_response = requests.get(api)
            json_api = movie_response.json()
            content_list = json_api['data']['CuratedSet']['items']
            counter = 0
            for content in content_list:
                if counter == 10:
                    break
                #print(str(counter+1),'- ',content['text']['title']['full'][data['key']]['default']['content'])
                title = content['text']['title']['full'][data['key']]['default']['content']

                if data['type'] == 'series':
                    self.create_payload_serie(content,title,self.main_url)
                if data['type'] == 'movie':
                    self.create_payload_movie(content,title,self.main_url)
                counter = counter + 1

    def create_payload_serie(self,content,title,main_url):
        """
        Method to create payloads for series
        Arg: All parameters to build dictionary
        Return: Nothing 

        """

        _id             = content['contentId']
        
        seasons_payload = None
        crew            = None
        deeplink        = main_url+'/series/'+content['text']['title']['slug']['series']['default']['content']+'/'+content['encodedSeriesId']
        year            = content['releases'][0]['releaseYear']
        synopsis        = None
        image           = content['image']['hero_tile']['3.91']['series']['default']['url']
        rating          = content['ratings'][0]['value']
        provider        = None
        genres          = None
        cast            = None
        directors       = None
        availability    = None
        download        = None
        isAdult         = None
        isBranded       = None
        country_list    = None
        package_serie   = [{'Type': 'subscription-vod'}]

        print('----------------------------------')
        print('ADDED ',title,' - ',_id, ' - ',deeplink)

        if content['tags'][0]['type'] == 'disneyPlusOriginal':
            isOriginal = True
        else:
            isOriginal = None
        if year:
            if year < 1900 or year > int(self._created_at.split('-')[0].strip()):
                year = None

        payload_serie = {      
            "PlatformCode":  self._platform_code, #Obligatorio      
            "Id":            _id,                 #Obligatorio
            "Seasons":       seasons_payload,                #Unicamente para series
            "Crew":          crew,
            "Title":         title,       #Obligatorio      
            "CleanTitle":    _replace(title),     #Obligatorio      
            "OriginalTitle": None,                          
            "Type":          'serie',               #Obligatorio      
            "Year":          year,                #Important!     
            "Duration":      None,            
            "Deeplinks": {          
                "Web":       deeplink,            #Obligatorio          
                "Android":   None,          
                "iOS":       None,      
            },      
            "Synopsis":      synopsis,      
            "Image":         image,      
            "Rating":        rating,              #Important!      
            "Provider":      provider,      
            "Genres":        genres,              #Important!      
            "Cast":          cast,      
            "Directors":     directors,           #Important!      
            "Availability":  availability,                #Important!      
            "Download":      download,      
            "IsOriginal":    isOriginal,          #Important!      
            "IsAdult":       isAdult,                #Important!   
            "IsBranded":     isBranded,          #Important!   (PREGUNTAR)
            "Packages":      package_serie,       #Obligatorio      
            "Country":       country_list,      
            "Timestamp":     datetime.now().isoformat(), #Obligatorio      
            "CreatedAt":     self._created_at     #Obligatorio
        }
        self.payloads.append(payload_serie) 

    def create_payload_movie(self,content,title,main_url):
        """
        Method to create payloads for movies
        Arg: All parameters to build dictionary
        Return: Nothing 

        """

        _id             = content['contentId']
        try:
            deeplink        = main_url+'/series/'+content['text']['title']['slug']['program']['default']['content']+'/'+content['encodedSeriesId']
        except:
            deeplink        = main_url+'/series/'+content['text']['title']['slug']['program']['default']['content']+'/'+content['family']['encodedFamilyId']
        year            = content['releases'][0]['releaseYear']
        synopsis        = None
        image           = content['image']['hero_tile']['3.91']['program']['default']['url']
        rating          = content['ratings'][0]['value']
        provider        = None
        genres          = None
        cast            = None
        directors       = None
        availability    = None
        download        = None
        isAdult         = None
        isBranded       = None
        country_list    = None
        package_movie   = [{'Type': 'subscription-vod'}]

        print('----------------------------------')
        print('ADDED ',title,' - ',_id, ' - ',deeplink)

        if content['tags'][0]['type'] == 'disneyPlusOriginal':
            isOriginal = True
        else:
            isOriginal = None
        
        if year:
            if year < 1900 or year > int(self._created_at.split('-')[0].strip()):
                year = None

        payload_movie = {      
            "PlatformCode":  self._platform_code,    #Obligatorio      
            "Id":            _id,                    #Obligatorio
            "Title":         title,                  #Obligatorio      
            "CleanTitle":    _replace(title),        #Obligatorio      
            "OriginalTitle": None,                          
            "Type":          'movie',                  #Obligatorio      
            "Year":          year,                   #Important!     
            "Duration":      None,          
            "Deeplinks": {          
                "Web":       deeplink,               #Obligatorio          
                "Android":   None,          
                "iOS":       None      
            },      
            "Synopsis":      synopsis,      
            "Image":         image,      
            "Rating":        rating,                 #Important!      
            "Provider":      None,      
            "Genres":        genres,                 #Important!      
            "Cast":          cast,      
            "Directors":     directors,              #Important!      
            "Availability":  None,                   #Important!      
            "Download":      None,      
            "IsOriginal":    isOriginal,             #Important!      
            "IsAdult":       None,                   #Important!   
            "IsBranded":     isOriginal,             #Important!   (preguntar)
            "Packages":      package_movie,          #Obligatorio      
            "Country":       country_list,      
            "Timestamp":     datetime.now().isoformat(), #Obligatorio      
            "CreatedAt":     self._created_at        #Obligatorio
        }
        self.payloads.append(payload_movie)

        


