# -*- coding: utf-8 -*-
import time
import requests
import re
#from common import config
from datetime import datetime
#from handle.mongo import mongo
# from platforms.disneyplus import Serie
# from updates.upload import Upload
# from handle.datamanager import Datamanager
# from handle.replace import _replace
class HBO():
    def __init__(self, ott_site_uid, ott_site_country, type):
        #self._config = config()['ott_sites'][ott_site_uid]
        self._created_at = time.strftime("%Y-%m-%d")
        #self.mongo = mongo()
        self.start_url = 'https://play.hbomax.com/page/'
        #self._platform_code = self._config['countries'][ott_site_country]
        #self.titanScraping = config()['mongo']['collections']['scraping']
        #self.titanScrapingEpisodios = config(
        #)['mongo']['collections']['episode']
        self.sesion = requests.session()

        if type == 'scraping':
            self._scraping()
        if type == 'testing':
            self._scraping()
        if type == 'return':
            '''
            Retorna a la Ultima Fecha
            '''
            params = {"PlatformCode": self._platform_code}
            lastItem = self.mongo.lastCretedAt(self.titanScraping, params)
            if lastItem.count() > 0:
                for lastContent in lastItem:
                    self._created_at = lastContent['CreatedAt']

            self._scraping()

    def _get_auth(self):
        
        print('Obteniendo token...')
        url = "https://oauth.api.hbo.com/auth/tokens"

        payload = {
            "client_id": "585b02c8-dbe1-432f-b1bb-11cf670fbeb0",
            "client_secret": "585b02c8-dbe1-432f-b1bb-11cf670fbeb0",
            "scope": "browse video_playback_free",
            "grant_type": "client_credentials",
            "deviceSerialNumber": "6c8795aa-588b-43be-9ae0-2d88731b565b",
            "clientDeviceData": {"paymentProviderCode": "blackmarket"}
        }
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/vnd.hbo.v9.full+json",
            "Accept-Language": "en-ca",
            "Accept-Encoding": "gzip, deflate, br",
            "Host": "oauth.api.hbo.com",
            "Origin": "https://play.hbomax.com",
            "Content-Length": "295",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Safari/605.1.15",
            "Referer": "https://play.hbomax.com/",
            "Connection": "keep-alive",
            "X-Hbo-Device-Name": "desktop",
            "X-Hbo-Client-Version": "Hadron/50.40.0.226 desktop (DESKTOP)",
            "X-B3-TraceId": "5a5de6cf-8ae7-4a89-f418-64261e0b325e-325ed080-3319-48a8-8960-789be063fb6d",
            "X-Hbo-Device-Os-Version": "undefined"
        }

        data = Datamanager._getJSON(
            self, url, json=payload, headers=headers, usePOST=True, showURL=False)
        print('Token Obtenido\n')
        return data['access_token']

    def _getEpiPayload(self, dataContent):
        for season in dataContent:
            if "season" in season['id']:
                episodesPayload = "["
                cont = 0
                for epiId in season['body']['references']['episodes']:
                    if cont == len(season['body']['references']['episodes'])-1:
                        episodesPayload += "{\"id\":\""+epiId+"\"}"
                    else:
                        episodesPayload += "{\"id\":\""+epiId+"\"},"
                    cont += 1
                episodesPayload += "]"
                return episodesPayload

    def link_img(self, link):
        link_ = link.replace("{{size}}", "760x326").replace("{{compression}}", "low").replace(
            "{{protection}}", "false").replace("{{protection}}", "false")
        return link_

    def _scraping(self):

        url = "https://comet.api.hbo.com/content"

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/vnd.hbo.v9.full+json",
            "Authorization": 'Bearer ' + self._get_auth(),
            "Accept-Language": "en-us",
            "Accept-Encoding": "gzip, deflate, br",
            "Host": "comet-latam.api.hbo.com",
            "Origin": "https://play.hbomax.com",
            "Referer": "https://play.hbomax.com/",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Safari/605.1.15",
            "Connection": "keep-alive",
            "X-Hbo-Device-Name": "desktop",
            "X-Hbo-Client-Version": "Hadron/50.40.0.226 desktop (DESKTOP)",
            "X-B3-TraceId": "72f25bb9-1e42-43f7-b90f-09d69cc77b4a-c597a133-67d7-4645-972f-4831ee4df6c4",
            "x-hbo-headwaiter": "entitlements:eyJpIjoiY29tZXRAMTAuMC42OTA4IiwidiI6MSwicyI6NDIsImFsZyI6ImRpciIsImVuYyI6IkEyNTZHQ00ifQ..vkGI62Ivy59XP_Zf.WhUbxfKz-NT8-8lTLVbVJr363ZnrgUQNjIpdbQvESiSfaGu4-7jblRn-_n1lJikWEYKcJ4tCOcXbTit2Z8n2qLrn75a2qmVI_40QIYIL5YSMO4Bc_iqDIhLp5RFXfRS_zkEldnRwu_VIpc-KB0hPowq0O_0AyMqAHEL2ESI8eOfWA-ichCw05X5pGZ1CxAtsjutXpLpyPqNgo5SZ7T53Ig9Bd5ISgFYjh_z14-ygEynISW2iWU-tCR5UPGD71pH1XJyCXDeHp1MiGo9HBzpZKEV4JlYyWUUgyR6c0FJb0B0L49mJ80k1GSrSLjwUqDtbV94i80REOCqlJoNwtmtm1WTI5hyqL5ujSZ4-kmgYNjGmIpckoRBINd2VWnBL91jM1BaRkJsEQqpvLT6O-Qosd8TsR5n1zJkPFD8UQoOur6RCyxbIyPi4jtJmqllDfE59t6jxCK0txz4_pBqASDuJqsFDiaPw9y4tvCmjXWvufBut937IhQQCTAwfuC9Tbh7TkRJzIj8tcCnz0bSnWPYHaye8t2-Bko_Nk-Xh.IYklDM-WcDuDCf5kBNHn-A,globalization:eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCIsImkiOiJnYXRld2F5QDAuMC4xNDMiLCJ2IjoxLCJzIjo0Mn0.eyJkIjp7InVpTGFuZ3VhZ2UiOiJlbi1VUyIsImZvcm1hdCI6ImVuLVVTIiwiYWx0ZXJuYXRlVWlMYW5ndWFnZSI6ImVuLVVTIn0sImlhdCI6MTYyNzU3NDA0NX0.BUM-DmXwqw1Fcs5UgA5Fftlc4JdD3W0SpLpc6UKDEHE,privacy:eyJpIjoiY29tZXRAMTAuMC42OTA4IiwidiI6MSwicyI6NDIsImFsZyI6ImRpciIsImVuYyI6IkEyNTZHQ00ifQ..UoMKTwdK0Y66KpEJ.UtIipBQJwKEXh7TSiGhM6xDyXoL8xzfG0i2pTBh6qLYxiF4Eq5TtaoEQewAlsVUZ5m3hBXIewQt8A4ZU33qsv6h9xfxtdMbYDhZELCr8yZ_dEG56N9Dc2Aow5SCQWOGhsJ7vnEWNRs37p60NodLStDUrfmtWjCqx4a_Un_ysaeExKmRnMv4venhLwQzepZfUIJA.24DhjPr9G5NCeu_6z5jtDA,profile:eyJpIjoiY29tZXRAMTAuMC42OTA4IiwidiI6MSwicyI6NDIsImFsZyI6ImRpciIsImVuYyI6IkEyNTZHQ00ifQ..AqCZDtYwCxfl8TAv.yE-t1A4u3aFX8Qcu21_wbKmYNJZbT6ew5BGcerWevyI2eTpC-4J2m_Uh3OVKmHHaFLFHq69Z7UYYBjpWWLBGk1GKWPRP7C3AqeuhRt4-6BNDpm0c-RqH21s3hCvsP5z2AqZCIGVpbQNTp9I-zMzsObQtBOHhTIKodF1Db2nsJHQ4a8ibH1FlNjVdRz9Ewt4Ej7yn45rGE7GZ4the08Bgtuv4Eg.JlwGVPtNbnEiD--Rf61qOg,telemetry:eyJpIjoiY29tZXRAMTAuMC42OTA4IiwidiI6MSwicyI6NDIsImFsZyI6ImRpciIsImVuYyI6IkEyNTZHQ00ifQ..T5sR5kCvFFtxLIAh.CNAKf95k5iBOePqRXeSyjJnPA8kDPP1-eDe8zLlbFKUkIoi8MSzg7dcbYuO9f2fBOCUQs4sPpUY2KYm1ekuGeHDByA7chRG02Wiy1UCodOfS757DWTxZo5WD7oGBUWnr5EJXEp_m7fpG9Vt4UTj53ERbiMBtWIU17w8kLy2vcy5uKLTcTwwxxf4.AU1PSTCaZYIf5AN2bM6UMg",
            "X-Hbo-Device-Os-Version": "undefined",
            "x-hbo-brownie": "sessionContext=epe1EU8f2tIimQdZ7Zg7YQ%3D%3D.rp92%2FYqravT%2BuRuB8nk%2BTwC3PDv%2FBg%2B0xnm4dj7D24ilTMYLPSVNt5B8j9UuBj%2ByQM5g%2FQmnJBttnrrccFv9Kbd6mdxssL9qSSPJFXhewhhhMsm9L6u15pR9l5DQayvi3NFbvGVZHTGu0y5QL5bg2%2FYZaXxsCTHPiVzDjSYX6uliK5cjqE%2B6RQgKTtfXsAIpnzn0ZWlfzp55JnA6uSSqPN9Z3eH%2FnW6lOj0DNG6bigxZoXNgPeeBlKFVKTn5gqLFS1DCdggRiwVI5aSoLi82pzcyrE%2FH5EfJ8kX5dYWBHbJiYUcdsNX4rkizh4hS3g%2FWiPH0lmY%2FDdewRQquK%2FpJguCVzm0%2BGr44qkk5RU6nJqpCxyegQyS3uWdTSGVhYl%2F072VRWsMHX1KTiC2U%2B%2FoJcN%2BLfXLtOPX660gh1AkeCZf%2F%2BYPNJDm1oIVJ1wFWhyTVfDoP2R2MTqOPxeuhgbwReyDcil4KK1VPHrB7N77xVeTMsFai0a7%2F0U%2Bf2Wg3R8I7V%2BccUBpPSG7CEO%2BAaW4CbWQkBQK%2FUQxAXYU1ntBvZnlvU5wTgB9Txf64xLqs1Q8H9gxGIdK1kFBB%2FK0H7adj4FvzPQHcOIwYDO2JNu%2FFqJXEvT1Ja0BrnIkVK9VlAP9dE5tEiSUfpl2inYE%2FfP0qpV2hqaEU5M67nG8IJzJn%2BNQ%3D"
        }
        list_top = []
        #Se ingresa con features para obtener los top 10 de la plataforma
        features = "urn:hbo:tab:k1YSGs04uqezgzZJtl3G9"
        payload = "[{\"id\":\""+features+"\"}]"

        data = Datamanager._getJSON(self, url, headers=headers, data=payload, usePOST=True)
        for item in data[0]['body']['references']['items']:
            payload = "[{\"id\":\""+item+"\"}]"
            data_top = Datamanager._getJSON(self, url, headers=headers, data=payload, usePOST=True)
            top_title = data_top[0]['body']['header']['label']
            #consigo el title del top para reconocerlo y agrupar los payloads con eso
            list_payloads = []
            for content in data_top[0]['body']['references']['items']:
                payload = "[{\"id\":\""+content+"\"}]"
                data_content = Datamanager._getJSON(self, url, headers=headers, data=payload, usePOST=True)
                id_movie = data_content[0]['id']
                payload = "[{\"id\":\""+id_movie+"\"}]"
                if re.search(':type:feature',payload):
                    content_type = 'movie'
                    payload = payload.replace(':type:feature', '').replace('tile', 'feature')
                else:
                    content_type = 'serie'
                    payload = payload.replace(':type:series', '').replace('tile', 'series')
                data_final = Datamanager._getJSON(self, url, headers=headers, data=payload, usePOST=True)
                list_payloads.append(self.get_payload(data_final[0],content_type))
            list_top.append({'Name': top_title, 'List Payloads': list_payloads})
        

    @staticmethod
    def get_id(content): return str(content['id'])

    @staticmethod
    def get_title(content): return content['body']['titles']['full']

    @classmethod
    def clean_title(cls,content): return _replace(cls.get_title(content))

    @staticmethod
    def get_synopsis(content): 
        if 'summaries' in content['body'].keys():
            if content['body']['summaries']['full']:
                synospsis = content['body']['summaries']['full']
            else:
                synospsis = None
        else: return None
        return synospsis

    @staticmethod
    def get_images(content):
        list_images = []
        if 'images' in content['body'].keys():
            for imag in content['body']['images']:
                list_images.append(content['body']['images'][imag])
        if list_images == []:
            return None
        else: return list_images

    @staticmethod
    def get_packages():
        return [{'Type':'subscription-vod'}]

    @staticmethod
    def get_availability(content):
        try:
            numbers = content['body']['endDate']
        except: return None
        numbers = numbers//1000
        return str(datetime.fromtimestamp(numbers))

    @staticmethod
    def get_year(content):
        year = None
        if 'releaseYear' in content['body'].keys():
            year = content['body']['releaseYear']
            if year < 1900 or year > datetime.now().year:
                year = None
        return year

    @staticmethod
    def get_rating(content): 
        if 'normalizaRating' in content['body'].keys():
            return str(content['body']['normalizaRating']['value'])
        else: return None

    @classmethod
    def get_duration(cls,content, content_type):
        if content_type == 'serie':
            return None
        else:
            return int(content['body']['duration']/60)

    @staticmethod
    def get_cast(content):
        actors = []
        if 'credits' in content['body'].keys():
            for cast in content['body']['credits']['cast']:
                actors.append(cast['person'])
        if actors:
            return actors
        else: return None

    @staticmethod
    def get_directors(content):
        directors = []
        if 'credits' in content['body'].keys():
            for dir in content['body']['credits']['directors']:
                directors.append(dir['person'])
        if directors:
            return directors
        else: return None
    
    @staticmethod
    def get_crew(content):
        crew = []
        if 'credits' in content['body'].keys():
            for role in content['body']['credits']:
                if role != 'directors' and role!= 'cast':
                    for person in content['body']['credits'][role]:
                        crew.append({'Role': person['role'], 'Name': person['person']})
        if crew:
            return crew
        else: return None


    def get_deeplinks(self,content, content_type):
        id =  self.get_id(content).replace('feature','page').replace('serie','page')
        if content_type == 'movie':
            deeplink = self.start_url + id + ':type:feature'
        else:
            deeplink = self.start_url + id + ':type:series'
        return deeplink
    
    @staticmethod
    def get_providers(content):
        providers = []
        if "attributionIcon" in content['body'].keys():
            whos_brandes= content['body']['attributionIcon']['alternateText']
            if  whos_brandes != "":
                providers.append(whos_brandes)
        if not providers: 
            return None
        else: return providers

    @classmethod
    def get_original(cls,content):
        providers = cls.get_providers(content)
        if providers:
            if "Max Originals" in providers or "HBO" in providers:
                return True
            else:
                return False
        else: return False
        
    @classmethod
    def is_branded(cls,content):
        is_original = cls.get_original(content)
        if is_original: return True
        else: return False
    

    def get_payload(self,data, content_type):

        payload = {
            'PlatformCode':  self._platform_code,
            'Id':            self.get_id(data),
            'Title':         self.get_title(data),
            'CleanTitle':    self.clean_title(data),
            'OriginalTitle': None,
            'Type':          content_type,
            'Year':          self.get_year(data),
            'Duration':      self.get_duration(data, content_type),
            'Deeplinks': {
                'Web':       self.get_deeplinks(data, content_type),
                'Android':   None,
                'iOS':       None,
            },
            'Playback':      None,
            'Synopsis':      self.get_synopsis(data),
            'Image':         self.get_images(data),
            'Rating':        self.get_rating(data),
            'Provider':      self.get_providers(data),
            'Genres':        None ,
            'Cast':          self.get_cast(data),
            'Crew':          self.get_crew(data),
            'Directors':     self.get_directors(data),
            'Availability':  self.get_availability(data),
            'Download':      None,
            'IsOriginal':    self.get_original(data),
            'IsAdult':       None,
            "IsBranded":     self.is_branded(data), 
            'Packages':      self.get_packages(),
            'Country':       None,
            'Timestamp':     datetime.now().isoformat(),
            'CreatedAt':     self._created_at,
        }
        return payload

