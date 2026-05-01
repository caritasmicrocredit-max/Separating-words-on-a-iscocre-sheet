"""
utils/google_drive_simple.py - جلب ملفات Google Drive
✅ مطابق تماماً لمنطق الـ HTML الذي كان يعمل معك
"""
import requests
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class SimpleDriveFetcher:
    """جلب ملفات Google Drive بنفس طريقة الـ HTML"""
    
    @staticmethod
    def get_file_content(file_id: str) -> Optional[bytes]:
        """
        تحميل ملف من Google Drive
        ✅ يستخدم نفس البروڭسي الذي يعمل في الـ HTML
        """
        # 🔗 نفس الرابط الذي كان يعمل في الـ HTML
        download_url = f"https://drive.google.com/uc?export=download&id={file_id}"
        proxy_url = f"https://api.allorigins.win/raw?url={download_url}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/pdf, */*'
        }
        
        try:
            # الطريقة 1: البروڭسي (نفس الـ HTML)
            response = requests.get(proxy_url, headers=headers, timeout=30)
            if response.status_code == 200 and len(response.content) > 5000:
                logger.info(f"✅ تم التحميل عبر البروڭسي: {file_id} ({len(response.content)} بايت)")
                return response.content
        except Exception as e:
            logger.warning(f"⚠️ البروڭسي فشل: {e}")
            
        try:
            # الطريقة 2: تحميل مباشر مع التعامل مع تأكيد جوجل
            session = requests.Session()
            session.headers.update(headers)
            
            resp = session.get(download_url, allow_redirects=True)
            
            # إذا طلب جوجل تأكيد (للملفات الكبيرة)
            if 'confirm' in resp.text and 'id=' in resp.text:
                import re
                match = re.search(r'confirm=([a-zA-Z0-9_-]+)', resp.text)
                if match:
                    confirm_url = f"{download_url}&confirm={match.group(1)}"
                    resp = session.get(confirm_url, allow_redirects=True)
            
            if resp.status_code == 200 and len(resp.content) > 5000:
                logger.info(f"✅ تم التحميل المباشر: {file_id} ({len(resp.content)} بايت)")
                return resp.content
        except Exception as e:
            logger.warning(f"⚠️ التحميل المباشر فشل: {e}")
            
        return None

    @staticmethod
    def extract_file_id(url: str) -> Optional[str]:
        """استخراج file_id من رابط Google Drive"""
        import re
        patterns = [
            r'/d/([a-zA-Z0-9-_]+)',
            r'id=([a-zA-Z0-9-_]+)',
            r'file/d/([a-zA-Z0-9-_]+)',
            r'open\?id=([a-zA-Z0-9-_]+)'
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match and match[1]:
                return match[1]
        return None