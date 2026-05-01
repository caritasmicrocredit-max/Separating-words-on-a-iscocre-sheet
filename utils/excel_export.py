"""
utils/excel_export.py - تصدير البيانات إلى Excel (في الذاكرة)
"""
import logging
from typing import Dict, Any
from datetime import datetime
import pandas as pd
import io

logger = logging.getLogger(__name__)


class ExcelExporter:
    """مصدر Excel يعمل في الذاكرة - مثالي لـ Streamlit Cloud"""
    
    @staticmethod
    def create_dataframe(data: Dict[str, Any]) -> pd.DataFrame:
        rows = []
        basic = data.get("basicInfo", {})
        
        rows.append(["== بيانات العميل الأساسية ==", ""])
        rows.append(["الرقم القومي", basic.get("nationalId") or "غير متاح"])
        rows.append(["الاسم", basic.get("name") or "غير متاح"])
        
        birth = basic.get("birthInfo") or {}
        rows.append(["تاريخ الميلاد", birth.get("birthDate") or "غير متاح"])
        
        age = basic.get("ageInfo") or {}
        rows.append(["العمر", age.get("display") or "غير متاح"])
        
        rows.append(["التقييم الائتماني", basic.get("creditScore") or "غير متاح"])
        
        rating = basic.get("ratingAnalysis") or {}
        rows.append(["تحليل التقييم", rating.get("rating") or "غير متاح"])
        rows.append(["توصية التقييم", rating.get("decision") or "غير متاح"])
        
        rows.append(["تاريخ التقرير", basic.get("reportDate") or "غير متاح"])
        
        days = basic.get("reportDaysAgo") or {}
        rows.append(["الاستعلام بقالو", days.get("display") or "غير متاح"])
        
        rows.append(["رقم التقرير", basic.get("reportNumber") or "غير متاح"])
        rows.append(["الرقم المرجعي", basic.get("referenceNumber") or "غير متاح"])
        rows.append(["", ""])
        
        rows.append(["== الأكواد المستخلصة ==", ""])
        rows.append(["الكود", "المؤسسة"])
        for code, name in data.get("codes", {}).items():
            rows.append([code, name])
        rows.append(["", ""])
        
        rows.append(["== جمل W ==", ""])
        for w in data.get("wPhrases", []):
            rows.append([w, ""])
        rows.append(["", ""])
        
        rows.append(["== العبارات الخاصة ==", ""])
        rows.append(["العبارة", "العدد"])
        for phrase, count in data.get("specialPhrases", {}).items():
            rows.append([phrase, count])
        
        return pd.DataFrame(rows, columns=["العنصر", "القيمة"])
    
    @staticmethod
    def export_to_bytes(data: Dict[str, Any]) -> bytes:
        """
        تصدير البيانات كـ bytes في الذاكرة
        
        Returns:
            بيانات ملف Excel كـ bytes
        """
        df = ExcelExporter.create_dataframe(data)
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='البيانات', index=False)
        
        output.seek(0)
        return output.read()