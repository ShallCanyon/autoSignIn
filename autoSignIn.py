from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from PIL import Image
import tesserocr
import os
from configparser import ConfigParser as CP

baseUrl = 'http://yq.gzhu.edu.cn/taskcenter/workflow/index'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/88.0.4324.104 Safari/537.36',
}
driver = webdriver.Chrome()
driver.get(baseUrl)
Wait = WebDriverWait(driver, 10)
screenshot = './screenshot.png'
captchaScreenshot = './captcha.png'


def login():
    try:
        cfg = CP()
        cfg.read('config.ini')
        userData = {
            'name': cfg.get('userdata', 'username'),
            'pw': cfg.get('userdata', 'userpassword')
        }

        nameInput = Wait.until(
            EC.presence_of_element_located((By.ID, 'username')))
        pwInput = Wait.until(
            EC.presence_of_element_located((By.ID, 'password'))
        )
        captchaIMG = Wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '#fm1 > div:nth-child(3) > img'))
        )
        '''imgUrl = captchaIMG.get_attribute('src')
        # imgUrl = ''.join([baseUrl, imgUrl])
        print(imgUrl)'''

        # 使用url访问captcha图片会随机，必须自动截取坐标
        locations = {
            'left': captchaIMG.location['x'],
            'top': captchaIMG.location['y'],
            'right': captchaIMG.location['x'] + captchaIMG.size['width'],
            'bottom': captchaIMG.location['y'] + captchaIMG.size['height']
        }
        driver.save_screenshot(screenshot)
        captchaResult = getCaptcha(screenshot, locations)
        os.remove(screenshot)
        # print(captchaResult)

        captchaInput = Wait.until(
            EC.presence_of_element_located((By.ID, 'captcha'))
        )
        submit = Wait.until(
            EC.element_to_be_clickable((By.CLASS_NAME, 'btn-submit'))
        )

        nameInput.send_keys(userData.get('name'))
        pwInput.send_keys(userData.get('pw'))
        captchaInput.send_keys(captchaResult)
        submit.click()
        return driver.get_cookies()
    except TimeoutException:
        driver.refresh()
        return login()


def getCaptcha(imgUrl, locations, threshold=127):
    # res = requests.get(imgUrl)
    # image = Image.open(BytesIO(res.content))
    if threshold > 255:
        return None
    print(threshold)
    rawimg = Image.open(imgUrl)
    rawimg.crop(
        (locations.get('left'),
         locations.get('top'),
         locations.get('right'),
         locations.get('bottom'))).save(captchaScreenshot)
    image = Image.open(captchaScreenshot)
    # image.show()
    image = image.convert('L')  # 灰度
    # 二值化
    # image = image.convert('1')
    table = []
    for i in range(256):
        if i < threshold:
            table.append(0)
        else:
            table.append(1)
    image = image.point(table, '1')

    result = tesserocr.image_to_text(image).strip()
    os.remove(captchaScreenshot)
    if len(result) != 4 or result.isdigit() is False:
        return getCaptcha(imgUrl, locations, threshold + 8)
    else:
        return result


def signIn():
    try:
        enterBtn = Wait.until(
            EC.element_to_be_clickable((By.XPATH, '/html/body/div[1]/div[3]/div[2]/div[3]/div[1]/ul/li['
                                                  '1]/div[1]/a[1]')))
        enterBtn.click()
        # 切换到新标签
        handles = driver.window_handles
        driver.switch_to.window(handles[1])

        # driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        signInBtn = Wait.until(EC.element_to_be_clickable((By.ID, 'preview_start_button')))
        signInBtn.click()
        checkbox = Wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="V1_CTRL82"]')))
        checkbox.click()
        submitBtn = Wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="form_command_bar"]/li[1]')))
        submitBtn.click()
    except TimeoutException:
        print("TimeOut")


if __name__ == '__main__':
    cookies = {}
    # print(driver.get_cookies())
    # print(len(driver.get_cookies()))
    if len(driver.get_cookies()) < 2:
        cookies = login()
        # print(cookies)
        # print(len(cookies))
    signIn()
