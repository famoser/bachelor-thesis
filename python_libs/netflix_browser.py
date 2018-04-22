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
    __cookies = None
    __chrome = None
    __port = None

    def __init__(self, port: int):
        """
        browser with netflix extension, using localhost:port as a proxy
        :param port: the port to use
        """
        self.__port = port

    def __enter__(self):
        # resolve credentials if possible
        if os.path.isfile(config.credentials_file_path):
            self.__credentials = json.load(open(config.credentials_file_path))

        # resolve cookies if possible
        if os.path.isfile(config.cookie_file_path):
            self.__cookies = pickle.load(open(config.cookie_file_path, "rb"))

        # finally start chrome
        self.__try_create_chrome()

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # closes the chrome browser
        self.__chrome.quit()

    def __try_create_chrome(self):
        """
        construct the selenium chrome browser
        """

        # use the test video URl to try to login
        video_url = self.__get_video_url(inventory.test_video)

        # create chrome config using a localhost proxy & the modified netflix extension
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--proxy-server=%s' % "127.0.0.1:" + str(self.__port))
        chrome_options.add_extension(config.netflix_extension_path)

        # construct chrome & request the test url
        self.__chrome = webdriver.Chrome(chrome_options=chrome_options)
        self.__chrome.get(video_url)

        # if cookies set, add them to the browser
        if self.__cookies is not None:
            for cookie in self.__cookies:
                self.__chrome.add_cookie(cookie)

        # request video URL again to check if we are logged in
        self.__chrome.get(video_url)

        # check for the login button
        login_link = self.__try_find_element_by_class("authLinks", 2)
        if login_link is not None:
            # login button found, so we need to perform a login
            link = login_link.get_attribute("href")
            self.__chrome.get(link)

            # get username & password field
            username_field = self.__try_find_element_by_id("email")
            password_field = self.__try_find_element_by_id("password")

            # fill in username & password according to the credentials
            username_field.send_keys(self.__credentials["netflix"]["username"])
            password_field.send_keys(self.__credentials["netflix"]["password"])

            # submit the form
            password_field.submit()

            # click on the profile to be used
            self.__chrome.get("https://www.netflix.com/SwitchProfile?tkn=" + self.__credentials["netflix"]["profile"])

            # save cookies for next time
            cookies = self.__chrome.get_cookies()
            pickle.dump(cookies, open(config.cookie_file_path, "wb"))

    @staticmethod
    def __get_video_url(netflix_id: int, rate: int = None):
        url = 'https://www.netflix.com/watch/' + str(netflix_id)
        if rate is not None:
            url += '?rate=' + str(rate)

        return url

    def navigate(self, netflix_id: int) -> bool:
        video_url = self.__get_video_url(netflix_id)
        self.__chrome.get(video_url)
        return True

    def set_video_time(self, video_time: int) -> bool:
        self.__chrome.execute_script("seek(" + str(video_time) + ")")
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
        self.__chrome.get(video_url)
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
        self.__chrome.execute_script("startFasterPlayback(10, " + str(config.skip_seconds) + ")")
        i = 200
        while i > 0:
            if not self.__chrome.execute_script("return stillActive()"):
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
                return self.__chrome.find_element_by_id(css_id)
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
                return self.__chrome.find_element_by_class_name(css_class)
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
