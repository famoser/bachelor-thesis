import requests as request
import datetime
import psutil
import subprocess
import time
from selenium import webdriver

port = 8081


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

    assert (response.status_code == 200)
    print("initialized at port " + str(port))

    harUrl = 'http://localhost:8080/proxy/' + str(port) + '/har'
    harData = '{}'
    response = request.put(harUrl, harData)
    print(response.status_code)
    assert (response.status_code == 204)
    print('started capture at port ' + str(port))


def end_capture():
    saveUrl = 'http://localhost:8080/proxy/' + str(port) + '/har'
    response = request.get(saveUrl)
    fileName = datetime.datetime.now().isoformat()
    with open(fileName + '.json', "w") as text_file:
        print(response.content.decode(), file=text_file)
    assert (response.status_code == 200)
    print('saved capture')

    stopUrl = 'http://localhost:8080/proxy/' + str(port)
    response = request.delete(stopUrl)
    assert (response.status_code == 200)
    print('stopped at port ' + str(port))


def start_browser(netflix_id, rate):
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--proxy-server=%s' % "127.0.0.1:" + str(port))
    chrome_options.add_extension('../netflix-1080p-1.2.9.crx')

    chrome = webdriver.Chrome(chrome_options=chrome_options)
    chrome.get('https://www.netflix.com/watch/' + netflix_id + '?rate=' + rate)

    chrome.execute_script("fasterPlayback()")
    i = 20
    while i > 0:
        print(chrome.execute_script("return stillActive()"))
        time.sleep(5)
        i -= 0

    return chrome


def end_browser(browser):
    browser.close()


end_browser_proxy()
start_browser_proxy()
start_capture()
chrome = start_browser("80018499", "1")

input("press enter to stop capture & save file")

end_browser(chrome)
end_capture()
end_browser_proxy()
