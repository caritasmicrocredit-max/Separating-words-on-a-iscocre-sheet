"""
app.py - التطبيق الرئيسي باستخدام Streamlit
نظام البحث والمعالجة المتكامل - نسخة Google Drive
"""
import streamlit as st
import pandas as pd
import logging
import tempfile
import os
from pathlib import Path

# استيراد الوحدات المحلية
from config import APP_TITLE, APP_ICON, analyze_credit_rating
from utils.pdf_processor import PDFProcessor
from utils.google_drive import GoogleDriveHandler, SimpleDriveFetcher
from utils.text_extractor import DataProcessor
from utils.excel_export import ExcelExporter

# إعدادات الصفحة
st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded"
)

# إعدادات RTL واللغة العربية
st.markdown("""
    <style>
    .main {direction: rtl; text-align: right;}
    .stTextInput input {direction: rtl; text-align: right;}
    .stTextArea textarea {direction: rtl; text-align: right;}
    div[data-testid="stExpander"] {direction: rtl; text-align: right;}
    .stAlert {direction: rtl; text-align: right;}
    </style>
""", unsafe_allow_html=True)

# إعداد logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === تهيئة الجلسات ===
if 'processed_data' not in st.session_state:
    st.session_state.processed_data = None
if 'pdf_content' not in st.session_state:
    st.session_state.pdf_content = None
if 'current_file' not in st.session_state:
    st.session_state.current_file = None

# === العنوان ===
st.title(f"{APP_ICON} {APP_TITLE}")
st.markdown("---")

# === الشريط الجانبي ===
with st.sidebar:
    st.header("⚙️ الإعدادات")
    
    # اختيار طريقة البحث
    search_method = st.radio(
        "طريقة البحث:",
        ["🔐 باستخدام حساب Google (API)", "🌐 ملفات عامة (بدون مصادقة)", "📁 ملف محلي"],
        index=2
    )
    
    st.markdown("---")
    
    # إعدادات المعالجة
    st.subheader("🔧 خيارات المعالجة")
    pdf_engine = st.selectbox(
        "محرك استخراج النصوص:",
        ["pdfplumber (أفضل)", "PyPDF2 (أسرع)"],
        index=0
    )
    
    st.markdown("---")
    
    # معلومات سريعة
    with st.expander("ℹ️ معلومات عن التطبيق"):
        st.markdown("""
        ### 📋 المميزات:
        - 🔍 البحث عن ملفات بالرقم القومي
        - 📄 عرض ومعالجة ملفات PDF
        - 🏦 استخراج أكواد المؤسسات
        - ⭐ تحليل التقييم الائتماني
        - 📊 تصدير النتائج إلى Excel
        
        ### 🔗 الروابط:
        - [مستودع GitHub](#)
        - [دليل الاستخدام](#)
        """)

# === المنطقة الرئيسية ===
col1, col2, col3 = st.columns([1, 2, 1])

