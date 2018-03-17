import requests as request
import datetime
import json
import os

from subprocess import check_output


def start_browser_proxy():
    os.system("../libs/browsermob-proxy-2.1.4/bin/browsermob-proxy")


def end_browser_proxy():
    while 1:
        pid = check_output(["pidof", "-s", "/bin/sh ../libs/browsermob-proxy-2.1.4/bin/browsermob-proxy"])
        if pid == 0:
            break
        os.system("kill " + str(pid))
        print("killed " + str(pid))

end_browser_proxy()
start_browser_proxy()
print('start proxy at default port')

startUrl = 'http://localhost:8080/proxy'
startData = '{"port": 8081}'
response = request.post(startUrl, startData)
startResponse = json.loads(response.content)
port = startResponse["port"]
assert (response.status_code == 200)

print('starting capture at port ' + str(port))

harUrl = 'http://localhost:8080/proxy/' + str(port) + '/har'
harData = '{"captureHeaders":true, "captureCookies":true}'
harData = '{}'
response = request.put(harUrl, harData)
assert (response.status_code == 204)

input("press enter to stop capture & save file")

saveUrl = 'http://localhost:8080/proxy/' + str(port) + '/har'
response = request.get(saveUrl)
fileName = datetime.datetime.now().isoformat()
with open(fileName + '.json', "w") as text_file:
    print(response.content.decode(), file=text_file)

assert (response.status_code == 200)

stopUrl = 'http://localhost:8080/proxy/' + str(port)
response = request.delete(stopUrl)
assert (response.status_code == 200)

end_browser_proxy()
