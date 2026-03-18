#!/usr/bin/env python3
"""
Пример использования Selenium интеграции для извлечения видеоссылок.
"""
import sys
from core.link_extractor import LinkExtractor
from core.selenium_manager import SeleniumManager


def example_1_simple_extraction():
    """Пример 1: Простое извлечение видеоссылок"""
    print("\n" + "="*60)
    print("ПРИМЕР 1: Простое извлечение видеоссылок")
    print("="*60)
    
    url = input("Введите URL страницы с видео: ").strip()
    if not url:
        print("❌ URL не введён")
        return
    
    extractor = LinkExtractor(headless=True, timeout=30)
    print(f"\n🌐 Загружаю {url}...")
    
    video_urls, page_info = extractor.extract_links(url)
    
    if video_urls:
        print(f"\n✅ Найдено {len(video_urls)} видеоссылок:\n")
        for i, link in enumerate(video_urls, 1):
            print(f"{i}. {link}")
        
        print("\n📋 Детали поиска:")
        for info in page_info:
            print(f"  • Тип: {info['type']}, Селектор: {info['selector']}")
    else:
        print("\n❌ Видеоссылки не найдены")


def example_2_browser_manager():
    """Пример 2: Использование SeleniumManager с контролем"""
    print("\n" + "="*60)
    print("ПРИМЕР 2: Использование SeleniumManager")
    print("="*60)
    
    url = input("Введите URL страницы: ").strip()
    if not url:
        print("❌ URL не введён")
        return
    
    browser = input("Выберите браузер (chrome/firefox/edge) [chrome]: ").strip().lower()
    if not browser:
        browser = 'chrome'
    
    print(f"\n🌐 Открываю {browser}...")
    manager = SeleniumManager(browser=browser, headless=True)
    
    if not manager.init_driver():
        print("❌ Не удалось инициализировать браузер")
        return
    
    print(f"📄 Загружаю {url}...")
    if not manager.get(url):
        print("❌ Не удалось загрузить страницу")
        manager.close()
        return
    
    print(f"📋 Заголовок: {manager.get_window_title()}")
    
    # Ищем видеоссылки
    video_elements = manager.find_elements('a[href*="mp4"], a[href*="webm"], video > source')
    print(f"🎬 Найдено видео элементов: {len(video_elements)}")
    
    for i, elem in enumerate(video_elements, 1):
        href = elem.get_attribute('href') or elem.get_attribute('src')
        if href:
            print(f"  {i}. {href}")
    
    manager.close()
    print("✅ Готово")


def example_3_with_javascript():
    """Пример 3: Использование JavaScript для поиска скрытых видео"""
    print("\n" + "="*60)
    print("ПРИМЕР 3: Поиск скрытых видео через JavaScript")
    print("="*60)
    
    url = input("Введите URL страницы: ").strip()
    if not url:
        print("❌ URL не введён")
        return
    
    manager = SeleniumManager(browser='chrome', headless=True)
    if not manager.init_driver():
        print("❌ Не удалось инициализировать браузер")
        return
    
    print(f"📄 Загружаю {url}...")
    if not manager.get(url):
        print("❌ Не удалось загрузить страницу")
        manager.close()
        return
    
    # JavaScript для поиска всех видео, включая скрытые
    script = """
    let videos = new Set();
    
    // HTML5 video
    document.querySelectorAll('video source').forEach(s => {
        if (s.src) videos.add(s.src);
    });
    
    // Атрибуты data-*
    document.querySelectorAll('[data-video-url], [data-video-src]').forEach(el => {
        let url = el.getAttribute('data-video-url') || el.getAttribute('data-video-src');
        if (url) videos.add(url);
    });
    
    // Видеоссылки в href
    document.querySelectorAll('a[href*="mp4"], a[href*="webm"], a[href*="video"]').forEach(a => {
        if (a.href) videos.add(a.href);
    });
    
    return Array.from(videos);
    """
    
    print("🔍 Выполняю JavaScript поиск...")
    videos = manager.execute_script(script)
    
    if videos:
        print(f"\n✅ Найдено {len(videos)} видеоссылок:\n")
        for i, video in enumerate(videos, 1):
            print(f"{i}. {video}")
    else:
        print("\n❌ Видеоссылки не найдены")
    
    manager.close()


def example_4_parallel_extraction():
    """Пример 4: Параллельное извлечение с нескольких сайтов"""
    print("\n" + "="*60)
    print("ПРИМЕР 4: Параллельное извлечение")
    print("="*60)
    
    print("Введите URLs (по одному на строку, пустая строка для завершения):")
    urls = []
    while True:
        url = input("URL: ").strip()
        if not url:
            break
        urls.append(url)
    
    if not urls:
        print("❌ URLs не введены")
        return
    
    print(f"\n🌐 Загружаю {len(urls)} сайтов параллельно...")
    
    import threading
    results = {}
    
    def extract(url):
        try:
            extractor = LinkExtractor(headless=True, timeout=20)
            video_urls, _ = extractor.extract_links(url)
            results[url] = video_urls
        except Exception as e:
            results[url] = []
            print(f"❌ Ошибка для {url}: {e}")
    
    threads = []
    for url in urls:
        thread = threading.Thread(target=extract, args=(url,))
        thread.start()
        threads.append(thread)
    
    for thread in threads:
        thread.join()
    
    print("\n📊 Результаты:\n")
    total = 0
    for url, videos in results.items():
        count = len(videos)
        total += count
        print(f"🔗 {url}")
        print(f"   ✅ Найдено {count} видеоссылок")
        for video in videos[:3]:  # Показываем первые 3
            print(f"      • {video[:60]}...")
        if count > 3:
            print(f"      ... и ещё {count-3}")
        print()
    
    print(f"📈 Итого: {total} видеоссылок с {len(urls)} сайтов")


def main():
    """Главное меню примеров"""
    print("\n" + "="*60)
    print("ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ SELENIUM LINK EXTRACTOR")
    print("="*60)
    
    examples = {
        '1': ('Простое извлечение видеоссылок', example_1_simple_extraction),
        '2': ('Использование SeleniumManager', example_2_browser_manager),
        '3': ('Поиск скрытых видео (JavaScript)', example_3_with_javascript),
        '4': ('Параллельное извлечение', example_4_parallel_extraction),
        '0': ('Выход', None),
    }
    
    while True:
        print("\nДоступные примеры:")
        for key, (desc, _) in examples.items():
            print(f"  {key}. {desc}")
        
        choice = input("\nВыберите пример (0 для выхода): ").strip()
        
        if choice == '0':
            print("\n👋 До свидания!")
            break
        elif choice in examples:
            desc, func = examples[choice]
            print(f"\n▶️  {desc}")
            try:
                func()
            except KeyboardInterrupt:
                print("\n⏹️  Отменено пользователем")
            except Exception as e:
                print(f"\n❌ Ошибка: {e}")
                import traceback
                traceback.print_exc()
        else:
            print("❌ Неверный выбор")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Выход")
        sys.exit(0)
