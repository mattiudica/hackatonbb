import sys
import os
import time
import requests
import time
import re
import json
import pyotp
from common import config
from handle.mongo import mongo
from updates.upload import Upload
from bs4 import BeautifulSoup
from selenium import webdriver
from pyvirtualdisplay import Display
from datetime import datetime
from handle.replace import _replace
from handle.datamanager import Datamanager
from selenium.webdriver.firefox.options import Options
from handle.payload     import Payload

path = os.path.abspath('.')
sys.path.insert(1, path)
import db_conection

class AmazonPrimeVideo():
    """
     - Recomendación de VPNS:
            LATAM: "amazon-prime-video" -> No hace falta.
            BR: "br.amazonprimevideo" -> ExpressVPN
            MX: "mx.amazonprimevideo" -> Correr en compu de México.
            SA: "sa.amazonprimevideo" -> GoshVPN
            BG: "bg.amazonprimevideo" -> ExpressVPN
            HR: "hr.amazonprimevideo" -> ExpressVPN
            MT: "mt.amazonprimevideo" -> GoshVPN
            LU: "lu.amazonprimevideo" -> ExpressVPN
            AE: "ae.amazonprimevideo" -> GoshVPN o PureVPN
            BD: "bd.amazonprimevideo" -> GoshVPN
            IL: "il.amazonprimevideo" -> ExpressVPN
            EG: "eg.amazonprimevideo" -> GoshVPN
    
        - Cuentas: Hay casos que con la misma cuenta se puede acceder a
        contenido de distintos países, pero esto es relativo. Este tema
        aún está en análisis.
    """
        
    def __init__(self, ott_site_uid, ott_site_country, operation):
        self._config            = config()['ott_sites'][ott_site_uid]
        self.country            = ott_site_country
        self.mongo = mongo()
        self._start_url         = self._config['start_url']
        self._url_api           = self._config['url_api']
        self._deeplink          = self._config['deeplink']
        self._deeplink2         = self._config['deeplink2']
        self._platform_code     = self._config['countries_data'][ott_site_country]['PlatformCode']
        self.titanTopOverall = config()['mongo']['collections']['scraping']
        self.titanTopMovies = config()['mongo']['collections']['scraping']
        self.titanTopSeries = config()['mongo']['collections']['scraping']
        self._created_at        = time.strftime('%Y-%m-%d')
        self.url_original       = self._config['url_original']
        
        # BBDD's.

        # ACCOUNT DATA.
        self.account            = self._config['countries_data'][ott_site_country]['account']
        if self.account:
            self.loggin_info    = self._config['accounts'][self.account]
            self._user_name     = self.loggin_info['user_name']
            self._user_pass     = self.loggin_info['user_pass']
            self.cookie         = ''

        #PAYLOADS
        self.payload_top_movies = []
        self.payload_top_series = []
        self.payload_top_overall= []
        
        # Parámetros claves.
        self.headers        = None
        self._server_region = self._config['countries_data'][ott_site_country]['region']
        self.get_cookie     = self._config['countries_data'][ott_site_country]['cookie']

        # STORE CURRENCY
        self.get_store      = self._config['countries_data'][ott_site_country].get('get_store')
        self.currency       = self._config['countries_data'][ott_site_country].get('store_currency')
        if not self.currency:
            self.currency   = config()['currency'][ott_site_country]

        # Iniciar Session.
        self.session = requests.session()

        print(f"\nIniciando scraping\nPlatformCode: {self._platform_code}\n")

        if operation == 'testing':
            #################################################################################
            # selenium_login() -> Debe ingresar correctamente a la primevideo para avanzar. #
            #################################################################################
            browser = self.selenium_login()
            if browser:
                self.scraping(browser)
            else:
                print("\nNo se pudo acceder a la página\nScraping Finalizado")
            self.session.close()
    
    def selenium_login(self):
        """Método fundamental para iniciar el preScraping.
        Aquí nos loggeamos y accedemos a la página princial de
        Amazon Prime Video.

        Returns:
            obj: Devuelve el objeto browser (Selenium).
        """
        ##############################################################
        #            Utilizamos Selenium para obtener urls           #
        ##############################################################
        if self.account:
            option = Options()
            option.add_argument('--headless')
            browser = webdriver.Firefox()

            check_location = self.validate_location(browser)
            if not check_location:
                return False
            print(" ##### Ingreando vía Selenium #####")
            browser.get(self._start_url)
            print(f"Loggin a {self._start_url}")
            print(f"Usando {self.account} -> {self._user_name}")  
            username = browser.find_element_by_xpath(self._config['queries']['user_name'])
            password = browser.find_element_by_xpath(self._config['queries']['user_pass'])
            
            username.send_keys(self._user_name)
            password.send_keys(self._user_pass)
            browser.find_element_by_xpath(self._config['queries']['btn_login']).click()
            time.sleep(1)
            if self.loggin_info.get('2FA'):
                try:
                    browser.find_element_by_xpath(self._config['queries']['chk_otp']).click()
                    time.sleep(1)
                    browser.find_element_by_xpath(self._config['queries']['btn_otp']).click()
                except:
                    pass

                codes2FA = browser.find_element_by_xpath(self._config['queries']['code_2fa'])
                code2FA = self.loggin_info['2FA']
                totp = pyotp.TOTP(code2FA)
                print("Current OTP:", totp.now())
                codes2FA.send_keys(totp.now())
                browser.find_element_by_xpath(self._config['queries']['btn_login2']).click()
             
        else:
            print('No requiere login.')
            browser = webdriver.Chrome()
            check_location = self.validate_location(browser)
            if not check_location:
                return False
            browser.get('https://www.primevideo.com/')
        time.sleep(5)
        
        try:
            try:
                ok_login = browser.find_element_by_xpath("//*[@id='pv-nav-main-menu']")            
                if ok_login:
                    print("Loggin exitoso\n")
                    return browser
            except:
                timer =  browser.find_element_by_xpath("//*[@id='timer']")
                intentos = 1
                while intentos != 4:
                    print(f"\n¡¡¡Acceso Denegado!!! Intentos: ({intentos}/3)")
                    print("El usuario de la cuenta debe verificar el acceso via sms o e-mail.")
                    time_ = int(re.sub("\D", "" ,timer.text ,flags=re.IGNORECASE))
                    print(f"El usuario debe confirmar en {time_} segundos.")
                    time.sleep(time_ + 1)
                    try:
                        ok_login = browser.find_element_by_xpath("//*[@id='pv-nav-main-menu']")
                        if ok_login:
                            print("Loggin exitoso\n")
                            return browser
                    except:
                        print("El usuario no autorizó. Reenviando coonfirmación.")
                        browser.find_element_by_xpath('//*[@id="resend-approval-link"]').click()
                        time.sleep(5)
                        timer =  browser.find_element_by_xpath("//*[@id='timer']")
                        time.sleep(5)
                        intentos += 1
                browser.quit()
                return None
        except:
            print(f"\n¡¡¡Acceso Denegado!!!  ROBOT ALERT (¬¬)")
            print("Detecta que es un robot. Hacer loggin manual.")
            print("Tiempo para loggearse e ingresar: 2 min.")
            time.sleep(120)
            try:
                ok_login = browser.find_element_by_xpath("//*[@id='pv-nav-main-menu']")
                if ok_login:
                    print("Loggin exitosooooooo\n")
                    return browser
            except:
                browser.quit()
                return None    

        print("Loggin exitoso\n")
        return browser
    
    def validate_location(self, browser):
        print('\n****** Validando ubicación *****')
        if self.country != 'LATAM':
            browser.get('https://www.primevideo.com')
            #############################
            #       LOCATION VPN        #
            #############################
            html = browser.page_source
            soup = BeautifulSoup(html,'html.parser')
            script = soup.find('script', attrs={'type':'text/template'}).text
            script_json = json.loads(script)
            try:
                location = script_json['initArgs']['context']
            except KeyError:
                location = script_json['props']['context']
            currentTerritory = location['currentTerritory']
            recordTerritory = location['recordTerritory']
            if currentTerritory != self.country:
                print('****************************************************************************************')
                print('**            No se ha conectado al pais correcto, el pais detectado es: ' + currentTerritory + '           **')
                print('**                         Verificar VPN. Se detiene scraping.                        **')
                print('****************************************************************************************')
                browser.close()
                time.sleep(5)
                browser.quit()
                time.sleep(5)
                return False
            else:
                print('Estas conectado correctamente a: ' + self.country + '\nSe inicia scraping.\n')
        else:
                print('Estas conectado correctamente a: ' + 'LATAM' + '\nSe inicia scraping.\n')
        return browser
    
    def get_urls(self, browser):
        ten_urls = []
        time.sleep(3)
        browser.execute_script("window.scroll(0, 1600)")
        time.sleep(15)
        try:
            browser.find_element_by_xpath('//*[@id="aiv-cl-main-middle"]/div/div[3]/div/div[7]/div/div/div[3]/div/div/div/button').click()
        except:
            raise Exception("No se encuentra disponible el top 10 en este pais")
        time.sleep(3)
        section = browser.find_element_by_xpath('//*[@id="aiv-cl-main-middle"]/div/div[3]/div/div[7]/div/div/div[3]/div/div/div/ul')    
        li  = section.find_elements_by_tag_name('li')
        for elem in li:
            ten_urls.append(elem.find_element_by_tag_name('a').get_attribute('href'))
        return ten_urls
    
    def get_series_url(self, browser):
        browser.find_element_by_css_selector('#pv-nav-tv-shows').click()
        return self.get_urls(browser)
        
    def get_movies_url(self, browser):
        browser.find_element_by_css_selector('#pv-nav-movies').click()
        return self.get_urls(browser)
        
    def get_url(self, url, headers=None):
        '''
        Método para hacer una petición
        '''
        requestsTimeout = 5
        while True:
            try:
                if headers:
                    response = self.session.get(url, headers=headers, timeout=requestsTimeout)
                else:
                    response = self.session.get(url, timeout=requestsTimeout)
                return response

            except requests.exceptions.ConnectionError:
                print("Connection Error, Retrying")
                time.sleep(requestsTimeout)
                continue
            except requests.exceptions.RequestException:
                print('Waiting...')
                time.sleep(requestsTimeout)
                continue
            break
    def scraping(self, browser):

        urls = {
            "url_top_ten_overall" : self.get_urls(browser),
            "url_top_ten_series"  : self.get_series_url(browser),
            "url_top_ten_movies"  : self.get_movies_url(browser)
        }
        
        for url in urls['url_top_ten_movies']:
            self.get_data(url,browser,insert_in ='movies')
            
        for url in urls['url_top_ten_series']:
            self.get_data(url,browser,insert_in ='serie')

        for url in urls['url_top_ten_overall']:
            self.get_data(url,browser,insert_in ='overall')


        # Corroborar que cierre bien el browser.

        print(f' DICCIONARIO TOP 10 MOVIES  {self.payload_top_movies}')
        print(f' DICCIONARIO TOP 10 SERIES  {self.payload_top_series}')
        print(f' DICCIONARIO TOP 10 OVERALL {self.payload_top_overall}')

        browser.close()
        time.sleep(5)
        browser.quit()
        time.sleep(5)     
        self.mongo.insertMany(self.titanTopOverall, self.payload_top_overall) 
        self.mongo.insertMany(self.titanTopMovies, self.payload_top_movies) 
        self.mongo.insertMany(self.titanTopSeries, self.payload_top_series)  
        Upload(self._platform_code, self._created_at, True)

    def get_type(self, browser):
        div = browser.execute_script('return document.querySelector(".dv-node-dp-seasons")')
        if div:
            return 'serie'
        else:
            return 'movie'


    def get_data(self,url,browser,insert_in):
        browser.get(url)
        time.sleep(3)
        
        packages = self.get_packages(browser)
        type_ = self.get_type(browser)
        
        response = self.get_url(url)
        html_soup = BeautifulSoup(response.text, 'lxml')
        
        if insert_in == 'movies':
            self.payload_top_movies.append(self.get_payload(html_soup,url,packages,type_)) 
        if insert_in == 'serie':
            self.payload_top_series.append(self.get_payload(html_soup,url,packages,type_))
        if insert_in == 'overall':
            self.payload_top_overall.append(self.get_payload(html_soup,url,packages,type_))

    def get_payload(self, html_soup,deeplink,packages, type_):
        payload = Payload()

        payload.platform_code = self._platform_code
        payload.id = self.get_id(deeplink)
        payload.title = self.get_title_h1(html_soup)
        payload.clean_title = self.clean_title(_replace(payload.title))
        payload.deeplink_web = deeplink
        payload.year = self.get_year(html_soup)
        payload.duration = self.get_duration(html_soup)
        payload.synopsis = self.cleanSynopsis(self.get_synopsis(html_soup))

        find_metadatos = html_soup.find('div', {'data-automation-id': 'meta-info'})
        if find_metadatos:
            find_all_metadatos = find_metadatos.find_all('dl')
            
            if find_all_metadatos:
                for item in find_all_metadatos:
                    find_element = item.find('dd')
                    find_all_ = find_element.find_all('a') or []
                    if not payload.cast:
                        payload.cast = self.get_cast(find_all_, item)
                    if not payload.genres:
                        payload.genres = self.get_genres(find_all_, item)
                    if not payload.directors:
                        payload.directors = self.get_directors(find_all_, item)         


        payload.rating = self.get_rating(html_soup)
        payload.image = self.get_images(html_soup)
        payload.is_adult = self.get_is_adult(payload.rating)
        payload.packages = packages
        payload.createdAt = self._created_at
        if type_ == 'movie':
            return payload.payload_movie()
        if type_ == 'serie':
            return payload.payload_serie()

        return payload
    
    def get_title_h1(self, html_soup):
        try:
            title = html_soup.find('h1',{'data-automation-id': 'title'}).text
            return title
        except Exception:
            return self.get_title_image(html_soup)    

    def get_title_image(self, html_soup):
        title = html_soup.find('img',{'class': '_1GS1_C'})
        title = title['alt']
        return title  

    def get_id(self, deeplink):
        id_base = re.search('detail\/.*\/',deeplink).group()
        id = id_base.replace('detail','').replace('/','')
        return id
    
    def get_year(self, html_soup):
        find_year = html_soup.find('span', {'data-automation-id': 'release-year-badge'})
        year = int(find_year.text) if find_year else None
        if year != None and (year < 1870 or year > datetime.now().year):
            year = None
        return year   

    def get_duration(self, html_soup):
        duration = None # checkear si tiene la estructura de hora igual en todos los paises, por ahora lo dejo para los paises
        #if self.country in ['LATAM', 'BR', 'MX', 'HK', 'IL']: # en esta lista
        find_duration = html_soup.find('span',{'data-automation-id':'runtime-badge'})
        duration = self.get_duration_time(find_duration.text) if find_duration else None
        return duration

    def get_duration_time(self, duration_text):
        """
        Método para obtener duracion de contenido

        Args:
            duration_text [str]: duracion en formato NUMh NUMmin 

        Retruns:
            duration [int]: duracion en minutos
        """
        try: 
            if 'h' in duration_text:
                horas, minutos = duration_text.split('h')
            else:
                horas = None
                minutos = duration_text

            horas = int(re.findall(r'\d+', horas)[0]) if horas else 0
            minutos = int(re.findall(r'\d+', minutos)[0]) if minutos and minutos.strip() != '' else 0

            duration = horas * 60 + minutos 
            duration = duration if duration != 0 else None
        except Exception:
            return None
        
        return duration

    def get_synopsis(self, html_soup):
        find_synopsis = html_soup.find('div', {'data-automation-id': 'atfSynopsisExpander'})
        synopsis = self.cleanSynopsis(find_synopsis.text) if find_synopsis else None
        return synopsis 

    def get_rating(self, html_soup):
        find_rating = html_soup.find('span', {'data-automation-id': 'rating-badge'})
        rating = None
        if find_rating:
            rating = find_rating.text.strip()
        return rating
    
    def get_is_adult(self, rating):
        try:
            n_rating = re.search('\d{1,2}',rating).group()
            n_rating = int(n_rating)
            if n_rating>=18:
                return True
        except Exception:
            pass
        return False
    
    def get_images(self, html_soup):
        find_images = [html_soup.find('img', class_='_2ZnCkI').get('src')] if html_soup.find('img', class_='_2ZnCkI') else None
        images = find_images if find_images else None
        return images

    def get_packages(self, browser):
        """Método para obtener los packages.

        Args:
            browser (obj): Session de selenium para obtener info de packages.

        Returns:
            list: Obtiene lista con los packages.
        """
        transaction = False
        packages = []

        buttons = browser.find_elements_by_tag_name('button')
        for button in buttons:
            if button.get_attribute('name') == 'more-purchase-options':
                button.click()
                time.sleep(1)
                transaction = True
                break

        if not transaction:
            packages = [{"Type": "subscription-vod"}]
            return packages

        soup = BeautifulSoup(browser.page_source, 'lxml')
        all_data = soup.find('div', {'class': re.compile('av-narrow$')})        
        for div in all_data:
            if 'dvui-modal-content' in div.get("class"):
                price_tags = div.contents[0]
                first_dict = {}
                for price_tag in price_tags:
                    key = None
                    tag_list = []
                    for n, tag in enumerate(price_tag):                        
                        # print(n)
                        # print(tag.text)
                        if n == 0:
                            key = tag.text.upper().strip()
                        else:
                            tag_list.append(tag.text.strip())
                    first_dict[key] = tag_list
    
        rent_dict = {}
        rents = first_dict.get('RENT')

        # En el caso de que sea Store de México.
        if not rents:
            rents = first_dict.get('ALQUILAR')
        if rents:
            for rent in rents:
                if 'MX' in self._platform_code.upper():
                    try:
                        rent = rent.split('document')[0].strip()
                    except:
                        pass
                if len(rent) < 2 or len(rent) > 20:
                    continue
                # print(rent)
                price = float(int(re.sub("\D", "", rent, flags=re.IGNORECASE))/ 100)
                definition = rent.split(" ")[1].strip()
                if definition == 'UHD':
                    definition = '4K'
                rent_dict[definition] = price

        buy_dict = {}
        buys = first_dict.get('BUY')
        if not buys:
            buys = first_dict.get('COMPRAR')
        if buys:
            for buy in buys:
                if 'MX' in self._platform_code.upper():
                    try:
                        buy = buy.split('document')[0].strip()
                    except:
                        pass
                if len(buy) < 2 or len(buy) > 20:
                    continue
                price = float(int(re.sub("\D", "", buy, flags=re.IGNORECASE))/ 100)
                definition = buy.split(" ")[1].strip()
                if definition == 'UHD':
                    definition = '4K'
                buy_dict[definition] = price

        definitions = set(list(rent_dict.keys()) + list(buy_dict.keys()))

        for definition in definitions:
            package_dict = {}
            package_dict["Type"] = "transaction-vod"
            package_dict["Definition"] = definition
            package_dict["Currency"] = self.currency
            rent_value = rent_dict.get(definition)
            if rent_value:
                package_dict["RentPrice"] = rent_value
            buy_value = buy_dict.get(definition)
            if buy_value:
                package_dict["BuyPrice"] = buy_value
            
            packages.append(package_dict)

        return packages

    def get_cast(self, find_all_, item):
        cast_name = ['Reparto', 'Atores principais' ,'Starring', 'بطولة', 'עם',]
        if item.dt.text.strip() in cast_name:
            cast = [_replace(people.text) for people in find_all_]
            if cast:
                if len(cast) == 1 and "," in cast[0]:
                    cast = cast[0].split(',')
                return cast
        return None
        
    def get_genres(self, find_all_, item):
        genres_name = ['Géneros', 'Gêneros', 'Genres' ,'סוגות' ,'الأصناف الفنية']
        if item.dt.text.strip() in genres_name:
            genres = [genre.text for genre in find_all_]
            return genres
        else:
            return None
        
    def get_directors(self, find_all_, item):
        directors_name = ['Dirección','Diretores','Directors','במאים' ,'إخراج']
        if item.dt.text.strip() in directors_name:
            directors = []
            for director in find_all_:
                if _replace(director.text) != 'N/A':
                    directors.append(_replace(director.text))
            if directors:
                if len(directors) == 1 and "," in directors[0]:
                    directors = directors[0].split(',')
            else:
                    return None
            return directors
        return None
 
    def clean_title(self, title):
        """Método para limpiar títulos.

        Args:
            title (str): Titulo sucio.

        Returns:
            str: Devuelve título limpio.
        """
        title = str(title)
        # Lenguajes a filtrar:
        lenguages = [
            "Hindi",
            "Tamil",
            "Telugu",
            "Malayalam",
            "Kannada"
        ]

        for lang in lenguages:
            filtro = f"\({lang}\)$"
            clean_title = re.sub(filtro, "" ,title ,flags=re.IGNORECASE)
            clean_title = clean_title.strip()
            if title != clean_title:
                break
            
        return clean_title
    
    def cleanSynopsis(self, synopsis):
        if synopsis:
            synopsis_cleaned = synopsis.replace('&#39;',"'").replace('&#34;','"').replace('\n', '').replace('\r','').replace('\t','')
            return synopsis_cleaned 
        else:
            return None
    
