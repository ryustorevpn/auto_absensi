import os
import time
import configparser
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

app = Flask(__name__)

# Membaca konfigurasi
config = configparser.ConfigParser()
config.read('configtest.cfg')

USERNAME = config['credentials']['username']
PASSWORD = config['credentials']['password']
LOGIN_URL = config['urls']['login_url']
URL_ABSENSI = config['urls']['absensi_url']

# Konfigurasi Selenium
chrome_options = Options()
chrome_options.add_argument("--window-size=1920x1080")
chrome_options.add_argument("--log-level=3")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")

def login_to_lms(driver):
    try:
        driver.get(LOGIN_URL)
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, 'username')))
        driver.find_element(By.ID, 'username').send_keys(USERNAME)
        driver.find_element(By.ID, 'password').send_keys(PASSWORD)
        driver.find_element(By.ID, 'password').send_keys(Keys.RETURN)
        time.sleep(5)
        return True
    except Exception as e:
        print(f"Error saat login: {e}")
        driver.quit()

def find_and_open_absensi(driver):
    try:
        driver.get(URL_ABSENSI)
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//table[contains(@class, 'generaltable')]"))
        )

        rows = driver.find_elements(By.XPATH, "//table[contains(@class, 'generaltable')]//tr")
        today_date = datetime.today().strftime("%a %d %b %Y")

        for row in rows:
            cells = row.find_elements(By.TAG_NAME, 'td')
            if len(cells) > 0:
                date_cell = cells[0].text.strip()

                # Cek apakah tanggal cocok
                if today_date in date_cell:
                    print(f"Tanggal Hari Ini: {today_date}")
                    print("Status: Tanggal Ditemukan, Mencari Link...")

                    # Cari link yang mengandung kata kunci 'view.php?id='
                    links = row.find_elements(By.TAG_NAME, "a")
                    for link in links:
                        href = link.get_attribute("href")
                        if href and "view.php?id=" in href:
                            print(f"Link Absensi Ditemukan: {href}")
                            link.click()
                            print("Link berhasil diklik, membuka halaman absensi...")
                            return True

                    print("Link absensi tidak ditemukan di baris ini.\n")
                    return False

        print("Absensi tidak ditemukan untuk hari ini.\n")
        return False

    except Exception as e:
        print(f"Error saat mencari link absensi: {e}")
        return False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    # Ambil data login dari form
    username = request.form['username']
    password = request.form['password']

    # Setup WebDriver
    driver = webdriver.Chrome(options=chrome_options)

    if login_to_lms(driver):
        message = find_and_open_absensi(driver)
        driver.quit()
        return jsonify(message=message)
    else:
        driver.quit()
        return jsonify(message="Login gagal.")

if __name__ == "__main__":
    app.run(debug=True)
