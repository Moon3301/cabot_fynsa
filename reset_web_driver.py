from flask import Flask
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

app = Flask(__name__)

# Abre la página web proporcionada
url_VMware = 'https://cloud.acbingenieria.cl/provider'

@app.route("/")
def main():

    try:

        #
        chrome_options = webdriver.ChromeOptions()
        
        #
        chrome_options.accept_insecure_certs = True
        chrome_options.add_argument("--enable-chrome-browser-cloud-management")
        chrome_options.add_argument("--start-maximized")
        
        #
        driver = webdriver.Chrome(options=chrome_options)

        #
        driver.get(url_VMware)

        #
        credentials_user = driver.find_element(By.ID, "usernameInput")
        credentials_pass = driver.find_element(By.ID, "passwordInput")
        btn_click_autenticate = driver.find_element(By.ID, "loginButton")

        #
        credentials_user.clear()
        credentials_user.send_keys("cacevedo")
        time.sleep(1)

        #
        credentials_pass.clear()
        credentials_pass.send_keys("Acb2k24*")
        time.sleep(1)

        #
        btn_click_autenticate.click()
        time.sleep(5)

        #
        #screen_index = driver.find_element(By.XPATH, "/html/body/vcd-app-container/vcd-app/clr-main-container")

        #
        WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.XPATH, "/html/body/vcd-app-container/vcd-app/clr-main-container/div[2]/main/vcd-loading-indicator/ng-component/clr-vertical-nav/div/a[6]"))
        )

        #
        btn_gateway1 = driver.find_element(By.XPATH, "/html/body/vcd-app-container/vcd-app/clr-main-container/div[2]/main/vcd-loading-indicator/ng-component/clr-vertical-nav/div/a[6]")
        btn_gateway1.click()
        time.sleep(5)

        #
        btn_fynsa = driver.find_element(By.XPATH, "/html/body/vcd-app-container/vcd-app/clr-main-container/div[2]/main/vcd-loading-indicator/ng-component/div/vcd-edge-gateways/clr-datagrid/div[1]/div/div/div/div/clr-dg-row[7]/div/div[2]/div/clr-dg-cell[1]/a")
    

        btn_fynsa.click()
        time.sleep(5)

        #
        btn_servicios = driver.find_element(By.XPATH, "/html/body/vcd-app-container/vcd-app/clr-main-container/div[2]/main/vcd-loading-indicator/ng-component/div/ng-component/div/vcd-entity-details-container/div/vcd-action-menu/div/button[2]")
        btn_servicios.click()
        time.sleep(5)

        #
        ifram_locator = driver.find_element(By.XPATH, "/html/body/vcd-app-container/vcd-app/clr-main-container/div[2]/main/vcd-loading-indicator/ng-component/div/ng-component/vcd-dynamic-content-modal/clr-modal/div/div[1]/div[2]/div/div[2]/iframe")
        WebDriverWait(driver, 20).until(EC.frame_to_be_available_and_switch_to_it(ifram_locator))

        #
        btn_vpn = driver.find_element(By.XPATH, "/html/body/vcd-app/div/div[2]/div/vcd-network-edge-tabset/vcd-tabset/ul/li[6]/a")
        btn_vpn.click()
        time.sleep(5)

        #
        btn_sitios_Ipsec = driver.find_element(By.XPATH, """ //*[@id="sitesTab"]/a """)
        btn_sitios_Ipsec.click()
        time.sleep(5)

        #
        btn_opc_pretorian = driver.find_element(By.XPATH, "/html/body/vcd-app/div/div[2]/div/vcd-network-edge-tabset/vcd-tabset/vcd-vpn-tabset/vcd-tabset/vcd-vpn-ipsec/vcd-vpn-ipsec-sites/div[2]/wj-flex-grid/div[1]/div[2]/div[1]/div[1]")
        btn_opc_pretorian.click()
        time.sleep(1)

        btn_edit_IPsec = driver.find_element(By.XPATH, "/html/body/vcd-app/div/div[2]/div/vcd-network-edge-tabset/vcd-tabset/vcd-vpn-tabset/vcd-tabset/vcd-vpn-ipsec/vcd-vpn-ipsec-sites/div[1]/button[2]")
        btn_edit_IPsec.click()
        time.sleep(2)

        #
        btn_check_disabled = driver.find_element(By.XPATH, "/html/body/vcd-app/div/div[2]/div/vcd-network-edge-tabset/vcd-tabset/vcd-vpn-tabset/vcd-tabset/vcd-vpn-ipsec/vcd-vpn-ipsec-sites/div[2]/vcd-collection-form-modal/vcd-ok-cancel-modal/clr-modal/div/div[1]/div/div[2]/vcd-vpn-ipsec-site-form/form/vcd-form-checkbox[1]/div/div")
        btn_check_disabled.click()
        time.sleep(3)

        #
        btn_save = driver.find_element(By.XPATH, "/html/body/vcd-app/div/div[2]/div/vcd-network-edge-tabset/vcd-tabset/vcd-vpn-tabset/vcd-tabset/vcd-vpn-ipsec/vcd-vpn-ipsec-sites/div[2]/vcd-collection-form-modal/vcd-ok-cancel-modal/clr-modal/div/div[1]/div/div[3]/button[2]")
        btn_save.click()
        time.sleep(3)

        #
        btn_change_save = driver.find_element(By.CLASS_NAME, "alert-save")
        
        btn_change_save.click()
        time.sleep(10)

        #
        btn_edit_IPsec.click()
        time.sleep(3)

        #
        btn_check_disabled.click()
        time.sleep(3)

        #
        btn_save.click()
        time.sleep(3)

        #
        btn_discard_changes = driver.find_element(By.CLASS_NAME, "alert-save")
        btn_discard_changes.click()

        #btn_change_save.click()

        time.sleep(3)


        # Realiza acciones en la página (puedes agregar más interacciones según tus necesidades)
        # Por ejemplo, puedes imprimir el título de la página
        print("Tarea realizada con exito ! ")

        time.sleep(3)

        

        return f'Título de la página: {driver.title}'

    except Exception as e:

        print(f"Error: {e}")
    
if __name__ == '__main__':
    app.run()
