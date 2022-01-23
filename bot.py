from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from bots.models import Bot
from time import sleep
from apps.models import App
from django.db import models
from random import randint
#from utils.models import WebBot
from immoscout.models import ImmoscoutUser, ImmoscoutUserData, ApplicationProfile, Flat

import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from django.db.models.signals import post_save, post_delete, pre_save
import sys
from datetime import datetime
options = Options()
options.add_argument("--headless")
options.add_argument("--window-size=1920x1080")

from bs4 import BeautifulSoup
from web.models import RotatingProxySession
import asyncio

class ImmoscoutBotManager(models.Manager):
    def create(self, profile, *args, **kwargs):
        login_data = ImmoscoutUser.objects.get_or_none(user=profile.user)
        user_data = ImmoscoutUserData.objects.get_or_none(user=profile.user)
        proxy=RotatingProxySession.objects.create()
        return super(ImmoscoutBotManager, self).create(login_data=login_data, proxy=proxy,
                                                       user_data=user_data, profile=profile, *args, **kwargs)
        
class ImmoscoutBot(Bot):   
    login_data          = models.ForeignKey(ImmoscoutUser, null=True, blank=True, on_delete=models.SET_NULL)
    user_data           = models.ForeignKey(ImmoscoutUserData, null=True, blank=True, on_delete=models.SET_NULL)
    proxy               = models.ForeignKey(RotatingProxySession, blank=True, on_delete=models.CASCADE)
    
    objects = ImmoscoutBotManager()
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.login_success = None
        self.flats = []
        self.driver = None
    
    def has_user_profile(self):
        return ImmoscoutUser.objects.active(self.profile.user) or ImmoscoutUserData.objects.active(self.profile.user)
    
    def activate(self):
        if self.login_data or self.user_data:
            super(ImmoscoutBot, self).activate()

    def get_url(self):
        self.driver.get(self.profile.url)

    def load_chrome(self):
        self.driver = webdriver.Chrome(f'immoscout/chromedriver', options=options) 

    def login(self):
        #Login
        login_data = self.login_data
        self.login_success = False
        try:
            self.driver.get('https://www.immobilienscout24.de/geschlossenerbereich/start.html')
            self.driver.find_element_by_id('username').send_keys(login_data.username)
            self.driver.find_element_by_id("submit").click()
            el = WebDriverWait(self.driver, 40).until(EC.presence_of_element_located((By.ID, 'password')))
            el.send_keys(login_data.password)
            self.driver.find_element_by_id("loginOrRegistration").click()
            success_url = 'https://www.immobilienscout24.de/meinkonto/overview/'
            self.login_success = self.driver.current_url == success_url
        except Exception as e:
            self.log(str(e), source='[Login Error]')

    def parse_main_page(self):
        self.flats = []
        resp = self.proxy.get(self.profile.url)
        soup = BeautifulSoup(resp.text, features="lxml")
        ul = soup.find("ul", {"id": "resultListItems"})
        if not ul:
            self.log('no "resultListItems" found in content')
            self.proxy.next()
            return
        for link in ul.find_all('a', {'class': 'result-list-entry__brand-title-container'}, href=True):
            href = 'https://www.immobilienscout24.de{href}'.format_map(link)
            flat = Flat.objects.create(title=link.text, link=href, user=self.profile.user, 
                                       user_data=self.user_data, login_data=self.login_data, profile=self.profile)
            if flat:
                self.flats.append(flat)
                
    def do_login(self):
        return self.login_data.active if self.login_data else False
    
    def run_main_loop(self, reload_time, proxy_switch_time):
        '''
        reload_time: time in seconds with in the bot have to reload the main page
        proxy_switch_time: time in minutes to stay on one proxy before force a switch
        '''
        count = 0
        while True:  
            self.parse_main_page()
            self.action()
            s = count * reload_time
            sys.stdout.write(f"\rreload..{count}; fetching time..{int((s - s%60)/60)} min. and {s%60} sec.")
            sleep(reload_time) 
            
            if count == (proxy_switch_time * 60 / reload_time):
                self.proxy.next()
                count = 0
            else:
                count += 1
                
    def run(self):
        self.load_chrome()
        if self.do_login():
            self.login()
            if not self.login_success:
                self.log('Login Failed', source='[Login Information]')
                exit()
            print('successfully logged in')
            #self.log('successfully logged in!', source='[Login Information]')

        # config
        reload_time = 5 # seconds
        proxy_switch_time = 10 # minutes
        
        self.run_main_loop(reload_time=reload_time, proxy_switch_time=proxy_switch_time)

            
    
    def get_total_count(self):
        return self.profile.user.flat_set.filter(profile=self.profile).count()
    
    def action(self):
        # wohnung für wohnung
        for flat in self.flats:
            submitted = False
            if flat.do_submit():
                submitted = self.submit(flat)            
                
            if submitted:
                msg = f'(SUBMITTED!) {flat.title}'
            else:
                msg = f'(NOT SUBMITTED!) {flat.title}'
                
            if self.profile.telegram:
                self.send_message(flat.link)
                
            self.log(msg, source=flat.link)      

           
            
    # Parsed Den Namen und Geschlecht des Anbieters (falls nicht möglich wird 'Damen und Herren verwendet'
    def get_salutation(self):
        content = self.driver.find_element_by_xpath("""//*[@id="is24-expose-modal"]\
                                    /div/div/div/div/div/div[1]/h4""").text.split()
        if 'Herr' in content:
            i = content.index('Herr')
            salutation = 'Sehr geehrter {}'.format(' '.join(content[i:]))
        elif 'Frau' in content:
            i = content.index('Frau')
            salutation = 'Sehr geehrte {}'.format(' '.join(content[i:]))
        else:
            salutation = 'Sehr geehrte Damen und Herren'

        return salutation


    # Drückt auf 'Anbieter Kontaktieren' un füllt die Form aus
    def write_info(self):
        # Geschlecht wählen
        el = WebDriverWait(self.driver, 40).until(
            EC.presence_of_element_located((By.ID, 'contactForm-salutation')))
        self.driver.execute_script("arguments[0].click();", el)

        for option in el.find_elements_by_tag_name('option'):
            if option.text == self.user_data.gender:
                option.click()
                break
        
        last_name = self.driver.find_element_by_id('contactForm-lastName')
        last_name.send_keys(self.user_data.last_name)
        
        first_name = self.driver.find_element_by_id('contactForm-firstName')
        first_name.send_keys(self.user_data.first_name)
        
        email = self.driver.find_element_by_id('contactForm-emailAddress')
        email.send_keys (self.user_data.email)
        
        if self.user_data.phone:
            phone = self.driver.find_element_by_id('contactForm-phoneNumber')
            phone.send_keys(self.user_data.phone)

        try:
            street = self.driver.find_element_by_id('contactForm-street')
            street.send_keys(self.user_data.street)
            
            house = self.driver.find_element_by_id('contactForm-houseNumber')
            house.send_keys(self.user_data.house)
            
            post_code = self.driver.find_element_by_id('contactForm-postcode')
            post_code.send_keys(self.user_data.post_code)
            
            city = self.driver.find_element_by_id('contactForm-city')
            city.send_keys(self.user_data.city)
        except:
            # form dont need Contackt information
            pass


    # Drückt auf 'Anbieter Kontaktieren' un füllt die Form aus
    def submit(self, flat):
        self.driver.get(flat.link)
        #'Anbieter Kontaktieren'
        element = WebDriverWait(self.driver, 20).until(EC.presence_of_element_located((By.XPATH, """//*[@id="is24-expose-contact-bar-top"]/div/div/div[1]/div/div[2]/a""")))
        self.driver.execute_script("arguments[0].click();", element)

        try:
            if not self.login_success and self.user_data.active:
                self.write_info()

            salutation = self.get_salutation()
            text_area = self.driver.find_element_by_id('contactForm-Message')
            text_area.clear()
            text = self.profile.text
            text_area.send_keys(f'{salutation}, \n\n{text}')

            sleep(1)
            
            #self.driver.find_element_by_xpath("//button[@data-ng-click='submit()'\
            #                             or contains(.,'Anfrage senden')]").click()
            sleep(1)
            return True
        
        except Exception as e:
            message = f'{e}\nMaby flat only for premium users'
            self.log(message, source='[contact Form Error]')
        
        return False

    

def immoscout_bot_post_delete_receiver(sender, instance, *args, **kwargs):
    if instance.proxy:
        instance.proxy.delete()
post_delete.connect(immoscout_bot_post_delete_receiver, sender=ImmoscoutBot)


#update data_profiles after change
def immoscout_data_post_save_receiver(sender, instance, created, *args, **kwargs):
    login_data = ImmoscoutUser.objects.get_or_none(user=instance.user)
    user_data = ImmoscoutUserData.objects.get_or_none(user=instance.user)
    ImmoscoutBot.objects.filter(profile__user=instance.user).update(login_data=login_data, user_data=user_data)

post_save.connect(immoscout_data_post_save_receiver, sender=ImmoscoutUser)
post_save.connect(immoscout_data_post_save_receiver, sender=ImmoscoutUserData)
