import requests as request
import datetime
import json

print('start proxy at default port')

startUrl = 'http://localhost:8080/proxy'
startData = '{}'
response = request.post(startUrl, startData)
startResponse = json.loads(response.content)
port = startResponse["port"]
assert (response.status_code == 200)

print('starting capture at port ' + str(port))

harUrl = 'http://localhost:8080/proxy/' + str(port) + '/har'
harData = '{"captureHeaders":true, "captureCookies":true}'
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
