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
