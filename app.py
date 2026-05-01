# app.py - النسخة المُصحّحة تماماً
import streamlit as st
import pandas as pd
import logging
import re
from datetime import datetime, date
import io

# ✅ استيراد صحيح من الوحدات المحلية
from config import APP_TITLE, APP_ICON, analyze_credit_rating, INSTITUTION_MAPPING, SPECIAL_PHRASES
from utils.pdf_processor import PDFProcessor
from utils.text_extractor import DataProcessor, TextExtractor
from utils.excel_export import ExcelExporter
from utils.google_drive_simple import SimpleDriveFetcher

# إعدادات الصفحة
st.set_page_config(page_title=APP_TITLE, page_icon=APP_ICON, layout="wide", initial_sidebar_state="expanded")

# دعم العربية و RTL
st.markdown("""
    <style>
    .main {direction: rtl; text-align: right;}
    .stTextInput input, .stTextArea textarea {direction: rtl; text-align: right;}
    div[data-testid="stExpander"], .stAlert {direction: rtl; text-align: right;}
    </style>
""", unsafe_allow_html=True)

# تهيئة الجلسات
if 'processed_data' not in st.session_state:
    st.session_state.processed_data = None
if 'pdf_content' not in st.session_state:
    st.session_state.pdf_content = None
if 'current_filename' not in st.session_state:
    st.session_state.current_filename = None

# العنوان
st.title(f"{APP_ICON} {APP_TITLE}")
st.markdown("---")

# الشريط الجانبي
with st.sidebar:
    st.header("⚙️ الإعدادات")
    input_method = st.radio("مصدر الملف:", ["📤 رفع ملف من الجهاز", "🔗 رابط ملف عام من Google Drive"], index=0)
    
    st.markdown("---")
    with st.expander("ℹ️ كيفية الاستخدام"):
        st.markdown("""
        ### 📋 الخطوات:
        1. اختر مصدر الملف
        2. ارفع الملف أو أدخل الرابط
        3. انتظر المعالجة التلقائية
        4. راجع النتائج في الأعمدة
        5. حمّل تقرير Excel إذا أردت
        
        ### 🔗 لملفات Google Drive:
        - تأكد أن الملف **عام** (مشارك مع "أي شخص لديه الرابط")
        - انسخ الرابط من زر "مشاركة" في Drive
        """)
    
    if st.button("🗑️ مسح جميع البيانات", use_container_width=True):
        st.session_state.clear()
        st.rerun()

# المنطقة الرئيسية - 3 أعمدة
col1, col2, col3 = st.columns([1, 2, 1])

# --- العمود الأيمن: الإدخال والبيانات الأساسية ---
with col1:
    st.subheader("🔍 إدخال الملف")
    
    if input_method == "📤 رفع ملف من الجهاز":
        uploaded_file = st.file_uploader("اختر ملف PDF", type=['pdf'], help="اختر ملف تقرير من جهازك")
        
        if uploaded_file:
            with st.spinner("🔄 جاري المعالجة..."):
                pdf_bytes = uploaded_file.getvalue()
                st.session_state.pdf_content = pdf_bytes
                st.session_state.current_filename = uploaded_file.name
                
                processor = PDFProcessor()
                text = processor.extract_text(pdf_bytes)
                
                # ✅ عرض النص المستخرج للتحقق (مهم للتصحيح)
                with st.expander("👁️ معاينة النص المستخرج", expanded=False):
                    st.text_area("النص", text[:500] + "..." if len(text) > 500 else text, height=150, disabled=True)
                
                if text and len(text.strip()) > 50:
                    st.session_state.processed_data = DataProcessor.process_full_text(text)
                    st.success(f"✅ تمت معالجة {len(text)} حرف")
                    st.rerun()
                else:
                    st.error("❌ لم يتم استخراج نص كافٍ من الملف")
                    st.caption("💡 قد يكون الملف ممسوحاً ضوئياً (صور) ولا يحتوي على نص قابل للاستخراج")
    
    else:  # رابط Google Drive
        drive_url = st.text_input("رابط ملف Google Drive:", placeholder="https://drive.google.com/file/d/FILE_ID/view")
        
        if st.button("📥 تحميل ومعالجة", type="primary", use_container_width=True):
            if not drive_url:
                st.error("⚠️ الرجاء إدخال رابط الملف")
            else:
                with st.spinner("🔄 جاري التحميل والمعالجة..."):
                    file_id = SimpleDriveFetcher.extract_file_id(drive_url)
                    
                    if not file_id:
                        st.error("❌ لم يتم التعرف على معرف الملف من الرابط")
                    else:
                        content = SimpleDriveFetcher.get_file_content(file_id)
                        
                        if content:
                            st.session_state.pdf_content = content
                            st.session_state.current_filename = f"drive_{file_id}.pdf"
                            
                            processor = PDFProcessor()
                            text = processor.extract_text(content)
                            
                            with st.expander("👁️ معاينة النص المستخرج", expanded=False):
                                st.text_area("النص", text[:500] + "..." if len(text) > 500 else text, height=150, disabled=True)
                            
                            if text and len(text.strip()) > 50:
                                st.session_state.processed_data = DataProcessor.process_full_text(text)
                                st.success(f"✅ تمت المعالجة - {len(text)} حرف")
                                st.rerun()
                            else:
                                st.error("❌ لم يتم استخراج نص كافٍ")
                        else:
                            st.error("❌ فشل تحميل الملف - تأكد أن الملف عام")
    
    st.markdown("---")
    
    # === بطاقة البيانات الأساسية ===
    st.subheader("👤 بيانات العميل")
    
    if st.session_state.processed_data:
        basic = st.session_state.processed_data.get("basicInfo", {})
        
        if basic.get('nationalId'):
            st.info(f"**الرقم القومي:** `{basic['nationalId']}`")
        if basic.get('name'):
            st.success(f"**الاسم:** {basic['name']}")
        if basic.get('birthInfo'):
            st.caption(f"🎂 الميلاد: {basic['birthInfo'].get('birthDate')}")
            if basic.get('ageInfo'):
                st.caption(f"📊 العمر: {basic['ageInfo'].get('display')}")
        if basic.get('creditScore'):
            rating = basic.get('ratingAnalysis', {})
            st.metric(label="التقييم", value=basic['creditScore'], delta=rating.get('rating') if rating else None)
            if rating:
                st.caption(f"💡 {rating.get('decision')}")
        if basic.get('reportDate'):
            st.caption(f"📅 التقرير: {basic['reportDate']}")
            if basic.get('reportDaysAgo'):
                st.caption(f"⏰ منذ: {basic['reportDaysAgo'].get('display')}")
        if basic.get('reportNumber'):
            st.caption(f"🔢 رقم التقرير: {basic['reportNumber']}")
        if basic.get('referenceNumber'):
            st.caption(f"📋 المرجع: {basic['referenceNumber']}")
    else:
        st.info("📭 ارفع ملفاً لبدء المعالجة")

