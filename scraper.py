from selenium.webdriver.common import desired_capabilities
from seleniumwire import webdriver as wire_webdriver
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
import time
import datetime
import random
import urllib
import os
import configparser
import config


class Scrap:
    def __init__(self, remote=False, headless=False, proxy=False, base_dir=f"{os.path.dirname(os.path.realpath(__file__))}/selenium_modules/"):
        self.remote = remote
        self.headless = headless
        self.cookies = None
        self.proxy = proxy
        self.base_dir = base_dir
        
        if proxy:
            self.get_credentials()

    def log(s,t=None):
            now = datetime.datetime.now()
            if t == None :
                    t = "Main"
            print ("%s :: %s -> %s " % (str(now), t, s))

    def get_credentials(self, retry=False):
        config = configparser.ConfigParser()
        try:
            config.read(f"{os.path.dirname(os.path.realpath(__file__))}/credentials.ini")
            self.brightdata_username = config["BRIGHTDATA"].get("brightdata_username")
            self.brightdata_pwd = config["BRIGHTDATA"].get("brightdata_pwd")
        except:
            if not retry:
                self.get_credentials()


    def __parse_url(self, url):
        p = urllib.parse.urlparse(url, 'http')
        netloc = p.netloc or p.path
        path = p.path if p.netloc else ''
        if not netloc.startswith('www.'):
            netloc = 'www.' + netloc

        p = urllib.parse.ParseResult('http', netloc, path, *p[3:])
        return p.geturl()

    def get_proxies(self):
        """
            Uses Bright Data proxies
        """
        port = 22225
        session_id = random.random()
        super_proxy_url = "http://%s-country-fr-session-%s:%s@zproxy.lum-superproxy.io:%d" % (
            self.brightdata_username,
            session_id,
            self.brightdata_pwd,
            port,
        )
        return {
            "http": super_proxy_url,
            "https": super_proxy_url,
        }

    def __driver(self, download_path=""):
        options = webdriver.ChromeOptions()
        # options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        if download_path:
            options.add_experimental_option("prefs", {
                "download.default_directory": download_path,
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": True
            })

        wire_options = {}

        if self.proxy:
             wire_options['proxy'] = self.get_proxies()

        if self.headless:
            options.add_argument("--headless")
        else:
            options.add_extension(f'{self.base_dir}idontcareaboutcookies.crx')

        if self.proxy and not self.remote:
            return wire_webdriver.Chrome(f'{self.base_dir}chromedriver', seleniumwire_options=wire_options, options=options)

        elif self.proxy and self.remote:
            return wire_webdriver.Remote(command_executor="http://127.0.0.1:4444/wd/hub", desired_capabilities=DesiredCapabilities.CHROME, seleniumwire_options=wire_options.update({"addr": "http://127.0.0.1:4444/wd/hub"}), options=options)

        elif not self.proxy and self.remote:
            return webdriver.Remote(command_executor="http://127.0.0.1:4444/wd/hub", desired_capabilities=DesiredCapabilities.CHROME, options=options)

        return webdriver.Chrome(f'{self.base_dir}chromedriver', options=options)

    def get(self, url, timeout=60, has_timeout=False, sleep=0):
        driver = self.__driver()
        driver.set_page_load_timeout(timeout)
        try:
            driver = self.process_get(driver, self.__parse_url(url), sleep)

        except Exception as e:
            print(e)
            if e is TimeoutException and not has_timeout:
                self.log("Connection failed, retry")
                return self.get(self.__parse_url(url), timeout, True)
            else:
                driver.execute_script("window.stop();")
        data = driver.page_source
        driver.quit()

        return data

    def sleep_get(self, driver, url, sleep):
        data = self.get(url)
        time.sleep(sleep)
        return data

    def get_driver(self, timeout=60):
        driver = self.__driver()
        driver.set_page_load_timeout(timeout)
        return driver

    def get_body_text(self, url=None):
        soup = BeautifulSoup(self.get(url), 'lxml')
        [s.decompose() for s in soup("script")]  # remove <script> elements
        if not soup.body:
            return None
        return soup.body.get_text()
    