# --- العمود الأيمن: البحث والبيانات الأساسية ---
with col1:
    st.subheader("🔍 البحث")
    
    national_id_input = st.text_input(
        "الرقم القومي (14 رقم):",
        placeholder="أدخل الرقم القومي للبحث...",
        max_chars=14,
        key="national_id_search"
    )
    
    # زر البحث
    if st.button("🔎 بحث", type="primary", use_container_width=True):
        if not national_id_input or not national_id_input.isdigit() or len(national_id_input) != 14:
            st.error("⚠️ الرجاء إدخال رقم قومي صحيح (14 رقم)")
        else:
            with st.spinner("جاري البحث..."):
                # تنفيذ البحث حسب الطريقة المختارة
                if search_method == "🔐 باستخدام حساب Google (API)":
                    handler = GoogleDriveHandler()
                    if handler.connect(GOOGLE_DRIVE_SCOPES):
                        files = handler.search_files(national_id_input)
                        if files:
                            st.success(f"✅ تم العثور على {len(files)} ملف")
                            st.session_state.search_results = files
                        else:
                            st.warning("❌ لم يتم العثور على ملفات مطابقة")
                    else:
                        st.error("❌ فشل الاتصال بـ Google Drive. تحقق من ملف credentials.json")
                
                elif search_method == "🌐 ملفات عامة (بدون مصادقة)":
                    # للعرض فقط - يحتاج إلى تنفيذ مخصص
                    st.info("ℹ️ البحث عن ملفات عامة يتطلب إعداد Google Custom Search API")
                    st.code("يمكنك إضافة معرفات الملفات يدوياً في ملف إعدادات")
                
                else:  # ملف محلي
                    st.info("ℹ️ استخدم زر رفع الملف في الأسفل للبحث المحلي")

    st.markdown("---")
    
    # عرض نتائج البحث
    if 'search_results' in st.session_state and st.session_state.search_results:
        st.subheader("📁 نتائج البحث")
        for i, file in enumerate(st.session_state.search_results[:5], 1):
            with st.expander(f"{i}. {file.get('name', 'ملف غير معروف')}"):
                st.text(f"🆔 ID: {file.get('id')}")
                st.text(f"📅 آخر تعديل: {file.get('modifiedTime', '')[:10] if file.get('modifiedTime') else ''}")
                
                if st.button(f"📥 تحميل ومعالجة #{i}", key=f"load_{i}", use_container_width=True):
                    with st.spinner("جاري التحميل والمعالجة..."):
                        handler = GoogleDriveHandler()
                        content = handler.download_file_content(file['id'])
                        
                        if content:
                            st.session_state.pdf_content = content
                            st.session_state.current_file = file['name']
                            
                            # معالجة النص
                            processor = PDFProcessor(preferred_engine="pdfplumber" if "أفضل" in pdf_engine else "pypdf2")
                            text = processor.extract_text_from_bytes(content)
                            
                            if text:
                                st.session_state.processed_data = DataProcessor.process_full_text(text)
                                st.success("✅ تمت المعالجة بنجاح!")
                                st.rerun()
                            else:
                                st.error("❌ لم يتم استخراج نص من الملف")
                        else:
                            st.error("❌ فشل تحميل الملف")
    
    st.markdown("---")
    
    # === بطاقة البيانات الأساسية ===
    st.subheader("👤 بيانات العميل")
    
    if st.session_state.processed_data:
        basic = st.session_state.processed_data.get("basicInfo", {})
        
        # عرض المعلومات في بطاقات
        st.info(f"**الرقم القومي:** `{basic.get('nationalId', 'غير متاح')}`")
        
        if basic.get('name'):
            st.success(f"**الاسم:** {basic['name']}")
        
        if basic.get('birthInfo'):
            st.caption(f"🎂 تاريخ الميلاد: {basic['birthInfo'].get('birthDate')}")
            st.caption(f"📊 العمر: {basic.get('ageInfo', {}).get('display')}")
        
        # التقييم الائتماني
        if basic.get('creditScore'):
            rating = basic.get('ratingAnalysis', {})
            st.metric(
                label="التقييم الائتماني",
                value=basic['creditScore'],
                delta=rating.get('rating')
            )
            st.caption(f"💡 التوصية: {rating.get('decision')}")
        
        if basic.get('reportDate'):
            st.caption(f"📅 تاريخ التقرير: {basic['reportDate']}")
            if basic.get('reportDaysAgo'):
                st.caption(f"⏰ منذ: {basic['reportDaysAgo'].get('display')}")
    else:
        st.info("📭 قم بتحميل ملف لمعالجة البيانات")

# --- العمود الأوسط: عارض PDF ---
with col2:
    st.subheader("📑 عارض PDF")
    
    # منطقة رفع الملفات
    uploaded_file = st.file_uploader(
        "📤 رفع ملف PDF",
        type=['pdf'],
        help="يمكنك رفع ملف من جهازك للمعالجة الفورية"
    )
    
    if uploaded_file:
        with st.spinner("جاري معالجة الملف..."):
            # حفظ مؤقت للملف
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
                tmp.write(uploaded_file.getvalue())
                tmp_path = tmp.name
            
            try:
                # استخراج النص
                engine = "pdfplumber" if "أفضل" in pdf_engine else "pypdf2"
                processor = PDFProcessor(preferred_engine=engine)
                text = processor.extract_text_from_file(tmp_path)
                
                if text:
                    st.session_state.processed_data = DataProcessor.process_full_text(text)
                    st.session_state.pdf_content = uploaded_file.getvalue()
                    st.session_state.current_file = uploaded_file.name
                    st.success(f"✅ تم استخراج {len(text)} حرف")
                    st.rerun()
                else:
                    st.error("❌ لم يتم استخراج نص من الملف")
            finally:
                os.unlink(tmp_path)
    
    # عرض PDF إذا كان متاحاً
    if st.session_state.pdf_content:
        # عرض باستخدام مكون Streamlit
        with st.expander("🔍 معاينة الملف", expanded=True):
            # ملاحظة: streamlit-pdf-viewer قد يحتاج إعدادات إضافية
            # هنا نعرض رسالة بديلة
            st.info("📄 تم تحميل الملف بنجاح")
            st.caption(f"📁 الاسم: {st.session_state.current_file}")
            st.caption(f"📊 الحجم: {len(st.session_state.pdf_content) / 1024:.1f} KB")
            
            # زر لتحميل الملف المحلي
            st.download_button(
                label="💾 تحميل الملف",
                data=st.session_state.pdf_content,
                file_name=st.session_state.current_file or "file.pdf",
                mime="application/pdf"
            )
    else:
        st.markdown("""
        <div style="
            border: 2px dashed #ccc; 
            border-radius: 10px; 
            padding: 40px; 
            text-align: center;
            color: #666;
            margin: 20px 0;
        ">
            <h3>📄 منطقة عرض PDF</h3>
            <p>قم برفع ملف أو البحث في Google Drive للبدء</p>
        </div>
        """, unsafe_allow_html=True)
    
    # عناصر التحكم في العرض (اختياري)
    if st.session_state.processed_data:
        with st.expander("⚙️ خيارات العرض"):
            col_zoom1, col_zoom2 = st.columns(2)
            with col_zoom1:
                if st.button("🔍 تكبير"):
                    st.info("ميزة التكبير تحتاج إلى مكون مخصص")
            with col_zoom2:
                if st.button("🔎 تصغير"):
                    st.info("ميزة التصغير تحتاج إلى مكون مخصص")

