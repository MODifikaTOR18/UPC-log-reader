import json, datetime
import requests
from time import sleep
from selenium import webdriver
from selenium.webdriver import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions

with open('script_info.json', 'r') as file:
    settings = json.load(file)

host = settings['host']
user = settings['login']
secret = settings['secret']
apiToken = settings['token']
chatID = settings['chatID']

written_rows = 0 # Количество записанных в сообщение строк лога
message = f"#UPC лог за последние 30 минут. \n" # Заголовок сообщения
apiURL = f'https://api.telegram.org/bot{apiToken}/sendMessage'

# Задаём настройки браузера Firefox
options = Options()
options.add_argument("--headless")

# Запускаем браузер с заданными настройками
browser = webdriver.Firefox(options=options)
browser.get(host)
wait = WebDriverWait(browser, timeout=10, poll_frequency=2)

# Ищем поля ввода логина и пароля, вводим данные
input_username = wait.until(
    expected_conditions.element_to_be_clickable((By.NAME,'login_username')))
input_username.send_keys(user)

input_password = wait.until(
    expected_conditions.element_to_be_clickable((By.NAME, 'login_password')))
input_password.send_keys(secret + Keys.ENTER)

# Теперь нужно изменить адрес и добавить адрес страницы логов
sleep(3)
new_url = browser.current_url.split('/')
new_url[-1] = 'eventweb.htm'
new_url = '/'.join(new_url)

# После изменения можно переходить по новому адресу
browser.get(new_url)

# Ждём прогрузки страницы
wait.until(
    expected_conditions.element_to_be_clickable((By.LINK_TEXT, 'Next >')))

# В таблице логов получаем все строки, выкидываем строку с заголовками столбцов
table = browser.find_elements(by=By.CLASS_NAME, value='table')
table_rows = table[0].find_elements(by=By.TAG_NAME, value='tr')
table_rows.pop(0)

# Проходимся по строкам и смотрим на их время
for row in table_rows:
    td = row.find_elements(by=By.TAG_NAME, value="td")
    log_time_str = td[0].text[1:] + ' ' + td[1].text
    log_time = datetime.datetime.strptime(log_time_str, '%d.%m.%Y %H:%M:%S')
    curr_time = (datetime.datetime.now() - datetime.timedelta(minutes=30))

    # Если время не старше 5 минут, а текст лога не содержит инфы о входе/выходе, записываем строку
    if curr_time < log_time and ('logged in' not in td[3].text and 'logged out' not in td[3].text):
        message += f"{td[0].text} {td[1].text} {td[3].text}\n"
        written_rows += 1

# Постим полученный лог в телегу, если есть что постить
if written_rows > 0:
    try:
        response = requests.post(apiURL, json={'chat_id': chatID, 'text': message})
    except Exception as e:
        print(e)

print(message)
logoff = browser.find_element(by=By.PARTIAL_LINK_TEXT, value="Log Off")
logoff.click()
browser.close()
