import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# إعدادات الصفحة
st.set_page_config(page_title="Calibration Calculator", page_icon="🧪")

st.title("برنامج حساب معاملات المعايرة (Cubic Fit)")
st.write("أدخل قيم الامتصاصية والتركيز الخاصة بـ Ferritin للحصول على Par A, B, C, D")

# إنشاء جدول إدخال بيانات ديناميكي
if 'df' not in st.session_state:
    st.session_state.df = pd.DataFrame({
        'Absorbance': [0.0, 0.0, 0.0, 0.0],
        'Concentration': [0.0, 0.0, 0.0, 0.0]
    })

# واجهة الجدول
edited_df = st.data_editor(st.session_state.df, num_rows="dynamic", use_container_width=True)

if st.button("احسب المعاملات (Calculate)"):
    # تجهيز البيانات
    df_clean = edited_df.dropna()
    x = df_clean['Absorbance'].values
    y = df_clean['Concentration'].values
    
    if len(x) < 4:
        st.error("الرجاء إدخال 4 نقاط على الأقل (نظام Cubic يتطلب 4 نقاط).")
    else:
        try:
            # الحساب الرياضي (معادلة الدرجة الثالثة)
            # y = Ax^3 + Bx^2 + Cx + D
            coeffs = np.polyfit(x, y, 3)
            
            # ترتيب المعاملات (A, B, C, D)
            par_a, par_b, par_c, par_d = coeffs
            
            # عرض النتائج في مربعات احترافية
            st.write("### النتائج النهائية (تُنقل للجهاز):")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Par A", f"{par_a:.4f}")
            c2.metric("Par B", f"{par_b:.4f}")
            c3.metric("Par C", f"{par_c:.4f}")
            c4.metric("Par D", f"{par_d:.4f}")
            
            # رسم المنحنى للتأكد من دقة المطابقة
            st.write("---")
            st.write("### رسم المنحنى البياني:")
            fig, ax = plt.subplots()
            x_range = np.linspace(min(x), max(x), 100)
            y_fit = np.polyval(coeffs, x_range)
            ax.plot(x_range, y_fit, label='Cubic Fit', color='blue')
            ax.scatter(x, y, color='red', label='Your Data')
            ax.set_xlabel('Absorbance')
            ax.set_ylabel('Concentration')
            ax.legend()
            st.pyplot(fig)
            
        except Exception as e:
            st.error(f"حدث خطأ أثناء الحساب: {e}")

st.write("---")
st.caption("ملاحظة: تأكد من دقة قيم الامتصاصية (Absorbance) لضمان دقة المعاملات.")