# --- العمود الأيسر: النتائج والأكواد ---
with col3:
    st.subheader("🏦 الأكواد والمؤسسات")
    
    if st.session_state.processed_data:
        codes = st.session_state.processed_data.get("codes", {})
        
        if codes:
            # عرض الأكواد في جدول
            code_df = pd.DataFrame([
                {"الكود": code, "المؤسسة": name}
                for code, name in codes.items()
            ])
            st.dataframe(code_df, use_container_width=True, hide_index=True)
            
            # زر نسخ
            if st.button("📋 نسخ الأكواد", use_container_width=True):
                codes_text = "\n".join([f"{c} - {n}" for c, n in codes.items()])
                st.code(codes_text, language="text")
                st.success("✅ تم نسخ الأكواد")
        else:
            st.info("لا توجد أكواد مستخلصة")
    
    st.markdown("---")
    
    st.subheader("⭐ العبارات الخاصة")
    
    if st.session_state.processed_data:
        special = st.session_state.processed_data.get("specialPhrases", {})
        w_phrases = st.session_state.processed_data.get("wPhrases", [])
        
        # عرض جمل W
        if w_phrases:
            st.markdown(f"**جمل W:**")
            for w in w_phrases:
                st.markdown(f"- 🔹 `{w}`")
        
        # عرض العبارات الخاصة
        if special:
            st.markdown("**العبارات المكتشفة:**")
            for phrase, count in special.items():
                st.markdown(f"- {phrase} ({count})")
        elif not w_phrases:
            st.info("لا توجد عبارات خاصة")
    
    st.markdown("---")
    
    # أزرار الإجراءات
    st.subheader("⚡ إجراءات سريعة")
    
    if st.session_state.processed_data:
        if st.button("📊 تصدير إلى Excel", type="primary", use_container_width=True):
            try:
                output_file = ExcelExporter.export_to_excel(
                    st.session_state.processed_data
                )
                with open(output_file, "rb") as f:
                    st.download_button(
                        label="💾 تحميل الملف",
                        data=f.read(),
                        file_name=output_file,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                st.success(f"✅ تم إنشاء: {output_file}")
            except Exception as e:
                st.error(f"❌ خطأ في التصدير: {e}")
        
        if st.button("🗑️ مسح البيانات", use_container_width=True):
            st.session_state.processed_data = None
            st.session_state.pdf_content = None
            st.session_state.current_file = None
            if 'search_results' in st.session_state:
                del st.session_state['search_results']
            st.rerun()
    else:
        st.info("📭 لا توجد بيانات للإجراءات")

# === شريط الحالة السفلي ===
st.markdown("---")
col_status1, col_status2, col_status3 = st.columns(3)

with col_status1:
    st.caption("🔄 حالة المعالجة")
    if st.session_state.processed_data:
        st.success("✅ جاهز")
    else:
        st.warning("⏳ في الانتظار")

with col_status2:
    st.caption("📊 إحصائيات")
    if st.session_state.processed_data:
        codes_count = len(st.session_state.processed_data.get("codes", {}))
        phrases_count = len(st.session_state.processed_data.get("specialPhrases", {}))
        st.text(f"أكواد: {codes_count} | عبارات: {phrases_count}")

with col_status3:
    st.caption("🛠️ الإصدار")
    st.text("v1.0.0 • Streamlit")

# === ملاحظة هامة للمطور ===
if st.checkbox("👨‍💻 وضع المطور", key="dev_mode"):
    with st.expander("🔧 معلومات تقنية", expanded=True):
        st.code("""
# لتشغيل التطبيق محلياً:
streamlit run app.py

# لتهيئة مصادقة Google Drive:
1. أنشئ مشروع في: https://console.cloud.google.com
2. فعّل Drive API
3. أنشئ OAuth 2.0 Client ID
4. حمّل credentials.json وضعه في مجلد المشروع
5. شغّل التطبيق واتبع خطوات المصادقة
        """, language="bash")
        
        st.json({
            "session_state": {
                "has_data": st.session_state.processed_data is not None,
                "has_pdf": st.session_state.pdf_content is not None,
                "current_file": st.session_state.current_file
            }
        })