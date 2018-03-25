from selenium import webdriver

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--proxy-server=%s' % "127.0.0.1:8081")
chrome_options.add_extension('../netflix-1080p-1.2.9.crx')

chrome = webdriver.Chrome(chrome_options=chrome_options)


chrome.get('https://www.youtube.com/watch?v=dT5ALH3ICTc')

print(chrome.execute_script("return document.getElementById('movie_player').getAvailableQualityLevels()"))