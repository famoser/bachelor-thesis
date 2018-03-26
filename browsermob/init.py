import requests as request
import datetime
import psutil
import subprocess
import time
import json
from selenium import webdriver


def start_browser_proxy():
    subprocess.Popen(["../libs/browsermob-proxy-2.1.4/bin/browsermob-proxy"])
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


def start_capture():
    startUrl = 'http://localhost:8080/proxy'
    startData = '{"port": ' + str(port) + '}'
    response = request.post(startUrl, startData)

    port = json.load(response.content)["port"]
    assert (response.status_code == 200)
    print("initialized at port " + str(port))

    harUrl = 'http://localhost:8080/proxy/' + str(port) + '/har'
    harData = '{}'
    response = request.put(harUrl, harData)
    print(response.status_code)
    assert (response.status_code == 204)
    print('started capture at port ' + str(port))

    return port

def play_in_browser(netflix_id, rate, port):
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--proxy-server=%s' % "127.0.0.1:" + str(port))
    chrome_options.add_extension('../netflix-1080p-1.2.9.crx')

    chrome = webdriver.Chrome(chrome_options=chrome_options)
    chrome.get('https://www.netflix.com/watch/' + str(netflix_id) + '?rate=' + str(rate))

    chrome.execute_script("fasterPlayback()")
    i = 20
    while i > 0:
        print(chrome.execute_script("return stillActive()"))
        time.sleep(5)
        i -= 0

    browser.close()


def end_capture(netflix_id, rate, port):
    saveUrl = 'http://localhost:8080/proxy/' + str(port) + '/har'
    response = request.get(saveUrl)
    fileName = str(netflix_id) + '_' + str(rate) + "_ " + datetime.datetime.now().isoformat()
    with open(fileName + '.json', "w") as text_file:
        print(response.content.decode(), file=text_file)
    assert (response.status_code == 200)
    print('saved capture')

    stopUrl = 'http://localhost:8080/proxy/' + str(port)
    response = request.delete(stopUrl)
    assert (response.status_code == 200)
    print('stopped at port ' + str(port))


end_browser_proxy()
start_browser_proxy()

rate = 1
netflix_ids = [80018499]
for netflix_id in netflix_ids:
	while rate <= 4:
		port = start_capture()
		chrome = play_in_browser(netflix_id, rate, port)
		end_capture(netflix_id, rate, port)


end_browser_proxy()
