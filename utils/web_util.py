import time

from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chromium.webdriver import ChromiumDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait


def get_driver() -> ChromiumDriver:
    """
    sf chrome 不能更改设置
    download.default_directory：指定下载文件的目录
    profile.default_content_settings.popups：0 为屏蔽弹窗，1 为开启弹窗
    prefs = {'profile.default_content_settings.popups': 0, 'download.default_directory': download_dir}
    options.add_experimental_option('prefs', prefs)
    :return: ChromiumDriver
    """
    options = Options()

    options.add_argument('--disable-blink-features=AutomationControlled')
    server = Service('../chromedriver.exe')
    return webdriver.Chrome(service=server, options=options)


def login_sf(driver: ChromiumDriver, url: str) -> None:
    driver.get(url)
    while True:
        try:
            if driver.find_element(By.XPATH, '//*[@id="qrcodeimg"]'):
                print('请扫码登录')
                time.sleep(2)
        except NoSuchElementException as e:
            print('登录成功')
            break


def wait_download_completed(driver: ChromiumDriver) -> [str]:
    """
    等待全部下载完毕
    :param driver:
    :return:
    """
    current_tab = driver.current_window_handle

    def check_downloads_chrome(web_driver) -> [str]:
        if not web_driver.current_url.startswith("chrome://downloads"):
            # create new tab
            driver.execute_script("window.open()")
            # move to new tab
            new_tab = driver.window_handles[-1]
            driver.switch_to.window(new_tab)
            driver.get('chrome://downloads/')
        # 确认文件下载完成
        return web_driver.execute_script("""
            var items = document.querySelector('downloads-manager').shadowRoot.querySelector('#downloadsList').items;
            if (items.length === 0) {
                return []
            }
            if (items.every(e => e.state === "COMPLETE")) {
                return items.map(e => e.filePath || e.file_url);
            }
            """)

    paths = WebDriverWait(driver, 10, 1).until(check_downloads_chrome)
    print('download files:{}'.format(paths))
    driver.switch_to.window(current_tab)
    return paths
