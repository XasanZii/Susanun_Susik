"""
Google Sheets Integration для сохранения ссылок и логов.
"""
import os
import json
from datetime import datetime
from typing import List, Dict, Optional


class SheetsManager:
    """
    Менеджер для работы с Google Sheets.
    Сохраняет ссылки и логи ошибок.
    """
    
    def __init__(self):
        self.local_storage_file = "links_and_logs.json"
        self.data = self._load_local_storage()
    
    def _load_local_storage(self) -> Dict:
        """Загрузка локального хранилища"""
        if os.path.exists(self.local_storage_file):
            try:
                with open(self.local_storage_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {"links": [], "error_logs": [], "success_logs": []}
        return {"links": [], "error_logs": [], "success_logs": []}
    
    def _save_local_storage(self):
        """Сохранение локального хранилища"""
        try:
            with open(self.local_storage_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Ошибка сохранения: {e}")
    
    def add_link(self, url: str, title: str = "", status: str = "pending") -> bool:
        """
        Добавление ссылки в таблицу.
        
        Args:
            url: URL видео
            title: Название видео
            status: Статус (pending, completed, error)
        
        Returns:
            True если успешно, False если ошибка
        """
        try:
            link_entry = {
                "timestamp": datetime.now().isoformat(),
                "url": url,
                "title": title,
                "status": status,
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            self.data["links"].append(link_entry)
            self._save_local_storage()
            return True
        except Exception as e:
            print(f"Ошибка добавления ссылки: {e}")
            return False
    
    def update_link_status(self, url: str, status: str, result_path: str = ""):
        """
        Обновление статуса ссылки.
        
        Args:
            url: URL видео
            status: Новый статус (completed, error)
            result_path: Путь к сохранённому файлу
        """
        try:
            for link in self.data["links"]:
                if link["url"] == url:
                    link["status"] = status
                    link["result_path"] = result_path
                    link["completed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    break
            self._save_local_storage()
        except Exception as e:
            print(f"Ошибка обновления: {e}")
    
    def add_error_log(self, url: str, error_message: str) -> bool:
        """
        Добавление записи об ошибке.
        
        Args:
            url: URL видео где произошла ошибка
            error_message: Описание ошибки
        
        Returns:
            True если успешно
        """
        try:
            error_entry = {
                "timestamp": datetime.now().isoformat(),
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "url": url,
                "error": error_message
            }
            
            self.data["error_logs"].append(error_entry)
            self._save_local_storage()
            return True
        except Exception as e:
            print(f"Ошибка логирования ошибки: {e}")
            return False
    
    def add_success_log(self, url: str, title: str, file_path: str) -> bool:
        """
        Добавление записи об успешной загрузке.
        
        Args:
            url: URL видео
            title: Название видео
            file_path: Путь к сохранённому файлу
        
        Returns:
            True если успешно
        """
        try:
            success_entry = {
                "timestamp": datetime.now().isoformat(),
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "url": url,
                "title": title,
                "file_path": file_path
            }
            
            self.data["success_logs"].append(success_entry)
            self._save_local_storage()
            return True
        except Exception as e:
            print(f"Ошибка логирования успеха: {e}")
            return False
    
    def get_all_links(self) -> List[Dict]:
        """Получение всех ссылок"""
        return self.data.get("links", [])
    
    def get_error_logs(self) -> List[Dict]:
        """Получение всех логов ошибок"""
        return self.data.get("error_logs", [])
    
    def get_success_logs(self) -> List[Dict]:
        """Получение всех логов успехов"""
        return self.data.get("success_logs", [])
    
    def export_as_csv(self, csv_type: str = "links") -> str:
        """
        Экспорт данных в CSV формат.
        
        Args:
            csv_type: Тип экспорта (links, errors, successes)
        
        Returns:
            CSV строка
        """
        import csv
        from io import StringIO
        
        output = StringIO()
        
        if csv_type == "links":
            data = self.data["links"]
            if not data:
                return "Нет данных"
            
            writer = csv.DictWriter(output, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
        
        elif csv_type == "errors":
            data = self.data["error_logs"]
            if not data:
                return "Нет данных"
            
            writer = csv.DictWriter(output, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
        
        elif csv_type == "successes":
            data = self.data["success_logs"]
            if not data:
                return "Нет данных"
            
            writer = csv.DictWriter(output, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
        
        return output.getvalue()
