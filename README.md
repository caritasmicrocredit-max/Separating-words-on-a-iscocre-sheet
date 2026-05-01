# 🔍 نظام البحث والمعالجة المتكامل - نسخة Streamlit

نظام متكامل لمعالجة تقارير الائتمان، استخراج البيانات، وتصدير النتائج.

## ✨ المميزات
- 📤 رفع ملفات PDF من الجهاز
- 🔗 دعم روابط Google Drive العامة
- 📄 استخراج النصوص والبيانات تلقائياً
- 🏦 التعرف على أكواد المؤسسات المالية
- ⭐ تحليل التقييم الائتماني
- 📊 تصدير النتائج إلى Excel

## 🚀 التشغيل السريع

### محلياً:
```bash
# 1. استنساخ المشروع
git clone https://github.com/YOUR_USERNAME/caritas-reports-streamlit.git
cd caritas-reports-streamlit

# 2. إنشاء بيئة افتراضية
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. تثبيت المتطلبات
pip install -r requirements.txt

# 4. تشغيل التطبيق
streamlit run app.py