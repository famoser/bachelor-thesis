import requests as request

url = 'http://localhost:8080/proxy'
data = '{"port":8081}'

'starting proxy server'
response = request.post(url, data=data)

print(response)