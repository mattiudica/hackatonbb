import sys
import os
path = os.path.abspath('.')
sys.path.insert(1, path)
import db_conection


import time
# -*- coding: utf-8 -*-
import time
import requests
import hashlib
import json
import re
import unicodedata
import threading
import platform
import pyautogui
from pyvirtualdisplay                               import Display
from difflib                                        import SequenceMatcher
from bs4                                            import BeautifulSoup
from common                                         import config
from datetime                                       import datetime
from handle.mongo                                   import mongo
from handle.replace                                 import _replace
from handle.datamanager                             import Datamanager
from handle.datamanager                             import RequestsUtils
from selenium                                       import webdriver
from selenium.webdriver.common.action_chains        import ActionChains
from selenium.webdriver.firefox.options             import Options



class Login():
    
    def __init__(self, ott_site_uid, ott_site_country, type):
        
        self._config                    = config()['ott_sites'][ott_site_uid]
        self._country                   = ott_site_country
        # self._start_url                 = self._config['start_url']
        self._platform_code             = self._config['countries'][ott_site_country]
        # if self._country != 'JP':
        #     self.class_id               = self._config['class_id'][ott_site_country]
        #     self.locale                 = self._config['locale'][ott_site_country]
        #     self.market_code            = self._config['market_code'][ott_site_country]
        self._created_at                = time.strftime('%Y-%m-%d')
        self.mongo                      = mongo()
        # self.currency                   = config()['currency'][ott_site_country]
        self.titanScraping              = config()['mongo']['collections']['scraping']
        self.titanScrapingEpisodios     = config()['mongo']['collections']['episode']
        self.titanPreScraping           = config()['mongo']['collections']['prescraping']
        self.headers  = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
        self.currentSession = self.sesion = requests.session()
        self.skippedEpis = 0
        self.skippedTitles = 0
        self.req_utils = RequestsUtils()
        self.browser = webdriver.Firefox() 
        self.payloads = []
        self.lista_ids = []

        ######################### REGEX para JP ##################################
        self.regex_epi_1 = re.compile(r'(第?\d+|第\D+)(話|章|回|集|試|幕|食目|時限目|曲|滑走|χ|斤|撃|夜|問|首|柱|弾|羽|試合|節|品目|号|日目|巻|席|球|軒目|怪|条|箱|憑目|病)')
        self.regex_epi_2 = re.compile(r'(Ep|エピソード|EPISODE|Eps|DAY|♯|#|＃|Part|Lesson|プロファイル|File|Mission|ファイル|Station|Story|Round|PHASE-|OPE|Lv|Episodio|Life|STAGE|標的|CODE|KARTE|EX|ROAD|chapter|Lecon|act|Op|No|CHANGE|GP-|イメージ|ディメンジョン|Task|vol|ページ|case|レベル|ルーン|SAILING|Target|Phase|page|その|レッスン|Quest|Epi|Agenda|Piece|SCENE|Target|Fight|refre)\☆?\:?\.?\s?\d+', re.IGNORECASE)
        self.regex_season_1 = re.compile(r'(シーズン|season|S\.|第)\s?\d+(期|シリーズ)?', re.IGNORECASE)
        self.regex_season_2 = re.compile(r'\d+(st|nd|rd|th)\s?season', re.IGNORECASE)
        self.regex_espacio = re.compile(r'\s')
        self.regex_corchetes = re.compile(r'【.+?】')
        self.regex_parentesis = re.compile(r'(（|\().+?(\)|）)')
        ##########################################################################
        
        if type == 'scraping':
            self._scraping()

        elif type == 'return':
            params = {'PlatformCode' : self._platform_code}
            lastItem = self.mongo.lastCretedAt(self.titanScraping, params)
            if lastItem.count() > 0:
                for lastContent in lastItem:
                    self._created_at = lastContent['CreatedAt']

            self._scraping()

        elif type == 'testing':
            self._scraping(testing = True)



    def _scraping(self, testing):
        urls = ['https://www.netflix.com/login', 'https://www.netflix.com/browse/genre/83', 'https://www.netflix.com/browse/genre/34399']
        self.get_user()               
        for url in urls:
            if url == 'https://www.netflix.com/login':
                self.overall = True
            if url == 'https://www.netflix.com/browse/genre/83':
                self.series = True
            if url == 'https://www.netflix.com/browse/genre/34399':
                self.movies = True

            self.lista_ids = []
            mostWatched = []
            titulos_mostWatched = []
            self.browser.get(url)
            time.sleep(3)
            soup = BeautifulSoup(self.browser.page_source, 'lxml')
            time.sleep(3)
            container = soup.find('div', attrs={"class": "lolomoRow lolomoRow_title_card ltr-0", 'data-list-context' : "mostWatched"})
            slider_item = container.find_all('div', class_="slider-item slider-item-")
            self.lista_ids.append(slider_item)
            self.get_items(container)
            time.sleep(5)
            
            for item in self.lista_ids:
                for itemId in item:
                    if itemId.text != '':
                        if itemId.div.text in titulos_mostWatched:
                            pass
                        else:
                            mostWatched.append(itemId)
                            titulos_mostWatched.append(itemId.div.text)
                            link = itemId.div.div.a.get('href')
                            top_position = itemId.div.div.get('id')

                            pattern = re.compile(r"\d-(\d)$")
                            match = pattern.search(top_position)
                            
                            match = int(match.groups()[0])

                            self.get_position(match)
                            id_ = re.search('[0-9]{8,}',link).group(0)
                            deeplink = 'https://www.netflix.com/browse?jbv={}'.format(id_)
                            self.get_payloads(deeplink, id_, itemId.div.text, top_position)
            print('a')
            

        
    def get_payloads(self, deeplink, id_, titulo, top_position):
        self.browser.get(deeplink)
        soup = BeautifulSoup(self.browser.page_source, 'lxml')
        time.sleep(3)
        synopsis = soup.find('p', class_="preview-modal-synopsis previewModal--text").contents
        genres_content = soup.find('div', attrs={'class' : "previewModal--tags", "data-uia" : "previewModal--tags-genre"}).contents
        genres = [x.previous for x in genres_content if x.previous]
        genres.pop(0)
        genres.pop(0)
        genres = [_replace(x) for x in genres]
        duration = soup.find('span', class_="duration").contents
        if 'temporada' in duration:
            type_ = 'serie'
            duration = None
        else:
            type_ = 'movie'

        image = soup.find('div', class_="videoMerchPlayer--boxart-wrapper").find('img')
        image = image.get('src')

        year = soup.find('div', class_="year").contents

        rating = soup.find('span', class_="maturity-number").contents
        try:
            cast_container = soup.find('div', attrs={'class':"previewModal--tags", 'data-uia':"previewModal--tags-person"}).contents    
            
            cast = [x.previous for x in cast_container if x.previous]

            cast.pop(0)
            cast.pop(0)
        except Exception:
            cast = None
        payload = {
                'PlatformCode':  self._platform_code,
                'Id':            id_,
                'Title':         titulo,
                'OriginalTitle': None,
                'CleanTitle':    _replace(titulo),
                'TopPosition':   top_position,
                'Type':          type_, # 'movie' o 'serie'
                'Year':          year,
                'Duration':      duration, # duracion en minutos
                'Deeplinks': {
                    'Web':       deeplink,
                    'Android':   None,
                    'iOS':       None,
                },
                'Playback':      None,
                'Synopsis':      synopsis,
                'Image':         str(image), # [str, str, str...] # []
                'Rating':        rating,
                'Provider':      None,
                'Genres':        str(genres), # [str, str, str...]
                'Cast':          str(cast), # [str, str, str...]
                'Directors':     None, # [str, str, str...]
                'Availability':  None,
                'Download':      None,
                'IsOriginal':    None,
                'IsAdult':       None,
                'Packages':      [{"Type":"subscription-vod"}],
                'Country':       None, # [str, str, str...]
                'Timestamp':     datetime.now().isoformat(),
                'CreatedAt':     self._created_at,
            }
        print('Insertado un payload top :)')
        self.payloads.append(payload)
            

    def get_user(self):
        self.browser.get("https://www.netflix.com/login")
        email = self.browser.find_element_by_id('id_userLoginId')
        password = self.browser.find_element_by_id('id_password')
        time.sleep(10)
        sign_in_button = self.browser.find_element_by_xpath("/html/body/div[1]/div/div[3]/div/div/div[1]/form/button")
        email.send_keys('axelmoscoa1154@outlook.com')
        password.send_keys('darwin1154')
        time.sleep(2)
        sign_in_button.click()
        time.sleep(10)

        usuario = self.browser.find_element_by_xpath('/html/body/div[1]/div/div/div[1]/div[1]/div[2]/div/div/ul/li[1]/div/a/div/div').click()            
        print('Se ingresó al usuario :)')
            
    def get_items(self, container):
        cont = 1
        while True:
            item = container.find_all('div', class_="slider-item slider-item-{}".format(cont))
            if item != []:
                self.lista_ids.append(item)
                print('Se obtiene un item')
                cont += 1
            else:  
                while True:             
                    try:                                                    
                        self.clickear_botones()
                        time.sleep(4)
                        soup = BeautifulSoup(self.browser.page_source, 'lxml')
                        container = soup.find('div', attrs={"class": "lolomoRow lolomoRow_title_card ltr-0", 'data-list-context' : "mostWatched"})
                        cont = 1
                        while True:
                            item = container.find_all('div', class_="slider-item slider-item-{}".format(cont))
                            if item != []:
                                self.lista_ids.append(item)
                                print('Se obtiene un item')
                                cont += 1
                            else:
                                break
                        break
                    except Exception:
                        pyautogui.press('space') 
                        time.sleep(15)
                break            


    def clickear_botones(self):
        cont = 1
        while cont < 10:
            try:
                boton = self.browser.find_element_by_css_selector('#row-{} > div:nth-child(1) > div:nth-child(1) > div:nth-child(1) > span:nth-child(3)'.format(cont))
                boton.click()
                cont += 1
                time.sleep(2)
            except Exception:
                break  

    def get_position(self, top_position):
        positional_value = 0
        real_value = 1
        while True:
            if top_position == positional_value:
                top_position = real_value
                break
            else:
                positional_value += 1
                real_value += 1

        return top_position