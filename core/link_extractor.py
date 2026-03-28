# core/link_extractor.py
"""
Модуль для извлечения видеоссылок с использованием Selenium.
Поддерживает скрытые элементы, редиректы, кнопки загрузки.
"""
import os
import time
import requests
from typing import List, Dict, Optional, Tuple
from urllib.parse import urlparse, parse_qs
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.common.exceptions import (
    TimeoutException, 
    NoSuchElementException, 
    WebDriverException
)


class LinkExtractor:
    """
    Извлекает видеоссылки со страниц, включая скрытые элементы.
    Поддерживает: прямые ссылки, кнопки загрузки, редиректы, скрытые видео.
    """
    
    # Расширения видеофайлов
    VIDEO_EXTENSIONS = {
        '.mp4', '.webm', '.mkv', '.avi', '.mov', '.flv', '.wmv', '.m4v',
        '.3gp', '.ogv', '.ts', '.m3u8', '.mpd'
    }
    
    # Селекторы для поиска видеоссылок
    COMMON_VIDEO_SELECTORS = [
        'video > source',  # HTML5 video
        'a[href*="video"]',
        'a[href*="download"]',
        'a[href*="mp4"]',
        'a[href*="webm"]',
        'a[href*="mkv"]',
        'a[href*="stream"]',
        'a[data-src*="video"]',
        'a[data-href*="video"]',
        '[data-video-url]',
        '[data-video-src]',
        '.video-link',
        '.download-link',
    ]
    
    DOWNLOAD_BUTTON_SELECTORS = [
        'button:contains("Скачать")',
        'a:contains("Скачать")',
        'button[class*="download"]',
        'a[class*="download"]',
        'button[class*="Download"]',
        'a[class*="Download"]',
        'button[aria-label*="download"]',
        'a[aria-label*="download"]',
    ]
    
    def __init__(self, headless: bool = True, timeout: int = 30):
        """
        Инициализация экстрактора ссылок.
        
        Args:
            headless: Запустить браузер в режиме headless
            timeout: Таймаут ожидания элементов в секундах
        """
        self.headless = headless
        self.timeout = timeout
        self.driver = None
        self.session = requests.Session()
        
    def _init_driver(self) -> Optional[webdriver.Chrome]:
        """Инициализирует Selenium WebDriver для Chrome."""
        try:
            options = ChromeOptions()
            if self.headless:
                options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            # User-Agent для избежания блокировки
            options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            
            driver = webdriver.Chrome(options=options)
            return driver
        except Exception as e:
            print(f"❌ Ошибка инициализации Selenium: {e}")
            return None
    
    def _extract_video_from_attributes(self, element) -> Optional[str]:
        """Извлекает видеоссылку из атрибутов элемента."""
        try:
            # Проверяем различные атрибуты с видеоссылками
            attrs = ['src', 'href', 'data-src', 'data-href', 'data-video-url', 'data-video-src']
            for attr in attrs:
                url = element.get_attribute(attr)
                if url and self._is_video_url(url):
                    return url
        except:
            pass
        return None
    
    def _is_video_url(self, url: str) -> bool:
        """Проверяет, является ли URL видеофайлом."""
        if not url:
            return False
        
        url_lower = url.lower()
        
        # Проверяем расширение
        for ext in self.VIDEO_EXTENSIONS:
            if ext in url_lower:
                return True
        
        # Проверяем известные видеосервисы
        video_services = [
            'youtube.com', 'youtu.be', 'vimeo.com', 'dailymotion.com',
            'twitch.tv', 'facebook.com/video', 'instagram.com', 'tiktok.com',
            'dropbox.com', 'drive.google.com', 'cdn.', 'video.'
        ]
        
        for service in video_services:
            if service in url_lower:
                return True
        
        return False
    
    def _get_redirect_url(self, url: str) -> Optional[str]:
        """
        Получает финальный URL после редиректов.
        Полезно для кнопок загрузки, которые редиректят на видео.
        """
        try:
            response = self.session.head(
                url,
                allow_redirects=True,
                timeout=10,
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            )
            
            final_url = response.url
            if self._is_video_url(final_url):
                return final_url
                
        except Exception as e:
            print(f"⚠️ Ошибка проверки редиректа {url}: {e}")
        
        return None
    
    def _find_download_buttons(self) -> List[str]:
        """
        Находит и нажимает кнопки загрузки, возвращает полученные ссылки.
        """
        links = []
        
        if not self.driver:
            return links
        
        try:
            # Ищем кнопки по текстам и классам
            potential_buttons = self.driver.find_elements(
                By.XPATH, 
                "//button | //a[contains(translate(@class, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'download')]"
            )
            
            for button in potential_buttons:
                try:
                    # Проверяем текст кнопки
                    button_text = button.text.lower()
                    if any(word in button_text for word in ['скачать', 'download', 'dl', 'get']):
                        href = button.get_attribute('href')
                        
                        if href:
                            # Проверяем прямую ссылку
                            if self._is_video_url(href):
                                links.append(href)
                            else:
                                # Проверяем редирект
                                redirect_url = self._get_redirect_url(href)
                                if redirect_url:
                                    links.append(redirect_url)
                except:
                    continue
            
        except Exception as e:
            print(f"⚠️ Ошибка поиска кнопок загрузки: {e}")
        
        return links
    
    def _find_hidden_videos(self) -> List[str]:
        """
        Находит видео, скрытые другими элементами, через JavaScript injection.
        """
        links = []
        
        if not self.driver:
            return links
        
        try:
            # Script для поиска всех видеоссылок в DOM, даже скрытых
            script = """
            let videos = [];
            
            // Поиск в HTML5 video элементах
            document.querySelectorAll('video source').forEach(src => {
                let url = src.src || src.getAttribute('data-src');
                if (url) videos.push(url);
            });
            
            // Поиск в атрибутах data-*
            document.querySelectorAll('[data-video-url], [data-video-src], [data-src*="video"]').forEach(el => {
                let url = el.getAttribute('data-video-url') || 
                          el.getAttribute('data-video-src') || 
                          el.getAttribute('data-src');
                if (url) videos.push(url);
            });
            
            // Поиск в iframe src
            document.querySelectorAll('iframe').forEach(iframe => {
                let src = iframe.src;
                if (src && (src.includes('video') || src.includes('youtube') || src.includes('vimeo'))) {
                    videos.push(src);
                }
            });
            
            // Поиск в скрытых ссылках
            document.querySelectorAll('a[href*="mp4"], a[href*="webm"], a[href*="video"]').forEach(link => {
                let url = link.href;
                if (url) videos.push(url);
            });
            
            // Поиск в style атрибутах (background-image и т.д.)
            document.querySelectorAll('[style*="video"], [style*="url"]').forEach(el => {
                let style = el.getAttribute('style');
                let matches = style.match(/url\\(['"]?([^'")]+)['"]?\\)/g);
                if (matches) {
                    matches.forEach(m => {
                        let url = m.match(/url\\(['"]?([^'")]+)['"]?\\)/)[1];
                        if (url && (url.includes('mp4') || url.includes('webm') || url.includes('video'))) {
                            videos.push(url);
                        }
                    });
                }
            });
            
            return Array.from(new Set(videos)); // Удаляем дубликаты
            """
            
            result = self.driver.execute_script(script)
            links.extend(result if result else [])
            
        except Exception as e:
            print(f"⚠️ Ошибка поиска скрытых видео: {e}")
        
        return links
    
    def extract_links(self, url: str) -> Tuple[List[str], List[Dict]]:
        """
        Основной метод извлечения всех видеоссылок со страницы.
        
        Returns:
            (direct_video_urls: List[str], page_info: List[Dict])
            где page_info содержит информацию о найденных ссылках
        """
        video_urls = []
        page_info = []
        
        try:
            # Инициализируем драйвер
            self.driver = self._init_driver()
            if not self.driver:
                return video_urls, page_info
            
            print(f"🌐 Открываем страницу: {url}")
            self.driver.get(url)
            
            # Ждём загрузки контента
            WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_all_elements_located((By.TAG_NAME, "body"))
            )
            
            time.sleep(3)  # Даём время на загрузку JS контента
            
            # 1. Ищем видео в обычных элементах
            print("🔍 Поиск видеоссылок...")
            for selector in self.COMMON_VIDEO_SELECTORS:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for elem in elements:
                        link = self._extract_video_from_attributes(elem)
                        if link and link not in video_urls:
                            video_urls.append(link)
                            page_info.append({
                                'type': 'common_selector',
                                'selector': selector,
                                'url': link
                            })
                except:
                    continue
            
            # 2. Ищем скрытые видео через JavaScript
            print("🔎 Поиск скрытых видео...")
            hidden_videos = self._find_hidden_videos()
            for link in hidden_videos:
                if link and link not in video_urls:
                    video_urls.append(link)
                    page_info.append({
                        'type': 'hidden_element',
                        'selector': 'javascript_injection',
                        'url': link
                    })
            
            # 3. Ищем кнопки загрузки
            print("⬇️ Поиск кнопок загрузки...")
            download_links = self._find_download_buttons()
            for link in download_links:
                if link and link not in video_urls:
                    video_urls.append(link)
                    page_info.append({
                        'type': 'download_button',
                        'selector': 'download_button',
                        'url': link
                    })
            
            # Фильтруем и валидируем ссылки
            valid_urls = []
            for url_item in video_urls:
                if self._is_video_url(url_item):
                    # Нормализуем URL (абсолютный путь)
                    if url_item.startswith('/'):
                        parsed = urlparse(url)
                        absolute_url = f"{parsed.scheme}://{parsed.netloc}{url_item}"
                        valid_urls.append(absolute_url)
                    elif not url_item.startswith('http'):
                        parsed = urlparse(url)
                        absolute_url = f"{parsed.scheme}://{parsed.netloc}/{url_item}"
                        valid_urls.append(absolute_url)
                    else:
                        valid_urls.append(url_item)
            
            print(f"✅ Найдено видеоссылок: {len(valid_urls)}")
            return valid_urls, page_info
            
        except TimeoutException:
            print(f"⏱️ Таймаут загрузки страницы: {url}")
            return video_urls, page_info
        except WebDriverException as e:
            print(f"❌ Ошибка WebDriver: {e}")
            return video_urls, page_info
        except Exception as e:
            print(f"❌ Ошибка извлечения ссылок: {e}")
            return video_urls, page_info
        finally:
            if self.driver:
                try:
                    self.driver.quit()
                except:
                    pass
    
    
    def click_video_player(self) -> bool:
        """
        Автоматически находит и нажимает на кнопку Play видеоплеера.
        Поддерживает различные виды видеоплееров (HTML5, YouTube, Vimeo и т.д.)
        
        Returns:
            True если успешно найден и нажат видеоплеер, False если ошибка
        """
        if not self.driver:
            print("❌ Драйвер не инициализирован")
            return False
        
        try:
            print("🎬 Поиск видеоплеера...")
            
            # Селекторы для различных видеоплееров
            player_selectors = [
                # HTML5 video
                'video', 'video button[aria-label*="Play"]', 'video button[role="button"]',
                # YouTube Player
                'button[aria-label="Play (k)"]', 'button.ytp-play-button',
                '[role="presentation"] button[aria-label*="play" i]',
                # Vimeo
                'button[data-action="play"]', '[data-action="play"]',
                # Generic
                'button[class*="play" i]', '.play-button', '.player-button',
                '[role="button"][aria-label*="Play" i]',
                'a[class*="play" i]', 'div[class*="play-button" i]'
            ]
            
            for selector in player_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        # Проверяем видимость элемента
                        if element.is_displayed():
                            # Проверяем, что это именно кнопка Play
                            text = element.get_attribute('aria-label') or element.text or ""
                            if "play" in text.lower() or "play" in selector.lower():
                                try:
                                    # Скроллим к элементу
                                    self.driver.execute_script(
                                        "arguments[0].scrollIntoView(true);",
                                        element
                                    )
                                    time.sleep(0.5)
                                    
                                    # Нажимаем на элемент
                                    element.click()
                                    print(f"✅ Нажал на видеоплеер: {selector}")
                                    time.sleep(1)
                                    return True
                                except Exception as e:
                                    # Пробуем через JavaScript если обычный клик не сработал
                                    try:
                                        self.driver.execute_script(
                                            "arguments[0].click();",
                                            element
                                        )
                                        print(f"✅ Нажал на видеоплеер через JS: {selector}")
                                        time.sleep(1)
                                        return True
                                    except:
                                        continue
                except:
                    continue
            
            # Fallback: пробуем через JavaScript
            print("⏳ Пробую альтернативные методы нажатия...")
            try:
                # Для HTML5 video
                script = """
                    let video = document.querySelector('video');
                    if (video && video.paused) {
                        video.play();
                        return 'HTML5 video played';
                    }
                    
                    let playBtn = document.querySelector('[role="button"][aria-label*="Play"], 
                                                          button[aria-label*="play"],
                                                          button[class*="play"]');
                    if (playBtn) {
                        playBtn.click();
                        return 'Play button clicked';
                    }
                    
                    return 'No player found';
                """
                result = self.driver.execute_script(script)
                if result != 'No player found':
                    print(f"✅ {result}")
                    return True
            except:
                pass
            
            print("⚠️ Видеоплеер не найден")
            return False
            
        except Exception as e:
            print(f"❌ Ошибка при нажатии на видеоплеер: {e}")
            return False
    
    def youtube_login(self, email: str, password: str, verify_code: str = None, save_cookies_path: str = None) -> bool:
        """
        Выполняет вход в YouTube аккаунт.
        
        Args:
            email: Email Google аккаунта
            password: Пароль Google аккаунта
            verify_code: Код двухфакторной аутентификации (если нужен)
            save_cookies_path: Путь для сохранения куки (опционально)
        
        Returns:
            True если успешно, False если ошибка
        """
        if not self.driver:
            self.driver = self._init_driver()
        
        if not self.driver:
            print("❌ Не удалось инициализировать браузер")
            return False
        
        try:
            # Используем прямую ссылку на авторизацию
            auth_url = "https://accounts.google.com/ServiceLogin?service=youtube&uilel=3&passive=true&continue=https%3A%2F%2Fwww.youtube.com%2Fsignin%3Faction_handle_signin%3Dtrue%26app%3Ddesktop%26hl%3Dru%26next%3Dhttps%253A%252F%252Fwww.youtube.com%252F&hl=ru&ec=65620"
            
            print("🔐 Переходу на страницу авторизации...")
            self.driver.get(auth_url)
            time.sleep(2)
            
            # Проверяем, может быть уже авторизованы
            try:
                profile_btn = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, "//yt-img-shadow[@id='avatar-btn']|//button[@aria-label='Create a video or post']"))
                )
                if profile_btn:
                    print("✅ Уже авторизованы в YouTube!")
                    return True
            except:
                pass
            
            # Вводим email
            print("📧 Ввожу email...")
            try:
                email_field = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.ID, "identifierId"))
                )
                email_field.clear()
                email_field.send_keys(email)
                
                # Нажимаем Next
                try:
                    next_button = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.ID, "identifierNext"))
                    )
                    next_button.click()
                except:
                    # Пробуем нажать Enter
                    email_field.send_keys(Keys.RETURN)
                
                time.sleep(3)
            except TimeoutException:
                print("❌ Поле email не найдено")
                return False
            except Exception as e:
                print(f"❌ Ошибка ввода email: {e}")
                return False
            
            # Вводим пароль
            print("🔑 Ввожу пароль...")
            try:
                # Используем точный селектор для поля пароля
                password_field = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "#password"))
                )
                password_field.clear()
                password_field.send_keys(password)
                
                # Нажимаем кнопку авторизации с точным селектором
                try:
                    auth_button = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "#buttons > ytd-button-renderer > yt-button-shape > a > yt-touch-feedback-shape > div.yt-spec-touch-feedback-shape__fill"))
                    )
                    auth_button.click()
                except:
                    # Fallback: просто нажимаем Enter
                    print("⏳ Пробую нажать Enter...")
                    password_field.send_keys(Keys.RETURN)
                
                time.sleep(3)
            except TimeoutException:
                print("⚠️ Поле пароля не найдено (возможно требуется двухфакторная аутентификация)")
            except Exception as e:
                print(f"❌ Ошибка ввода пароля: {e}")
                return False
            
            # Проверяем, нужна ли двухфакторная аутентификация
            try:
                verify_field = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, "//input[@aria-label='Enter your verification code']|//input[@name='verificationCode']"))
                )
                if verify_code:
                    print(f"🔐 Ввожу код 2FA...")
                    verify_field.clear()
                    verify_field.send_keys(verify_code)
                    
                    try:
                        verify_button = self.driver.find_element(By.ID, "verifyButton")
                        verify_button.click()
                    except:
                        verify_field.send_keys(Keys.RETURN)
                    
                    time.sleep(3)
                else:
                    print("⚠️ Требуется двухфакторная аутентификация. Ввожу код вручную...")
                    # Даём 90 секунд на ручной ввод кода
                    for i in range(90):
                        try:
                            verify_field_check = self.driver.find_element(By.XPATH, "//input[@aria-label='Enter your verification code']|//input[@name='verificationCode']")
                            if not verify_field_check:
                                break
                        except:
                            break
                        time.sleep(1)
            except TimeoutException:
                # 2FA не требуется
                print("✅ 2FA не требуется")
                pass
            except Exception as e:
                print(f"⚠️ Ошибка с 2FA: {e}")
            
            # Переходим на YouTube и проверяем авторизацию
            print("⏳ Проверяю авторизацию...")
            self.driver.get("https://www.youtube.com")
            
            # Ждём загрузки страницы
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
            except:
                pass
            
            time.sleep(2)
            
            # Проверяем успешность входа
            try:
                profile = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, "//yt-img-shadow[@id='avatar-btn']|//button[@aria-label='Create a video or post']"))
                )
                print("✅ Вход в YouTube успешен!")
                
                # Сохраняем куки если указан путь
                if save_cookies_path:
                    try:
                        cookies = self.driver.get_cookies()
                        import json
                        with open(save_cookies_path, 'w') as f:
                            json.dump(cookies, f, indent=2)
                        print(f"💾 Куки сохранены в {save_cookies_path}")
                    except Exception as e:
                        print(f"⚠️ Не удалось сохранить куки: {e}")
                
                return True
            except:
                print("⚠️ Статус входа неясен, но продолжаю...")
                
                # Все равно пробуем сохранить куки
                if save_cookies_path:
                    try:
                        cookies = self.driver.get_cookies()
                        import json
                        with open(save_cookies_path, 'w') as f:
                            json.dump(cookies, f, indent=2)
                        print(f"💾 Куки сохранены в {save_cookies_path}")
                    except Exception as e:
                        print(f"⚠️ Не удалось сохранить куки: {e}")
                
                return True
            
        except KeyboardInterrupt:
            print("❌ Вход отменён пользователем")
            return False
        except Exception as e:
            print(f"❌ Ошибка при входе в YouTube: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def extract_with_cookies(
        self, 
        url: str, 
        cookies_path: Optional[str] = None,
        browser: str = "chrome"
    ) -> Tuple[List[str], List[Dict]]:
        """
        Извлекает ссылки заходя с куками (для приватных видео).
        
        Args:
            url: URL страницы
            cookies_path: Путь к файлу с куками
            browser: Браузер для получения куков
        
        Returns:
            (video_urls, page_info)
        """
        # TODO: Интегрировать с yt-dlp cookies или загруженными куками
        return self.extract_links(url)