# --- العمود الأوسط: معلومات الملف ---
with col2:
    st.subheader("📄 معلومات الملف")
    
    if st.session_state.current_filename:
        st.success(f"✅ {st.session_state.current_filename}")
        if st.session_state.pdf_content:
            size_kb = len(st.session_state.pdf_content) / 1024
            st.caption(f"📊 الحجم: {size_kb:.1f} KB")
            st.download_button(label="💾 تحميل الملف الأصلي", data=st.session_state.pdf_content, file_name=st.session_state.current_filename, mime="application/pdf", use_container_width=True)
    else:
        st.markdown("<div style='border: 2px dashed #ccc; border-radius: 10px; padding: 30px; text-align: center; color: #666;'><h3>📄 منطقة المعلومات</h3><p>سيظهر هنا معلومات الملف بعد التحميل</p></div>", unsafe_allow_html=True)

# --- العمود الأيسر: النتائج والأكواد ---
with col3:
    st.subheader("🏦 الأكواد والمؤسسات")
    
    if st.session_state.processed_data:
        codes = st.session_state.processed_data.get("codes", {})
        if codes:
            code_df = pd.DataFrame([{"الكود": code, "المؤسسة": name} for code, name in codes.items()])
            st.dataframe(code_df, use_container_width=True, hide_index=True)
            with st.expander("📋 نسخ النتائج"):
                codes_text = "\n".join([f"{c} - {n}" for c, n in codes.items()])
                st.code(codes_text, language="text")
        else:
            st.info("لا توجد أكواد مستخلصة - قد يحتاج الملف لمعالجة مختلفة")
    
    st.markdown("---")
    
    st.subheader("⭐ العبارات الخاصة")
    if st.session_state.processed_data:
        special = st.session_state.processed_data.get("specialPhrases", {})
        w_phrases = st.session_state.processed_data.get("wPhrases", [])
        if w_phrases:
            st.markdown("**جمل W:**")
            for w in w_phrases[:3]:
                st.markdown(f"- 🔹 `{w}`")
        if special:
            st.markdown("**المكتشف:**")
            for phrase, count in special.items():
                st.markdown(f"- {phrase} <span style='color:red'>×{count}</span>", unsafe_allow_html=True)
        if not w_phrases and not special:
            st.info("لا توجد عبارات خاصة")
    
    st.markdown("---")
    
    st.subheader("⚡ تصدير النتائج")
    if st.session_state.processed_data:
        if st.button("📊 إنشاء تقرير Excel", type="primary", use_container_width=True):
            with st.spinner("🔄 جاري إنشاء التقرير..."):
                try:
                    excel_bytes = ExcelExporter.export_to_bytes(st.session_state.processed_data)
                    national_id = st.session_state.processed_data.get("basicInfo", {}).get("nationalId", "unknown")
                    filename = f"report_{national_id}.xlsx"
                    st.download_button(label="💾 تحميل التقرير الآن", data=excel_bytes, file_name=filename, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
                    st.success("✅ جاهز للتحميل!")
                except Exception as e:
                    st.error(f"❌ خطأ: {e}")
    else:
        st.info("📭 لا توجد بيانات للتصدير")

# شريط الحالة
st.markdown("---")
col_s1, col_s2, col_s3 = st.columns(3)
with col_s1:
    status = "✅ جاهز" if st.session_state.processed_data else "⏳ في الانتظار"
    st.caption(f"🔄 الحالة: {status}")
with col_s2:
    if st.session_state.processed_data:
        codes_n = len(st.session_state.processed_data.get("codes", {}))
        phrases_n = len(st.session_state.processed_data.get("specialPhrases", {}))
        st.caption(f"📊 الأكواد: {codes_n} | العبارات: {phrases_n}")
with col_s3:
    st.caption("🛠️ v1.0 • Streamlit")