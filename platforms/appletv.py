# -*- coding: utf-8 -*-
import sys
import os
path = os.path.abspath('.')
sys.path.insert(1, path)
import db_conection
import time
import requests
import json
from datetime import datetime
from bs4 import BeautifulSoup
from selenium import webdriver
import re
from common import config


class AppleTV():
    def __init__(self, ott_site_uid, ott_site_country, operation='testing'):
        
        self._config  = config()['ott_sites'][ott_site_uid]
        self._platform_code  = self._config['countries'][ott_site_country]
        self._created_at  = time.strftime("%Y-%m-%d")
        self.headers  = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:71.0) Gecko/20100101 Firefox/71.0'}
        self.currentSession = requests.session()
        self.insert_many_to_db = db_conection.insertMany
        self.insert_one_to_db = db_conection.insert
        self.scraped = []
        self.trending_movies = []
        self.trending_shows = []
        self.top_ten_movies = []
        self.top_ten_shows = []
        self.browser = webdriver.Firefox()
        if operation=='testing':
            self.scraping()

    def scraping(self):
        self.get_trendings()    
        payloads = list()
        start_url = 'https://tv.apple.com/api/uts/v2/browse/webLanding?l=en&utsk=6e3013c6d6fae3c2%3A%3A%3A%3A%3A%3A235656c069bb0efb&caller=web&sf=143441&v=36&pfm=web&locale=en-US'
        response = self.getUrl(url=start_url)
        data = response.json()
        
        id_list = []
        for item in data['data']['items']:
            _id = item['id']
            id_list.append(_id)

        apple_url= "https://tv.apple.com/"
        more_ids= self.applebs4(apple_url)

        for id in more_ids:
            id_list.append(id)
        
        id_list=list(set(id_list))
        
        for content in id_list:
            url = 'https://tv.apple.com/api/uts/v2/view/show/{}?utsk=6e3013c6d6fae3c2%3A%3A%3A%3A%3A%3A235656c069bb0efb&caller=web&sf=143441&v=36&pfm=web&locale=en-US'.format(content)
            print('CONTENT URL ',url)
            response = self.getUrl(url=url)
            try:
                data = response.json()
            except:
                continue
            
            content_deeplink = data['data']['content']['url']
            content_deeplink_data = self.currentSession.get(content_deeplink).text
            content_soup = BeautifulSoup(content_deeplink_data, 'lxml')
            
            print(data['data']['content']['type'])
            if data['data']['content']['type'] == 'Movie':
                _type = 'movie'
            elif data['data']['content']['type'] == 'Show':
                _type = 'serie'

            if data['data']['content'].get('genres'):
                genres = []
                for g in data['data']['content']['genres']:
                    genres.append(g['name'])
            else:
                genres = None
            
            roles_data = content_soup.find_all("div", {"class": "profile-lockup__details"})
            cast, directors, crew = self.get_roles(roles_data)
            
            imageL = []
            images =  data['data']['content']['images']['coverArt']['url'] if data['data']['content']['images'].get('coverArt') else None
            width  =  data['data']['content']['images']['coverArt']['width'] if data['data']['content']['images'].get('coverArt') else None
            height =  data['data']['content']['images']['coverArt']['height'] if data['data']['content']['images'].get('coverArt') else None
            if images != None and width != None and height != None:
                images = images.split('{')
                images = images[0]
                images = images + str(width) + 'x' + str(height) + 'tc.jpg'
                imageL.append(images)
            
            try:             
                _timestamp = data['data']['content']['releaseDate']
                _timestamp = str(_timestamp)
                _timestamp = _timestamp[:-3]
                _timestamp = int(_timestamp)
                year = datetime.date.fromtimestamp(_timestamp)
                year = str(year)
                year = year.split('-')
                year = int(year[0])
                if year < 1870 or year > datetime.now().year:
                    year = None
            except:
                year = None
            
            if not year:
                year = self.get_year_from_soup(content_soup)

            is_original= self.is_original(data['data']['content'])
            rating = self.get_rating(data['data']['content'])
            duration = self.get_duration(data['data']['content'])

            try:
                synopsis= data['data']['content']['description']
            except:
                synopsis= None

            payload = {
                'PlatformCode'  : self._platform_code,
                'Id'            :  data['data']['content']['id'],
                'Type'          : _type,
                'Title'         :  data['data']['content']['title'],
                'CleanTitle'    : data['data']['content']['title'],
                'OriginalTitle' : None,      
                'Year'          : year,
                'Duration'      : duration,
                'Deeplinks'     : {
                                    'Web':  content_deeplink,
                                    'Android': None,
                                    'iOS': None
                },
                'Synopsis'      : synopsis,
                'Rating'        : rating,
                'Provider'      : None,
                'Genres'        : genres,
                'Cast'          : cast,
                'Crew'          : crew,
                'Directors'     : directors,
                'Country'       : None,
                'Availability'  : None,
                'Download'      : None,
                'IsOriginal'    : is_original,
                'IsAdult'       : None,
                "IsBranded"     : None,
                'Image'         : imageL,
                'Packages'      : [{'Type': 'subscription-vod'}],
                'Timestamp'     : datetime.now().isoformat(),
                'CreatedAt'     : self._created_at
            }

            if data['data']['content']['id'] in self.scraped:
                continue
            else:
                self.scraped.append(data['data']['content']['id'])
                payloads.append(payload)

            if len(payloads) > 99:
                self.check_top_10(payloads)
                self.insert_many_to_db(payloads)
                payloads.clear()
        if payloads:
            self.insert_many_to_db(payloads)
        self.currentSession.close()

        print(f'\nFinished\n') 

        #Upload(self._platform_code, self._created_at, testing=testing)
        
    def getUrl(self, url):
        requestsTimeout = 5
        while True:
            try:
                response = self.currentSession.get(url, timeout=requestsTimeout)
                return response
            except requests.exceptions.ConnectionError:
                print("Connection Error, Retrying")
                time.sleep(requestsTimeout)
                requestsTimeout = requestsTimeout + 5
                if requestsTimeout == 45:
                    print('Timeout has reached 45 seconds.')
                    break
                continue
            except requests.exceptions.RequestException:
                print('Waiting...')
                time.sleep(requestsTimeout)
                requestsTimeout = requestsTimeout + 5
                if requestsTimeout == 45:
                    print('Timeout has reached 45 seconds.')
                    break
                continue
            break
    
    def is_original(self, data):
        return data['isAppleOriginal']
   
    def get_rating(self, data):
        return data['rating']['displayName'] if data.get('rating') else None

    def get_duration(self, data):
        if data.get('duration'):
            return data['duration'] // 60
        else:
            return None

    def applebs4(self, apple_url):
        response= self.getUrl(url=apple_url)
        data= BeautifulSoup(response.text, "html.parser")
        ids=[]
        list_of_li = data.find_all("li",{"class":"shelf-grid__list-item"})
        for li in list_of_li:
            div= li.find('div',{'class': 'canvas-lockup'})
            if not div:
                continue
            if not div.get('data-metrics-click'):
                continue
            data= div.get('data-metrics-click')
            data= json.loads(data) 
            id= data['targetId']
            ids.append(id)
        for li in list_of_li:
            div= li.find('a',{'class': 'notes-lockup'})
            if not div:
                continue
            if not div.get('data-metrics-click'):
                continue
            data= div.get('data-metrics-click')
            data= json.loads(data) 
            id= data['targetId']
            print(id)
            ids.append(id)
        return ids

    def get_year_from_soup(self, soup):
        """Este método se utiliza en el caso de que no se pudiera
        obtener el año de estreno de un contenido por API, se hace
        una consulta directa por html en base a la url de dicho contenido.
        
        - Return: int correspondiente al año | None si no se puede obtener
        """
        print('INTENTANDO OBTENER AÑO POR SOUP...')
        data_container = soup.find('div', {'class':'product-header__content__details__metadata--info'})
        if data_container:
            year = None
            for data in data_container.findAll('span'):
                try:
                    possible_year = int(data.text)
                    if possible_year in range(1870, datetime.now().year+1):
                        year = possible_year
                except:
                    continue
            return year
        else:
            return None

    def clean_cast(self, cast_list):
        """Limpia los nombres de los actores en caso de ser necesario
        """
        cast = []
        for actor in cast_list:
            cast.append(actor.replace('\xa0', ' '))
        return cast if cast else None
    
    
    def get_roles(self, roles_data):
        cast = []
        directors = []
        crew = []
        
        for person_data in roles_data:
            person_name_data = person_data.contents[1].text
            person_name = person_name_data.replace('\n','').strip().replace('\xa0', ' ')
            
            role_data = person_data.parent
            person_role = json.loads(role_data['data-metrics-click'])['contentType']
            
            if person_role == 'Actor':
                cast.append(person_name)
                
            elif person_role == 'Director':
                directors.append(person_name)
            
            else:
                crew.append(
                    {'Role': person_role,
                     'Name': person_name})
        
        return cast or None, directors or None, crew or None

    def get_trendings(self):
        trending_movies = []
        trending_shows = []
        flix_platforms = ['netflix','hbo','disney','amazon','itunes','google']
        search_movies = {
        'rotten_tomatoes':'https://editorial.rottentomatoes.com/guide/popular-movies/',
        'imdb' : 'https://www.imdb.com/chart/moviemeter/?sort=rk,asc&mode=simple&page=1',
        'the_numbers' : 'https://www.the-numbers.com/movies/trending',
        'flix_patrol' : 'https://flixpatrol.com/'
        }
        search_shows = {
            'rotten_tomatoes': 'https://www.rottentomatoes.com/browse/tv-list-2',
            'imdb': 'https://www.imdb.com/chart/tvmeter/?ref_=nv_tvv_mptv'
        }

        urls = search_movies.values()
        for url in urls:
            self.browser.get(url)
            page_source = self.browser.page_source
            if 'rottentomatoes' in url:
                content_soup = BeautifulSoup(page_source, 'lxml')
                data_container = content_soup.find_all('div', {'class':'row countdown-item'})
                top_ten = data_container[:10]
                for content in top_ten:
                    data_info = content.find('h2')
                    title = data_info.find('a').text
                    year = data_info.find('span', {'class':'subtle start-year'}).text
                    year = year[year.find("(")+1:year.find(")")]
                    trending_movies.append({title:year})
            elif 'imdb' in url:
                content_soup = BeautifulSoup(page_source, 'lxml')
                data_container = content_soup.find('tbody',{'class':'lister-list'})
                all_trs = data_container.find_all('tr')
                top_ten = all_trs[:10]
                for content in top_ten:
                    data_info = content.find('td',{'class':'titleColumn'})
                    title = data_info.find('a').text
                    year = data_info.find('span',{'class':'secondaryInfo'}).text
                    year = year[year.find("(")+1:year.find(")")]
                    trending_movies.append({title:year})
            elif 'numbers' in url:
                content_soup = BeautifulSoup(page_source, 'lxml')
                data_container = content_soup.find('div',{'id':'main'})
                all_divs = data_container.find_all('div', attrs = {'style':'border: 1px solid black; border-radius: 8px; padding: 6px; margin: 8px; box-shadow: 4px 4px 4px #888;'})
                top_ten = all_divs[:10]
                for content in top_ten:
                    data_info = content.find('table', attrs={'style':'width:410px;'})
                    all_trs = data_info.find('tbody').find_all('tr')
                    title = all_trs[0].find('span', attrs={'style':'font-size:200%;'}).text
                    year = all_trs[4].find('td').text
                    year = re.search(r"(\d{4})", year).group(1)
                    trending_movies.append({title:year})
            else:
                for plat in flix_platforms:
                    path_url = 'top10/{}'.format(plat)
                    url_ = url+(path_url)
                    self.browser.get(url_)
                    page_source = self.browser.page_source
                    content_soup = BeautifulSoup(page_source, 'lxml')
                    data_movies = content_soup.find('div',{'id':f'{plat}-1'}) 
                    data_container = data_movies.find('table',{'class':'card-table'})
                    all_trs = data_container.find_all('tr')
                    for tr in all_trs:
                        title_container = tr.find_all('td')
                        title_slug = title_container[1].find('a')['href']
                        content_url = 'https://flixpatrol.com{}'.format(title_slug)
                        self.browser.get(content_url)
                        page_source = self.browser.page_source
                        content_soup = BeautifulSoup(page_source, 'lxml')
                        data_container = content_soup.find('div',{'class':'md:flex items-baseline justify-between'})
                        title = data_container.find('h1',{'class':'mb-3'}).text
                        data_container = content_soup.find('div',{'class':'flex flex-wrap text-sm leading-6 text-gray-500'})
                        year_container = data_container.find_all('span')
                        year = year_container[4].text
                        year = year.split('/')[2]
                        trending_movies.append({title:year})
                    self.browser.get(url_)
                    page_source = self.browser.page_source
                    content_soup = BeautifulSoup(page_source, 'lxml')
                    data_series = content_soup.find('div',{'id':f'{plat}-2'})
                    data_container = data_series.find('table',{'class':'card-table'})
                    all_trs = data_container.find_all('tr')
                    for tr in all_trs:
                        title_container = tr.find_all('td')
                        title_slug = title_container[1].find('a')['href']
                        content_url = 'https://flixpatrol.com{}'.format(title_slug)
                        self.browser.get(content_url)
                        page_source = self.browser.page_source
                        content_soup = BeautifulSoup(page_source, 'lxml')
                        data_container = content_soup.find('div',{'class':'md:flex items-baseline justify-between'})
                        title = data_container.find('h1',{'class':'mb-3'}).text
                        trending_shows.append({'title':title})
        urls = search_shows.values()
        for url in urls:
            self.browser.get(url)
            page_source = self.browser.page_source
            content_soup = BeautifulSoup(page_source, 'lxml')
            if 'rottentomatoes' in url:
                data_container = content_soup.find('div',{'class':'mb-movies'})
                all_divs = data_container.find_all('div',{'class':'mb-movie'})
                for div in all_divs:
                    title = div.text
                    title = title.split(':')[0]
                    trending_shows.append({'title':title})
            else:
                data_container = content_soup.find('tbody',{'class':'lister-list'})
                all_trs = data_container.find_all('tr')
                top_ten = all_trs[:10]
                for content in top_ten:
                    data_info = content.find('td',{'class':'titleColumn'})
                    title = data_info.find('a').text
                    trending_shows.append({'title':title})

        self.trending_movies = self.set_dct(trending_movies)
        self.trending_shows = self.set_dct(trending_shows)

    def set_dct(self,lst):
        seen = set()
        new_l = []
        for d in lst:
            t = tuple(d.items())
            if t not in seen:
                seen.add(t)
                new_l.append(d)
        return new_l

    def check_top_10(self,lst,type):
        if type == 'movie':
            movies = [{payload['Title']:payload['Year']} for payload in lst]
            for dct in movies:
                for k,v in dct.items():
                    for dct1 in self.trending_movies:
                        for x,y in dct1.items():
                            if k==x and v==y:
                                self.top_ten_movies.append(dct)
        else:
            shows = [{'title': payload['Title']} for payload in lst]
            for dct in shows:
                for k,v in dct.items():
                    for dct1 in self.trending_shows:
                        for x,y in dct1.items():
                            if v==y:
                                self.top_ten_shows.append(dct)

