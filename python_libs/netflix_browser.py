import pickle
import os
import json
import time
from selenium import webdriver

from .config import StaticConfig

config = StaticConfig()


class NetflixBrowser:
    credentials = None
    cookies = None
    chrome = None
    port = None

    def __init__(self, port):
        self.port = port

        # resolve credentials if possible
        if os.path.isfile(config.credentials_file_path):
            self.credentials = json.load(open(config.credentials_file_path))

        # resolve cookies if possible
        if os.path.isfile(config.cookie_file_path):
            self.cookies = pickle.load(open(config.cookie_file_path, "rb"))

    # construct the selenium chrome browser
    def __try_create_chrome(self):
        # use the test video URl to try to login
        video_url = 'https://www.netflix.com/watch/80018499'

        # create chrome config using a localhost proxy & the modified netflix extension
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--proxy-server=%s' % "127.0.0.1:" + str(self.port))
        chrome_options.add_extension(config.netflix_extension_path)

        # construct chrome & request the test url
        self.chrome = webdriver.Chrome(chrome_options=chrome_options)
        self.chrome.get(video_url)

        # if cookies set, add them to the browser
        if self.cookies is not None:
            for cookie in self.cookies:
                self.chrome.add_cookie(cookie)

                # request video URL again to check if we are logged in
                self.chrome.get(video_url)

        # check for the login button
        login_link = self.__try_find_element_by_class("authLinks", 2)
        if login_link is not None:
            # login button found, so we need to perform a login
            link = login_link.get_attribute("href")
            self.chrome.get(link)

            # get username & password field
            username_field = self.__try_find_element_by_id("email")
            password_field = self.__try_find_element_by_id("password")

            # fill in usename & password according to the credentials
            username_field.send_keys(self.credentials["netflix"]["username"])
            password_field.send_keys(self.credentials["netflix"]["password"])

            # submit the form
            password_field.submit()

            # click on the profile to be used
            self.chrome.get("https://www.netflix.com/SwitchProfile?tkn=" + self.credentials["netflix"]["profile"])

            # save cookies for next time
            cookies = self.chrome.get_cookies()
            pickle.dump(cookies, open(config.cookie_file_path, "wb"))

    def play_in_browser(self, netflix_id):
        # construct url by appending the configured rate
        # javascript will then read out, and limit the netflix video to this default
        video_url = 'https://www.netflix.com/watch/' + str(netflix_id) + '?rate=' + str(rate)

        # load page & let video player initialize
        self.chrome.get(video_url)
        time.sleep(5)

        # check for fatal error 3 times
        if self.__try_find_element_by_class("nfp-fatal-error-view", 3) is not None:
            title = self.__try_find_element_by_class("error-title", 3)
            print(title.text)
            if title is not None and title.text == "Multiple Netflix Tabs":
                # this error is critical, netflix won't allow us to continue captureing
                # user may needs to reboot the computer for it to work again
                print("aborting; consider rebooting the computer for the error to go away")
                return False
            else:
                # unknown error occurred; per default we continue
                return True

        # start playback speedup from netflix extension
        self.chrome.execute_script("startFasterPlayback(10, " + str(config.skip_seconds) + ")")
        i = 200
        while i > 0:
            if not self.chrome.execute_script("return stillActive()"):
                break

            time.sleep(config.wait_seconds)
            i -= 1

        return True

    def __try_find_element_by_id(self, element_id, retries=5):
        while retries > 0:
            try:
                return self.chrome.find_element_by_id(element_id)
            except:
                # don't care, just retry
                time.sleep(1)
                retries -= 1
        return None

    def __try_find_element_by_class(self, element_id, retries=5):
        while retries > 0:
            try:
                return self.chrome.find_element_by_class_name(element_id)
            except:
                # don't care, just retry
                time.sleep(1)
                retries -= 1
        return None
