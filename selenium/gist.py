from selenium.webdriver import Firefox
import config

driver = Firefox(executable_path=config.FIREFOX_EXECUTABLE)
driver.get('https://www.youtube.com/watch?v=dT5ALH3ICTc')

print(driver.execute_script("return document.getElementById('movie_player').getAvailableQualityLevels()"))