import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Calibration Calculator", page_icon="🧪")

st.title("برنامج حساب معاملات المعايرة (Cubic Fit)")
st.write("أدخل قيم الامتصاصية والتركيز للحصول على Par A, B, C, D")

# ── جدول الإدخال ──────────────────────────────────────────
if 'df' not in st.session_state:
    st.session_state.df = pd.DataFrame({
        'Absorbance':    [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        'Concentration': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    })

if 'coeffs' not in st.session_state:
    st.session_state.coeffs = None

edited_df = st.data_editor(st.session_state.df, num_rows="dynamic", use_container_width=True)

if st.button("احسب المعاملات (Calculate)"):
    df_clean = edited_df.dropna()
    df_clean = df_clean[(df_clean['Absorbance'] != 0) | (df_clean['Concentration'] != 0)]
    x = df_clean['Absorbance'].values      # X = Absorbance
    y = df_clean['Concentration'].values   # Y = Concentration

    if len(x) < 4:
        st.error("الرجاء إدخال 4 نقاط على الأقل.")
    else:
        try:
            # Concentration = A·Abs³ + B·Abs² + C·Abs + D
            coeffs = np.polyfit(x, y, 3)
            st.session_state.coeffs = coeffs
            st.session_state.x = x
            st.session_state.y = y
        except Exception as e:
            st.error(f"خطأ: {e}")

# ═══════════════════════════════════════════════════════════
if st.session_state.coeffs is not None:
    coeffs = st.session_state.coeffs
    x = st.session_state.x   # Absorbance
    y = st.session_state.y   # Concentration
    par_a, par_b, par_c, par_d = coeffs

    # ── Par A B C D ────────────────────────────────────────
    st.write("### النتائج النهائية (تُنقل للجهاز):")
    st.info("المعادلة: `Concentration = A·Abs³ + B·Abs² + C·Abs + D`")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Par A", f"{par_a:.4f}")
    c2.metric("Par B", f"{par_b:.4f}")
    c3.metric("Par C", f"{par_c:.4f}")
    c4.metric("Par D", f"{par_d:.4f}")

    # ── اختبر قيمة Absorbance → Concentration ─────────────
    st.write("---")
    st.write("### 🔍 اختبر قيمة Absorbance")

    col_input, col_result = st.columns([1, 1])
    with col_input:
        test_abs = st.number_input(
            "أدخل قيمة Absorbance:",
            min_value=0.0,
            format="%.4f",
            step=0.0001,
            key="test_absorbance"
        )

    if test_abs > 0:
        calc_conc = np.polyval(coeffs, test_abs)
        with col_result:
            st.metric("Concentration المحسوب", f"{calc_conc:.2f}")
        if test_abs < min(x) or test_abs > max(x):
            st.warning(
                f"⚠️ القيمة {test_abs:.4f} خارج نطاق المعايرة "
                f"({min(x):.4f} → {max(x):.4f}) — النتيجة تقريبية."
            )

    # ── الرسم البياني ──────────────────────────────────────
    st.write("---")
    st.write("### رسم المنحنى البياني:")
    fig, ax = plt.subplots(figsize=(9, 4))
    x_range = np.linspace(min(x), max(x), 300)
    y_fit = np.polyval(coeffs, x_range)
    ax.plot(x_range, y_fit, label='Cubic Fit', color='blue', linewidth=2)
    ax.scatter(x, y, color='red', zorder=5, s=60, label='Calibrators')

    if test_abs > 0:
        calc_conc_plot = np.polyval(coeffs, test_abs)
        ax.axvline(x=test_abs, color='green', linestyle='--', alpha=0.6)
        ax.axhline(y=calc_conc_plot, color='green', linestyle='--', alpha=0.6)
        ax.scatter([test_abs], [calc_conc_plot], color='green', zorder=6, s=120,
                   marker='*', label=f'Test ({test_abs:.4f} → {calc_conc_plot:.2f})')

    ax.set_xlabel('Absorbance')
    ax.set_ylabel('Concentration')
    ax.legend()
    ax.grid(True, alpha=0.3)
    st.pyplot(fig)

    # ── One Point End ───────────────────────────────────────
    st.write("---")
    st.write("### 📊 هل ينفع التحليل يشتغل بـ One Point End؟")

    # K = Conc / Abs  →  Concentration = Absorbance × K
    mask = (x > 0) & (y > 0)
    x_nz = x[mask]   # Absorbance
    y_nz = y[mask]   # Concentration
    factors = y_nz / x_nz   # K = Conc / Abs
    mean_factor = np.mean(factors)
    cv_factor = (np.std(factors) / mean_factor) * 100

    factor_df = pd.DataFrame({
        'Absorbance':          np.round(x_nz, 4),
        'Concentration':       np.round(y_nz, 2),
        'Factor K (Conc/Abs)': np.round(factors, 2)
    })
    st.dataframe(factor_df, use_container_width=True)

    THRESHOLD_CV = 5.0
    col_f1, col_f2, col_f3 = st.columns(3)
    col_f1.metric("متوسط الفاكتور (Mean K)", f"{mean_factor:.2f}")
    col_f2.metric("CV% للفاكتور", f"{cv_factor:.2f}%")

    if cv_factor <= THRESHOLD_CV:
        col_f3.metric("الحكم", "✅ ينفع", delta="One Point OK")
        st.success(
            f"✅ **نعم** — الفاكتور ثابت (CV = {cv_factor:.2f}% ≤ {THRESHOLD_CV}%).\n\n"
            f"يمكن استخدام **One Point End** بمعامل **K = {mean_factor:.2f}**\n\n"
            f"المعادلة: `Concentration = Absorbance × {mean_factor:.2f}`"
        )
    else:
        col_f3.metric("الحكم", "❌ لا ينفع", delta=f"CV = {cv_factor:.2f}%")
        st.error(
            f"❌ **لا** — الفاكتور غير ثابت (CV = {cv_factor:.2f}% > {THRESHOLD_CV}%).\n\n"
            f"يجب استخدام **Cubic Fit** مع Par A, B, C, D.\n\n"
            f"الفاكتور التقريبي: **K = {mean_factor:.2f}** ⚠️ غير دقيق."
        )

    # رسم ثبات الفاكتور
    st.write("#### رسم ثبات الفاكتور K:")
    fig2, ax2 = plt.subplots(figsize=(8, 3))
    ax2.plot(x_nz, factors, 'o-', color='purple', linewidth=2, markersize=7, label='K per point')
    ax2.axhline(y=mean_factor, color='orange', linestyle='--', linewidth=2,
                label=f'Mean K = {mean_factor:.2f}')
    ax2.fill_between(x_nz,
                     mean_factor * (1 - THRESHOLD_CV / 100),
                     mean_factor * (1 + THRESHOLD_CV / 100),
                     alpha=0.15, color='green', label=f'±{THRESHOLD_CV}% zone')
    ax2.set_xlabel('Absorbance')
    ax2.set_ylabel('Factor K (Conc/Abs)')
    ax2.set_title('ثبات الفاكتور عبر نطاق المعايرة')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    st.pyplot(fig2)

st.write("---")
st.caption("Concentration = A·Abs³ + B·Abs² + C·Abs + D")
