# core/selenium_manager.py
"""
Менеджер для управления Selenium браузером с улучшенными функциями.
Включает поддержку кук, прокси, кастомных заголовков и более сложных сценариев.
"""
import os
import json
import time
from typing import Optional, List, Dict, Tuple
from urllib.parse import urlparse

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException


class SeleniumManager:
    """Менеджер для работы с Selenium браузерами."""
    
    SUPPORTED_BROWSERS = ['chrome', 'firefox', 'edge']
    
    def __init__(
        self,
        browser: str = 'chrome',
        headless: bool = True,
        proxy: Optional[str] = None,
        cookies_path: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """
        Args:
            browser: Браузер ('chrome', 'firefox', 'edge')
            headless: Запустить в режиме headless
            proxy: Прокси сервер (например, '127.0.0.1:8080')
            cookies_path: Путь к файлу с куками
            user_agent: Кастомный User-Agent
        """
        self.browser = browser.lower()
        self.headless = headless
        self.proxy = proxy
        self.cookies_path = cookies_path
        self.user_agent = user_agent or self._default_user_agent()
        self.driver = None
    
    @staticmethod
    def _default_user_agent() -> str:
        """Возвращает User-Agent по умолчанию."""
        return (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
            '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
    
    def _create_chrome_options(self) -> ChromeOptions:
        """Создаёт опции для Chrome."""
        options = ChromeOptions()
        
        if self.headless:
            options.add_argument('--headless=new')
        
        # Базовые аргументы
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument(f'user-agent={self.user_agent}')
        
        # Прокси
        if self.proxy:
            options.add_argument(f'--proxy-server={self.proxy}')
        
        # Отключаем автоматизацию
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        return options
    
    def _create_firefox_options(self) -> FirefoxOptions:
        """Создаёт опции для Firefox."""
        options = FirefoxOptions()
        
        if self.headless:
            options.add_argument('--headless')
        
        # User-Agent
        if self.user_agent:
            options.set_preference('general.useragent.override', self.user_agent)
        
        # Прокси
        if self.proxy:
            host, port = self.proxy.split(':')
            options.set_preference('network.proxy.type', 1)  # Manual
            options.set_preference('network.proxy.http', host)
            options.set_preference('network.proxy.http_port', int(port))
        
        return options
    
    def init_driver(self) -> bool:
        """
        Инициализирует WebDriver.
        
        Returns:
            True если успешно, False если ошибка
        """
        try:
            if self.browser == 'chrome':
                options = self._create_chrome_options()
                self.driver = webdriver.Chrome(options=options)
            
            elif self.browser == 'firefox':
                options = self._create_firefox_options()
                self.driver = webdriver.Firefox(options=options)
            
            elif self.browser == 'edge':
                options = ChromeOptions()  # Edge использует Chromium
                if self.headless:
                    options.add_argument('--headless')
                options.add_argument(f'user-agent={self.user_agent}')
                self.driver = webdriver.Edge(options=options)
            
            else:
                print(f"❌ Неподдерживаемый браузер: {self.browser}")
                return False
            
            # Загружаем куки если они есть
            if self.cookies_path and os.path.exists(self.cookies_path):
                self._load_cookies(self.cookies_path)
            
            return True
        
        except Exception as e:
            print(f"❌ Ошибка инициализации браузера: {e}")
            return False
    
    def _load_cookies(self, cookies_path: str):
        """Загружает куки в браузер."""
        try:
            # Сначала переходим на страницу, чтобы можно было установить куки
            self.driver.get('about:blank')
            
            with open(cookies_path, 'r') as f:
                cookies = json.load(f)
            
            for cookie in cookies:
                try:
                    self.driver.add_cookie(cookie)
                except Exception as e:
                    print(f"⚠️ Ошибка при загрузке кука: {e}")
        
        except Exception as e:
            print(f"⚠️ Ошибка загрузки файла кук: {e}")
    
    def _save_cookies(self, cookies_path: str):
        """Сохраняет куки из браузера в файл."""
        try:
            with open(cookies_path, 'w') as f:
                json.dump(self.driver.get_cookies(), f, indent=2)
            print(f"✅ Куки сохранены в {cookies_path}")
        except Exception as e:
            print(f"⚠️ Ошибка при сохранении кук: {e}")
    
    def get(self, url: str, timeout: int = 30) -> bool:
        """
        Переходит на URL с ожиданием загрузки.
        
        Returns:
            True если успешно, False если ошибка
        """
        if not self.driver:
            return False
        
        try:
            self.driver.get(url)
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_all_elements_located((By.TAG_NAME, "body"))
            )
            time.sleep(2)  # Ждём JS контента
            return True
        except TimeoutException:
            print(f"⏱️ Таймаут загрузки: {url}")
            return False
        except WebDriverException as e:
            print(f"❌ Ошибка WebDriver: {e}")
            return False
    
    def wait_for_element(
        self,
        selector: str,
        by: By = By.CSS_SELECTOR,
        timeout: int = 10
    ) -> bool:
        """Ждёт появления элемента."""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, selector))
            )
            return True
        except TimeoutException:
            print(f"⏱️ Элемент не найден по селектору: {selector}")
            return False
    
    def find_elements(
        self,
        selector: str,
        by: By = By.CSS_SELECTOR
    ) -> List:
        """Находит элементы."""
        if not self.driver:
            return []
        try:
            return self.driver.find_elements(by, selector)
        except:
            return []
    
    def execute_script(self, script: str) -> any:
        """Выполняет JavaScript."""
        if not self.driver:
            return None
        try:
            return self.driver.execute_script(script)
        except Exception as e:
            print(f"⚠️ Ошибка при выполнении скрипта: {e}")
            return None
    
    def scroll_to_bottom(self):
        """Скроллит страницу до конца (для подгрузки динамического контента)."""
        if not self.driver:
            return
        
        try:
            self.driver.execute_script(
                "window.scrollTo(0, document.body.scrollHeight);"
            )
            time.sleep(2)
        except:
            pass
    
    def get_page_source(self) -> str:
        """Возвращает исходный HTML текущей страницы."""
        if not self.driver:
            return ""
        return self.driver.page_source
    
    def get_window_title(self) -> str:
        """Возвращает заголовок окна."""
        if not self.driver:
            return ""
        return self.driver.title
    
    def close(self):
        """Закрывает браузер."""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None
    
    def __enter__(self):
        """Context manager support."""
        self.init_driver()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager support."""
        self.close()


class BrowserCookieExtractor:
    """
    Извлекает куки из системного браузера для использования в Selenium.
    """
    
    @staticmethod
    def export_chrome_cookies(output_path: str) -> bool:
        """
        Экспортирует куки из Chrome.
        Требует, чтобы Chrome был закрыт.
        """
        try:
            from browser_cookie3 import chrome
            cookies = chrome()
            
            cookies_list = []
            for cookie in cookies:
                cookies_list.append({
                    'name': cookie.name,
                    'value': cookie.value,
                    'domain': cookie.domain,
                    'path': cookie.path,
                    'secure': cookie.secure,
                    'httpOnly': cookie.has_nonstandard_attr('HttpOnly')
                })
            
            with open(output_path, 'w') as f:
                json.dump(cookies_list, f, indent=2)
            
            print(f"✅ Куки Chrome экспортированы в {output_path}")
            return True
        
        except ImportError:
            print("⚠️ Установите 'browser-cookie3' для экспорта кук:")
            print("  pip install browser-cookie3")
            return False
        except Exception as e:
            print(f"❌ Ошибка экспорта кук: {e}")
            return False
