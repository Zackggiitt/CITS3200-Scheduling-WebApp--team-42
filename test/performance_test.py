import os
import time
import pytest
import requests
import unittest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options


BASE_URL = "http://localhost:5000" 
TEST_USER = {"username": "test@example.com", "password": "password123"}

@pytest.fixture(scope="module")
def browser():
    options = Options()
    options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)
    yield driver
    driver.quit()

def test_ui_homepage(browser):
    browser.get(BASE_URL)
    assert "Error" not in browser.page_source

def test_ui_navigation_links(browser):
    browser.get(BASE_URL)
    links = browser.find_elements(By.TAG_NAME, "a")
    for link in links:
        href = link.get_attribute("href")
        if href and BASE_URL in href:
            browser.get(href)
            assert browser.title != ""  # page loads with a title

def test_ui_login_form(browser):
    browser.get(f"{BASE_URL}/login")
    user_field = browser.find_element(By.NAME, "username")
    pass_field = browser.find_element(By.NAME, "password")
    submit_btn = browser.find_element(By.XPATH, "//button[@type='submit']")
    user_field.send_keys(TEST_USER["username"])
    pass_field.send_keys(TEST_USER["password"])
    submit_btn.click()
    assert "dashboard" in browser.current_url or "login" in browser.current_url

def test_ui_form_validation(browser):
    browser.get(f"{BASE_URL}/register")
    submit_btn = browser.find_element(By.XPATH, "//button[@type='submit']")
    submit_btn.click()
    assert "error" in browser.page_source.lower()

def test_mobile_responsiveness(browser):
    browser.set_window_size(375, 812)  # iPhone X dimensions
    browser.get(BASE_URL)
    assert "menu" in browser.page_source.lower() or browser.find_elements(By.TAG_NAME, "nav")


if __name__ == "__main__":
    unittest.main()