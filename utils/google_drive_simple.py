"""
utils/google_drive_simple.py - جلب ملفات Google Drive العامة
✅ يعمل على Streamlit Cloud بدون مصادقة
"""
import logging
import requests
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)


class SimpleDriveFetcher:
    """
    جلب ملفات Google Drive العامة
    ⚠️ يعمل فقط مع الملفات المخصصة لـ "أي شخص لديه الرابط"
    """
    
    @staticmethod
    def get_file_content(file_id: str) -> Optional[bytes]:
        """
        جلب محتوى ملف عام كـ bytes
        """
        try:
            download_url = f"https://drive.google.com/uc?export=download&id={file_id}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(download_url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '')
                if content_type == 'application/pdf' or len(response.content) > 10000:
                    return response.content
            
            logger.warning(f"فشل جلب الملف: {response.status_code}")
            return None
            
        except Exception as e:
            logger.error(f"خطأ: {e}")
            return None
    
    @staticmethod
    def extract_file_id(url: str) -> Optional[str]:
        """استخراج معرف الملف من رابط Google Drive"""
        import re
        patterns = [
            r'/d/([a-zA-Z0-9-_]+)',
            r'id=([a-zA-Z0-9-_]+)',
            r'file/d/([a-zA-Z0-9-_]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    @staticmethod
    def search_by_national_id(national_id: str, file_list: List[Dict]) -> List[Dict]:
        """البحث في قائمة ملفات معروفة عن الرقم القومي"""
        return [f for f in file_list if national_id in f.get('name', '').lower()]