import requests as request
import datetime
import psutil
import subprocess
import time
import json
import pickle
import os
from selenium import webdriver

capture_dir = "capture"
capture_version = "1"
browsermob_dir = "tools/browsermob-proxy-2.1.4"
netflix_extension_path = "tools/netflix-1080p-1.2.9.crx"
config_dir = "."
capture_speed = "120"

cookie_file_name = "cookies.pkl"
cookie_path = config_dir + "/" + cookie_file_name


def start_browser_proxy():
    subprocess.Popen([browsermob_dir + "/bin/browsermob-proxy"])
    i = 3
    while i > 0:
        print("waiting " + str(i))
        time.sleep(1)
        i -= 1


def end_browser_proxy():
    found = None
    dictionary = {}
    for process in psutil.process_iter():
        dictionary[process.pid] = process

    for pid in sorted(dictionary):
        if 'browsermob-prox' in dictionary[pid].name():
            dictionary[pid].kill()
            found = True
            print("found & killed old process")
        if "java" in dictionary[pid].name() and found:
            dictionary[pid].kill()
            print("found & killed old java process")
            return


capture_started = False
capture_port = None


def start_capture():
    global capture_started, capture_port

    if not capture_started:
        startUrl = 'http://localhost:8080/proxy'
        startData = '{}'
        response = request.post(startUrl, startData)
        startResponse = json.loads(response.content)
        port = startResponse["port"]
        capture_port = port
        assert (response.status_code == 200)
        print("initialized at port " + str(port))

        capture_started = True

        harUrl = 'http://localhost:8080/proxy/' + str(port) + '/har'
        harData = '{}'
        response = request.put(harUrl, harData)
        print(response.status_code)
        assert (response.status_code == 204)
        print('started capture at port ' + str(port))

    return capture_port


cookies = None
chrome = None

def create_chrome(video_url, port):
    global cookies, cookie_path

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--proxy-server=%s' % "127.0.0.1:" + str(port))
    chrome_options.add_extension(netflix_extension_path)

    chrome = webdriver.Chrome(chrome_options=chrome_options)

    chrome.get(video_url)

    if cookies is None and os.path.isfile(cookie_path):
        cookies = pickle.load(open(cookie_path, "rb"))

    if cookies is not None:
        for cookie in cookies:
            chrome.add_cookie(cookie)

    chrome.get(video_url)

    trying_to_login = False
    try:
        login_link = chrome.find_element_by_class_name("authLinks")
        link = login_link.get_attribute("href")
        chrome.get(link)
        trying_to_login = True

        credentials = json.load(open(config_dir + '/credentials.json'))

        username_field = selenium_try_find_element_by_id(chrome, "email")
        username_field.send_keys(credentials["netflix"]["username"])

        password_field = selenium_try_find_element_by_id(chrome, "password")
        password_field.send_keys(credentials["netflix"]["password"])

        password_field.submit()

        chrome.get("https://www.netflix.com/SwitchProfile?tkn=" + credentials["netflix"]["profile"])
    except:
        if trying_to_login:
            print("login failed")
            return False
        else:
            print("already logged in")

    return True


def play_in_browser(netflix_id, rate):
    video_url = 'https://www.netflix.com/watch/' + str(netflix_id) + '?rate=' + str(rate)

    global cookies, chrome

    if chrome is None:
        if not create_chrome(video_url, port):
            return False

    chrome.get(video_url)

    cookies = chrome.get_cookies()
    pickle.dump(cookies, open(cookie_path, "wb"))

    time.sleep(5)
    'check for fatal error && sleeps 5 seconds if not'
    if selenium_try_find_element_by_class(chrome, "nfp-fatal-error-view", 3) is not None:
        title = selenium_try_find_element_by_class(chrome, "error-title", 3)
        if title is not None and title.text == "Multiple Netflix Tabs":
            create_chrome(video_url, port)

            chrome.get(video_url)

            cookies = chrome.get_cookies()
            pickle.dump(cookies, open(cookie_path, "wb"))
            if selenium_try_find_element_by_class(chrome, "nfp-fatal-error-view", 3) is not None:

                print("error view found, aborting")
                return True
        else:
            print("error view found, aborting")
            return True

    # start playback speedup
    chrome.execute_script("startFasterPlayback(10, " + capture_speed + ")")
    i = 200
    while i > 0:
        if not chrome.execute_script("return stillActive()"):
            break

        if selenium_try_find_element_by_class(chrome, "nfp-fatal-error-view", 1) is not None:
            print("error view found, aborting")
            return True

        time.sleep(4)
        i -= 1

    return True


def selenium_try_find_element_by_id(driver, element_id, retries=5):
    while retries > 0:
        try:
            return driver.find_element_by_id(element_id)
        except:
            # don't care, just retry
            time.sleep(1)
            retries -= 1
    return None


def selenium_try_find_element_by_class(driver, element_id, retries=5):
    while retries > 0:
        try:
            return driver.find_element_by_class_name(element_id)
        except:
            # don't care, just retry
            time.sleep(1)
            retries -= 1
    return None


def end_capture(netflix_id, rate, port):
    saveUrl = 'http://localhost:8080/proxy/' + str(port) + '/har'
    response = request.get(saveUrl)
    fileName = str(netflix_id) + '_' + str(rate) + "_ " + datetime.datetime.now().isoformat()
    with open(capture_dir + "/" + fileName + "_" + capture_version + '.json', "w") as text_file:
        print(response.content.decode(), file=text_file)
    assert (response.status_code == 200)
    print('saved capture')

    # stopUrl = 'http://localhost:8080/proxy/' + str(port)
    # response = request.delete(stopUrl)
    # assert (response.status_code == 200)
    # print('stopped at port ' + str(port))


end_browser_proxy()
start_browser_proxy()

'testvideo 80018499'
netflix_ids = [80111451, 80111452, 80018499]
no_errors = True
for netflix_id in netflix_ids:
    rate = 1
    while rate <= 4 and no_errors:
        port = start_capture()
        no_errors = no_errors and play_in_browser(netflix_id, rate, port)
        end_capture(netflix_id, rate, port)
        rate += 1

end_browser_proxy()

if not no_errors:
    print("something failed; stopped capture early")

if chrome is not None:
    chrome.close()
