"""
utils/text_extractor.py - استخراج البيانات من النصوص
"""
import re
import logging
from datetime import datetime, date
from typing import Dict, List, Optional, Any

from config import (
    NATIONAL_ID_PATTERN, CREDIT_SCORE_PATTERN, W_PHRASE_PATTERN,
    DATE_PATTERN, REFERENCE_PATTERN, INSTITUTION_CODE_PATTERN,
    SPECIAL_PHRASES, INSTITUTION_MAPPING, analyze_credit_rating
)

logger = logging.getLogger(__name__)


class TextExtractor:
    """مستخرج البيانات من النصوص"""
    
    @staticmethod
    def extract_national_id(text: str) -> Optional[str]:
        match = re.search(NATIONAL_ID_PATTERN, text)
        return match.group(0) if match else None
    
    @staticmethod
    def extract_credit_score(text: str) -> Optional[int]:
        match = re.search(CREDIT_SCORE_PATTERN, text)
        return int(match.group(1)) if match else None
    
    @staticmethod
    def extract_w_phrases(text: str) -> List[str]:
        return re.findall(W_PHRASE_PATTERN, text)
    
    @staticmethod
    def extract_institution_codes(text: str) -> Dict[str, str]:
        found_codes = {}
        codes = re.findall(INSTITUTION_CODE_PATTERN, text)
        for code in codes:
            clean_code = code.strip()
            institution_name = INSTITUTION_MAPPING.get(clean_code, "رمز غير معروف")
            if clean_code not in found_codes:
                found_codes[clean_code] = institution_name
        return found_codes
    
    @staticmethod
    def extract_special_phrases(text: str) -> Dict[str, int]:
        found = {}
        for phrase_config in SPECIAL_PHRASES:
            matches = re.findall(phrase_config["pattern"], text, re.IGNORECASE)
            if matches:
                found[phrase_config["display"]] = len(matches)
        return found
    
    @staticmethod
    def extract_report_date(text: str) -> Optional[str]:
        match = re.search(DATE_PATTERN, text)
        return match.group(0) if match else None
    
    @staticmethod
    def extract_reference_number(text: str) -> Optional[str]:
        match = re.search(REFERENCE_PATTERN, text)
        return match.group(0) if match else None
    
    @staticmethod
    def extract_name_after_id(text: str, national_id: str) -> Optional[str]:
        if not national_id:
            return None
        lines = text.split('\n')
        for i, line in enumerate(lines):
            if national_id in line and i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                arabic_match = re.search(r'[\u0600-\u06FF\s]+', next_line)
                if arabic_match:
                    name = arabic_match.group(0).strip()
                    if len(name) > 2:
                        return name
        return None


class DataProcessor:
    """معالج البيانات المحسوبة"""
    
    @staticmethod
    def calculate_age_from_national_id(national_id: str) -> Optional[Dict]:
        try:
            if len(national_id) != 14:
                return None
            century = 2000 if national_id[0] == '3' else 1900
            year = century + int(national_id[1:3])
            month = int(national_id[3:5])
            day = int(national_id[5:7])
            
            birth_date = f"{day:02d}/{month:02d}/{year}"
            today = date.today()
            birth = date(year, month, day)
            
            age_years = today.year - birth.year
            age_months = today.month - birth.month
            if age_months < 0 or (age_months == 0 and today.day < birth.day):
                age_years -= 1
                age_months = (12 + today.month - birth.month - 1) if age_months < 0 else 11
            
            return {
                "birthDate": birth_date,
                "ageYears": age_years,
                "ageMonths": age_months,
                "display": f"{age_years} سنة و {age_months} شهر"
            }
        except:
            return None
    
    @staticmethod
    def calculate_days_from_report_date(report_date: str) -> Optional[Dict]:
        try:
            if not report_date:
                return None
            day, month, year = map(int, report_date.split('/'))
            report = date(year, month, day)
            today = date.today()
            diff_days = abs((today - report).days)
            return {"days": diff_days, "display": f"{diff_days} يوم"}
        except:
            return None
    
    @staticmethod
    def process_full_text(text: str) -> Dict[str, Any]:
        extractor = TextExtractor()
        processor = DataProcessor()
        
        national_id = extractor.extract_national_id(text)
        credit_score = extractor.extract_credit_score(text)
        
        result = {
            "basicInfo": {
                "nationalId": national_id,
                "creditScore": credit_score,
                "ratingAnalysis": analyze_credit_rating(credit_score) if credit_score else None,
                "name": extractor.extract_name_after_id(text, national_id) if national_id else None,
                "reportDate": extractor.extract_report_date(text),
                "reportNumber": extractor.extract_w_phrases(text)[0] if extractor.extract_w_phrases(text) else None,
                "referenceNumber": extractor.extract_reference_number(text),
            },
            "codes": extractor.extract_institution_codes(text),
            "wPhrases": extractor.extract_w_phrases(text),
            "specialPhrases": extractor.extract_special_phrases(text),
        }
        
        if national_id:
            birth_info = processor.calculate_age_from_national_id(national_id)
            result["basicInfo"]["birthInfo"] = birth_info
            if birth_info and birth_info.get("birthDate"):
                result["basicInfo"]["ageInfo"] = {"display": birth_info["display"]}
        
        if result["basicInfo"]["reportDate"]:
            result["basicInfo"]["reportDaysAgo"] = processor.calculate_days_from_report_date(
                result["basicInfo"]["reportDate"]
            )
        
        return result