import time

from telepot import Bot

from selenium import webdriver
from selenium.webdriver import Firefox
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service

from config import *

SLEEP_TIME = 180.0
MSG_REPEAT_TIME = 20

def initialise_driver() -> Firefox:
    options = Options()
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36')
    options.set_preference('dom.webdriver.enabled', False)
    options.set_preference('useAutomationExtension', False)
    options.set_preference('general.useragent.override', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36')

    service = Service(executable_path='/usr/bin/geckodriver')
    driver = webdriver.Firefox(service=service, options=options)
    driver.maximize_window()
    return driver

def initialise_bot() -> Bot:
    return Bot(TELEGRAM_BOT_TOKEN)

def login(driver: Firefox) -> None:
    driver.get('https://visas-ch.tlscontact.com/visa/gb/gbLON2ch/home')
    time.sleep(5.)

    login_button_selector = '#tls-navbar > div > div.tls-navbar--links.-closed.height52 > div.tls-log > div.tls-navbar--slot.tls-navbar-right > a'
    login_button = driver.find_element(By.CSS_SELECTOR, login_button_selector)
    login_button.click()
    time.sleep(5.)

    email_field = driver.find_element(By.CSS_SELECTOR, '#username')
    password_field = driver.find_element(By.CSS_SELECTOR, '#password')

    email_field.send_keys(TLS_USERNAME)
    password_field.send_keys(TLS_PASSWORD)
    time.sleep(1.)

    password_field.send_keys(Keys.ENTER)
    time.sleep(10.)

def refresh_until_have_slot(driver: Firefox) -> None:
    driver.get(f'https://visas-ch.tlscontact.com/appointment/gb/gbLON2ch/{VISA_GRP_NUMBER}')

    while True:
        time.sleep(15.)

        elements = driver.find_elements(By.CSS_SELECTOR, '#app > div.tls-appointment > div.tls-popup-display > div.tls-popup-display--container > div > div > div.tls-popup--body > div:nth-child(2) > div:nth-child(1)')
        if not elements or 'Sorry, there is no available appointment at the moment' not in elements[0].text:
            break

        time.sleep(SLEEP_TIME)
        driver.refresh()

def send_message(bot: Bot, message: str) -> None:
    for _ in range(MSG_REPEAT_TIME):
        bot.sendMessage(TELEGRAM_CHAT_ID, message)
        time.sleep(5.)

def main() -> None:
    driver = initialise_driver()
    bot = initialise_bot()
    try:
        login(driver)
        refresh_until_have_slot(driver)
        send_message(bot, '御瑞西国之査証枠出現')
    except Exception as e:
        send_message(bot, '異常現象出現')
        raise e from None
    finally:
        driver.quit()

if __name__ == '__main__':
    main()
