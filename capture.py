import requests as request
import datetime
import psutil
import subprocess
import time
import json

from python_libs.config import StaticConfig
from python_libs.netflix_browser import NetflixBrowser

config = StaticConfig()
netflix_browser = NetflixBrowser()



def start_browser_proxy():
    subprocess.Popen([config.browsermob_dir + "/bin/browsermob-proxy"])
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




def end_capture(netflix_id, rate, port):
    saveUrl = 'http://localhost:8080/proxy/' + str(port) + '/har'
    response = request.get(saveUrl)
    fileName = str(netflix_id) + '_' + str(rate) + "_ " + datetime.datetime.now().isoformat().replace(":", "_")
    with open(cconfig.apture_dir + "/" + fileName + "_" + config.capture_version + '.json', "w") as text_file:
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
netflix_browser = NetflixBrowser()
for netflix_id in netflix_ids:
    rate = 1
    while rate <= 4 and no_errors:
        port = start_capture()
        no_errors = no_errors and play_in_browser(netflix_id, rate)
        end_capture(netflix_id, rate, port)
        rate += 1

end_browser_proxy()

if not no_errors:
    print("something failed; stopped capture early")

if chrome is not None:
    chrome.close()
