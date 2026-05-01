"""
utils/pdf_processor.py - معالجة ملفات PDF في الذاكرة
مُعدّ خصيصاً لـ Streamlit Cloud
"""
import io
import logging
from typing import Optional

try:
    from pypdf import PdfReader
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False
    try:
        from PyPDF2 import PdfReader
        PYPDF_AVAILABLE = True
    except ImportError:
        PYPDF_AVAILABLE = False

logger = logging.getLogger(__name__)


class PDFProcessor:
    """معالج PDF خفيف يعمل في الذاكرة"""
    
    def __init__(self):
        if not PYPDF_AVAILABLE:
            logger.warning("مكتبة pypdf/PyPDF2 غير مثبتة، لن تعمل معالجة PDF")
    
    def extract_text(self, pdf_bytes: bytes, max_pages: int = 10) -> str:
        """
        استخراج النص من بيانات PDF في الذاكرة
        
        Args:
            pdf_bytes: بيانات الملف
            max_pages: أقصى عدد صفحات للمعالجة
            
        Returns:
            النص المستخرج
        """
        try:
            if not PYPDF_AVAILABLE:
                return ""
            
            pdf_file = io.BytesIO(pdf_bytes)
            reader = PdfReader(pdf_file)
            
            text_parts = []
            pages_to_process = min(len(reader.pages), max_pages)
            
            for i in range(pages_to_process):
                page = reader.pages[i]
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text.strip())
            
            return "\n".join(text_parts)
            
        except Exception as e:
            logger.error(f"خطأ في استخراج النص: {e}")
            return ""
    
    def get_page_count(self, pdf_bytes: bytes) -> int:
        """الحصول على عدد الصفحات"""
        try:
            if not PYPDF_AVAILABLE:
                return 0
            pdf_file = io.BytesIO(pdf_bytes)
            reader = PdfReader(pdf_file)
            return len(reader.pages)
        except:
            return 0