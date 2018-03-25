import requests as request
import datetime
import os
import psutil

port = 8081


def start_browser_proxy():
    os.system("../libs/browsermob-proxy-2.1.4/bin/browsermob-proxy")


def end_browser_proxy():
    for process in psutil.process_iter():
        if process.name() == 'browsermob-prox':
            process.kill()


def start_capture():
    startUrl = 'http://localhost:8080/proxy'
    startData = '{"port": ' + str(port) + '}'
    response = request.post(startUrl, startData)
    assert (response.status_code == 200)
    print("initialized at port " + str(port))

    harUrl = 'http://localhost:8080/proxy/' + str(port) + '/har'
    harData = '{}'
    response = request.put(harUrl, harData)
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


end_browser_proxy()
start_browser_proxy()
start_capture()

input("press enter to stop capture & save file")

end_capture()
end_browser_proxy()
