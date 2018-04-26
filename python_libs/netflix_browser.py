import pickle
import os
import json
import time
from selenium import webdriver
from selenium.webdriver.remote.webelement import WebElement
from typing import Optional

from .config import StaticConfig
from .config import Inventory

config = StaticConfig()
inventory = Inventory()


class NetflixBrowser:
    __credentials = None
    __browser = None
    __port = None
    __use_chrome = None

    def __init__(self, port: int, use_chrome: bool = True):
        """
        browser with netflix extension, using localhost:port as a proxy
        :param port: the port to use
        """
        self.__port = port
        self.__use_chrome = use_chrome

    def __enter__(self):
        # resolve credentials if possible
        if os.path.isfile(config.credentials_file_path):
            self.__credentials = json.load(open(config.credentials_file_path))

        # start chrome or firefox
        if self.__use_chrome:
            # finally start the browser
            self.__browser = self.__try_create_chrome()
            cookie_path = config.chrome_cookie_file_path
        else:
            self.__browser = self.__try_create_firefox()
            cookie_path = config.firefox_cookie_file_path

        # resolve cookies if possible
        cookies = None
        if cookie_path is not None and os.path.isfile(cookie_path):
            cookies = pickle.load(open(cookie_path, "rb"))

        # login & save cookies for next time
        cookies = self.__try_login(cookies)
        if cookies is not None:
            pickle.dump(cookies, open(cookie_path, "wb"))

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # closes the chrome browser
        self.__browser.quit()

    def __try_create_firefox(self):
        # create chrome config using a localhost proxy & the modified netflix extension
        firefox_options = webdriver.FirefoxOptions()

        # construct chrome & request the test url
        return webdriver.Firefox(firefox_options=firefox_options)

    def __try_create_chrome(self):
        """
        construct the selenium chrome browser
        """

        # create chrome config using a localhost proxy & the modified netflix extension
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_extension(config.netflix_extension_path)

        # disable SSL checking & enforhrome ce redownload of everything
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument('--disable-application-cache')

        if self.__port != 0:
            chrome_options.add_argument('--proxy-server=%s' % "127.0.0.1:" + str(self.__port))

        # construct chrome & request the test url
        return webdriver.Chrome(chrome_options=chrome_options)

    def __try_login(self, cookies):
        # use the test video URl to try to login
        video_url = self.__get_video_url(inventory.test_video)

        self.__browser.get(video_url)

        # if cookies set, add them to the browser
        if cookies is not None:
            for cookie in cookies:
                self.__browser.add_cookie(cookie)

        # request video URL again to check if we are logged in
        self.__browser.get(video_url)

        # check for the login button
        login_link = self.__try_find_element_by_class("authLinks", 2)
        if login_link is not None:
            # login button found, so we need to perform a login
            link = login_link.get_attribute("href")
            self.__browser.get(link)

            # get username & password field
            username_field = self.__try_find_element_by_id("email")
            password_field = self.__try_find_element_by_id("password")

            # fill in username & password according to the credentials
            username_field.send_keys(self.__credentials["netflix"]["username"])
            password_field.send_keys(self.__credentials["netflix"]["password"])

            # submit the form
            username_field.submit()

            # click on the profile to be used
            self.__browser.get("https://www.netflix.com/SwitchProfile?tkn=" + self.__credentials["netflix"]["profile"])

            # save cookies for next time
            return self.__browser.get_cookies()
        return None

    @staticmethod
    def __get_video_url(netflix_id: int, rate: int = None):
        url = 'https://www.netflix.com/watch/' + str(netflix_id)
        if rate is not None:
            url += '?rate=' + str(rate)

        return url

    def navigate(self, netflix_id: int) -> bool:
        video_url = self.__get_video_url(netflix_id)
        self.__browser.get(video_url)
        return True

    def set_video_time(self, video_time: int) -> bool:
        self.__browser.execute_script("seek(" + str(video_time) + ")")
        return True

    def play_in_browser(self, netflix_id: int, rate: int) -> bool:
        """
        opens the netflix video and gets the javascript to limit the profiles according to the rate
        then plays the video, speeding up according to the config
        it will return False if you can not continue to use this instance as a capture
        (happen when "Multiple Netflix Tabs" error pops up)

        :param netflix_id: the video id
        :param rate: the amount it should be
        :return: False if you cannot continue capture, else True
        """
        # construct url by appending the configured rate
        # javascript will then read out, and limit the netflix video to this default
        video_url = self.__get_video_url(netflix_id, rate)

        # load page & let video player initialize
        self.__browser.get(video_url)
        time.sleep(5)

        # check for fatal error 3 times
        if self.__try_find_element_by_class("nfp-fatal-error-view", 3) is not None:
            title = self.__try_find_element_by_class("error-title", 3)
            print("Netflix error occurred: " + title.text)
            if title is not None:
                if title.text == "Multiple Netflix Tabs":
                    # this error is critical, netflix won't allow us to continue capturing
                    # user may needs to reboot the computer for it to work again
                    print("aborting; consider rebooting the computer for the error to go away")
                    return False
                if title.text == "Unexpected Error":
                    # this error happens when javascript selects a profile unsupported by this video type
                    # this happens often, and is no reason to stop capturing
                    return True
                print("halting; new error found!")
                time.sleep(500000)
            else:
                # unknown error occurred; per default we continue
                return True

        # start playback speedup from netflix extension
        self.__browser.execute_script("startFasterPlayback(10, " + str(config.skip_seconds) + ")")
        i = 200
        while i > 0:
            if not self.__browser.execute_script("return stillActive()"):
                break

            time.sleep(config.wait_seconds)
            i -= 1

        return True

    def __try_find_element_by_id(self, css_id: str, retries: int = 5) -> Optional[WebElement]:
        """
        looks in the chrome instance if it can find that element
        retries as long as specified, waits 1 seconds before trying again

        :param css_id: the id of the css element
        :param retries: the amount of retries to perform
        :return: the selenium object if found, else None
        """
        while retries > 0:
            try:
                return self.__browser.find_element_by_id(css_id)
            except:
                # don't care, just retry
                time.sleep(1)
                retries -= 1

        return None

    def __try_find_element_by_class(self, css_class: str, retries: int = 5) -> Optional[WebElement]:
        """
        looks in the chrome instance if it can find that element
        retries as long as specified, waits 1 seconds before trying again

        :param css_class: the class of the css element
        :param retries: the amount of retries to perform
        :return: the selenium object if found, else None
        """

        while retries > 0:
            try:
                return self.__browser.find_element_by_class_name(css_class)
            except:
                # don't care, just retry
                time.sleep(1)
                retries -= 1

        return None

    @staticmethod
    def __try_with_repeat(func, retries: int):
        """
        retries a function multiple times, returns None if all fail
        waits 1 second before each retry

        :param func: the function to try repeatedly
        :param retries: the amount of retries to try
        :return:
        """
        while retries > 0:
            try:
                return func()
            except:
                # don't care, just retry
                time.sleep(1)
                retries -= 1
        return None
