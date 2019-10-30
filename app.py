import os
import sys

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options  
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.select import Select


import time

import logging

logging.basicConfig(level=logging.INFO)
_LOGGER = logging.getLogger()

class JHStress():
    def __init__(self):
        self.load_config()
        chrome_options = Options()  
        if self.headless:
            chrome_options.add_argument("--headless")
        self.driver = webdriver.Chrome(chrome_options=chrome_options)
        self.driver.get(self.url)
        self.action = ActionChains(self.driver)
        _LOGGER.info("Config loaded, driver initialized")

    def load_config(self):

        self.url = os.environ.get('JH_URL')
        self.username = os.environ.get('JH_LOGIN_USER')
        self.password = os.environ.get('JH_LOGIN_PASS')
        self.notebooks = os.environ.get('JH_NOTEBOOKS', "").split(",")
        self.user_name = os.environ.get('JH_USER_NAME', 'test-user1')
        self.spawner = {
            "image": os.environ.get('JH_NOTEBOOK_IMAGE', "s2i-minimal-notebook:3.6"),
            "size": os.environ.get('JH_NOTEBOOK_SIZE', "None"),
        }
        self.as_admin = os.environ.get('JH_AS_ADMIN', False)
        self.headless = os.environ.get('JH_HEADLESS', False)


        if not self.url:
            _LOGGER.error("You need to provide $JH_URL env var.")
            raise Exception("You need to provide $JH_URL env var.")

    def click_menu(self, button):
        cell_elem = self.driver.find_element(By.XPATH, '//a[text()="%s"]' % button)
        cell_elem.click()

    def openshift_login(self, username, password):
        username_elem = self.driver.find_element_by_id("inputUsername")
        username_elem.send_keys(username)
        password_elem = self.driver.find_element_by_id("inputPassword")
        password_elem.send_keys(password)
        login_elem = self.driver.find_element(By.XPATH, '//button[text()="Log In"]')
        login_elem.send_keys(Keys.RETURN)

    def admin_add_user(self):
        admin_elem = self.driver.find_element_by_link_text("Admin")
        admin_elem.click()
        _LOGGER.info("Admin console")

        user_elem = None
        try:
            user_elem = self.driver.find_element(By.XPATH, '//tr[@data-user="%s"]' % self.user_name)
        except:
            pass

        if user_elem:
            _LOGGER.info("User %s exists, cleaning up" % self.user_name)
            self.admin_del_user()

        _LOGGER.info("User %s does not exist" % self.user_name)
        textarea_visible = False
        retry = 0
        while not textarea_visible and retry < 3:
            add_user_elem = self.driver.find_element(By.ID, "add-users")
            add_user_elem.click()

            try:
                w = WebDriverWait(self.driver, 1)
                user_input_elem = w.until(EC.visibility_of_element_located((By.XPATH, '//textarea[@class="form-control username-input"]')))
            except Exception as ex:
                retry += 1
                continue
            textarea_visible = True

        user_input_elem.clear()
        user_input_elem.send_keys(self.user_name)

        save_users_elem = self.driver.find_element(By.XPATH, '//button[text()="Add Users"]')
        save_users_elem.click()
            

        w = WebDriverWait(self.driver, 5)
        start_elem = w.until(EC.element_to_be_clickable((By.XPATH, '//a[@href="/hub/spawn/%s"]' % self.user_name)))
        start_elem.click()

    def admin_del_user(self):
        self.driver.get(self.url+ "/hub/home")
        admin_elem = self.driver.find_element_by_link_text("Admin")
        admin_elem.click()

        try:
            w = WebDriverWait(self.driver, 5)
            stop_elem = w.until(EC.element_to_be_clickable((By.XPATH, '//tr[@data-user="%s"]//a[text()="stop server"]' % self.user_name)))
            stop_elem.click()
        except:
            pass
        
        w = WebDriverWait(self.driver, 50)
        start_elem = w.until(EC.element_to_be_clickable((By.XPATH, '//a[@href="/hub/spawn/%s"]' % self.user_name)))

        del_elem = w.until(EC.element_to_be_clickable((By.XPATH, '//tr[@data-user="%s"]//a[text()="delete"]' % self.user_name)))
        del_elem.click()

        confirm_del_elem  = w.until(EC.element_to_be_clickable((By.XPATH, '//button[text()="Delete User"]')))
        confirm_del_elem.click()

    def run(self):
        self.login()
        _LOGGER.info("Logged in")
        if self.as_admin:
            self.admin_add_user()
            _LOGGER.info("Added user %s as admin" % self.user_name)
        self.spawn()
        _LOGGER.info("Spawned the server")
        tab = self.driver.window_handles[0]

        for notebook in self.notebooks:
            self.run_notebook(notebook, tab)
            _LOGGER.info("Notebook %s finished" % notebook)
        if self.as_admin:
            self.admin_del_user()
            _LOGGER.info("Deleted user %s" % self.user_name)
        else:
            self.stop()
            _LOGGER.info("Stopped the server")

    def login(self):
        elem = self.driver.find_element_by_link_text("Sign in with OpenShift")
        elem.send_keys(Keys.RETURN)

        self.openshift_login(self.username, self.password)
    
    def spawn(self):
        image_select = Select(self.driver.find_element(By.XPATH, '//select[@name="custom_image"]'))
        image_select.select_by_value(self.spawner["image"])

        size_select = Select(self.driver.find_element(By.XPATH, '//select[@name="size"]'))
        size_select.select_by_value(self.spawner["size"])

        spawn_elem = self.driver.find_element(By.XPATH, '//input[@value="Spawn"]')
        spawn_elem.click()

        w = WebDriverWait(self.driver, 120)
        element = w.until(EC.presence_of_element_located((By.ID, 'notebook_list_header')))
    
    def stop(self):
        self.driver.get(self.url+ "/hub/home")
        stop_elem = self.driver.find_element_by_id("stop")
        stop_elem.click()

    def run_notebook(self, notebook, tab):
        try:
            w = WebDriverWait(self.driver, 10)
            element = w.until(EC.presence_of_element_located((By.XPATH, '//span[text()="%s"]' % notebook)))
        except Exception as e:
            _LOGGER.error(e)

        notebook_elem = self.driver.find_element(By.XPATH, '//span[text()="%s"]' % notebook)
        notebook_elem.click()

        #Switch to new tab
        self.driver.switch_to_window(self.driver.window_handles[1])

        self.run_all_cells()
        self.driver.close()
        self.driver.switch_to_window(tab)

    def run_all_cells(self):
        try:
            w = WebDriverWait(self.driver, 20)
            element = w.until(EC.presence_of_element_located((By.XPATH, '//i[@id="kernel_indicator_icon"][@title="Kernel Idle"]')))
        except Exception as e:
            _LOGGER.error(e)
            raise e

        wait = WebDriverWait(self.driver, 10)
        elem = wait.until(EC.element_to_be_clickable((By.XPATH, '//a[text()="Cell"]')))

        self.click_menu("Cell")
        elem = self.driver.find_element_by_id("all_outputs")
        self.driver.execute_script("arguments[0].setAttribute('class','dropdown-submenu open')", elem)

        clear_elem = self.driver.find_element_by_id("clear_all_output")
        clear_elem.click()


        self.click_menu("Cell")
        self.click_menu("Run All")

        end_of_notebook = "End Of Notebook"

        wait = WebDriverWait(self.driver, 60)
        end_elem = wait.until(EC.presence_of_element_located((By.XPATH, '//pre[contains(text(), "%s")]' % end_of_notebook)))
        _LOGGER.info("Reached a cell with content %s" % end_of_notebook)

    def quit(self):
        self.driver.quit()


if __name__ == "__main__":
    jhs = JHStress()
    jhs.run()
    jhs.quit()

    #jhs.login()
    #jhs.run_all_cells()
    jhs.quit()

#print(driver.page_source)

    