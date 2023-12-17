import configparser
import textwrap
import traceback

import telegram
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common import NoSuchElementException, TimeoutException
import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

chrome_options = Options()
chrome_options.add_argument("--headless")

password = None
driver = None
is_local = False
traffic_limit = 400  # Gb


def auth():
    wait = WebDriverWait(driver, 10)
    driver.get("http://192.168.1.1/")
    assert "No results found." not in driver.page_source

    wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="pc-login-password"]')))

    password_input = driver.find_element(By.XPATH, '//*[@id="pc-login-password"]')
    password_input.send_keys(password)

    login_button = driver.find_element(By.XPATH, '//*[@id="pc-login-btn"]')
    login_button.click()

    time.sleep(5)
    try:
        confirm_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="confirm-yes"]')))
        confirm_button.click()
    except (NoSuchElementException, TimeoutException):
        return


def get_traffic_limit():
    wait = WebDriverWait(driver, 10)
    button_advanced_settings = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="advanced"]/span[2]')))
    button_advanced_settings.click()

    time.sleep(5)
    button_internet = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="menuTree"]/li[3]/a')))
    button_internet.click()

    button_traffic = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="menuTree"]/li[3]/ul/li[4]/a')))
    button_traffic.click()
    traffic_field = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="tu_traffic_disInput"]')))

    return traffic_field.text


def logout():
    wait = WebDriverWait(driver, 10)

    button_exit = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="topLogout"]')))
    button_exit.click()

    button_yes = wait.until(
        EC.element_to_be_clickable((By.XPATH, '//*[@id="alert-container"]/div/div[4]/div/div[2]/div/div[2]/button')))
    button_yes.click()


def progress_string(percentage):
    total_steps = 20
    steps = int(percentage / 100 * total_steps)
    res = '['
    res += '\u25A0' * steps
    res += '\u25A1' * (total_steps - steps)
    res += ']'
    return res


if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read('./config.ini') if is_local else config.read('/config.ini')
    telegram_token = config.get('telegram', 'token')
    telegram_chat = config.get('telegram', 'chat')
    password = config.get('dlink', 'password')
    try:
        driver = webdriver.Remote(
            command_executor='http://localhost:4444/wd/hub' if is_local else 'http://selenium-grid:4444/wd/hub',
            options=chrome_options
        )
        driver.implicitly_wait(1)
        auth()
        traffic = get_traffic_limit()
        print(traffic)
        logout()

        traffic = float(traffic.split(' ')[0])
        perc = int(traffic / traffic_limit * 100)

        message = f"""
        Used {traffic} of {traffic_limit} GB
        {progress_string(perc)}
        """
        message = textwrap.dedent(message).lstrip()
        print(message)

        bot = telegram.Bot(token=telegram_token)
        bot.send_message(chat_id=telegram_chat, text=message)

    except Exception as e:
        print('Error:')
        print(e)
        traceback.print_exc()
    finally:
        if driver is not None:
            driver.close()
            driver.quit()
