import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# إعدادات الصفحة
st.set_page_config(page_title="Calibration Calculator", page_icon="🧪")

st.title("برنامج حساب معاملات المعايرة (Cubic Fit)")
st.write("أدخل قيم التركيز والامتصاصية — زي الجهاز بالظبط (X = Concentration, Y = Absorbance)")

# جدول الإدخال
if 'df' not in st.session_state:
    st.session_state.df = pd.DataFrame({
        'Concentration': [0.0, 32.5, 52.0, 100.0, 365.0, 600.0],
        'Absorbance':    [0.0,  0.0,  0.0,   0.0,   0.0,   0.0]
    })

if 'coeffs' not in st.session_state:
    st.session_state.coeffs = None

edited_df = st.data_editor(st.session_state.df, num_rows="dynamic", use_container_width=True)

if st.button("احسب المعاملات (Calculate)"):
    df_clean = edited_df.dropna()
    df_clean = df_clean[(df_clean['Concentration'] != 0) | (df_clean['Absorbance'] != 0)]
    x = df_clean['Concentration'].values   # X = Concentration  ← زي الجهاز
    y = df_clean['Absorbance'].values      # Y = Absorbance     ← زي الجهاز

    if len(x) < 4:
        st.error("الرجاء إدخال 4 نقاط على الأقل.")
    else:
        try:
            # Absorbance = A·Conc³ + B·Conc² + C·Conc + D
            coeffs = np.polyfit(x, y, 3)
            st.session_state.coeffs = coeffs
            st.session_state.x = x
            st.session_state.y = y
        except Exception as e:
            st.error(f"خطأ: {e}")

# ═══════════════════════════════════════════════════════
# عرض النتائج
# ═══════════════════════════════════════════════════════
if st.session_state.coeffs is not None:
    coeffs = st.session_state.coeffs
    x = st.session_state.x   # Concentration
    y = st.session_state.y   # Absorbance
    par_a, par_b, par_c, par_d = coeffs

    # ── Par A B C D ──────────────────────────────────────
    st.write("### النتائج النهائية (تُنقل للجهاز):")
    st.info("المعادلة: `Absorbance = A·Conc³ + B·Conc² + C·Conc + D`")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Par A", f"{par_a:.4f}")
    c2.metric("Par B", f"{par_b:.4f}")
    c3.metric("Par C", f"{par_c:.4f}")
    c4.metric("Par D", f"{par_d:.4f}")

    # ── اختبر قيمة Absorbance → Concentration ────────────
    st.write("---")
    st.write("### 🔍 اختبر قيمة — أدخل Absorbance واحصل على Concentration")
    st.caption("الجهاز بيعمل Reverse Lookup: يدخل Absorbance المقاس → يحل المعادلة عكسياً")

    col_input, col_result = st.columns([1, 1])
    with col_input:
        test_abs = st.number_input(
            "Absorbance المقاس:",
            min_value=0.0,
            format="%.4f",
            step=0.0001,
            key="test_absorbance"
        )

    if test_abs > 0:
        # حل المعادلة عكسياً: A·x³ + B·x² + C·x + (D - test_abs) = 0
        poly_coeffs = [par_a, par_b, par_c, par_d - test_abs]
        roots = np.roots(poly_coeffs)

        # نختار الجذر الحقيقي الموجب في نطاق المعايرة
        conc_min, conc_max = min(x), max(x)
        valid_roots = [
            r.real for r in roots
            if abs(r.imag) < 1e-6 and r.real >= 0
        ]

        # نرتب حسب الأقرب للنطاق
        in_range = [r for r in valid_roots if conc_min <= r <= conc_max]
        out_range = [r for r in valid_roots if r not in in_range]

        if in_range:
            calc_conc = min(in_range, key=lambda r: abs(r - np.mean(x)))
            in_range_flag = True
        elif out_range:
            calc_conc = min(out_range, key=lambda r: abs(r - np.mean(x)))
            in_range_flag = False
        else:
            calc_conc = None
            in_range_flag = False

        with col_result:
            if calc_conc is not None:
                st.metric(
                    label="Concentration المحسوب",
                    value=f"{calc_conc:.2f}"
                )
            else:
                st.error("لا يوجد جذر حقيقي موجب — تحقق من قيمة الامتصاصية.")

        if calc_conc is not None and not in_range_flag:
            st.warning(
                f"⚠️ القيمة خارج نطاق المعايرة ({conc_min:.1f} → {conc_max:.1f}) — "
                f"النتيجة تقريبية."
            )

    # ── الرسم البياني ─────────────────────────────────────
    st.write("---")
    st.write("### رسم المنحنى البياني (زي الجهاز — X: Concentration, Y: Absorbance):")
    fig, ax = plt.subplots(figsize=(9, 4))
    x_range = np.linspace(min(x), max(x), 300)
    y_fit = np.polyval(coeffs, x_range)
    ax.plot(x_range, y_fit, label='Cubic Fit', color='blue', linewidth=2)
    ax.scatter(x, y, color='red', zorder=5, s=60, label='Calibrators')

    # نقطة الاختبار
    if 'test_absorbance' in st.session_state and st.session_state.test_absorbance > 0:
        t_abs = st.session_state.test_absorbance
        poly_c = [par_a, par_b, par_c, par_d - t_abs]
        roots_plot = np.roots(poly_c)
        valid_plot = [r.real for r in roots_plot if abs(r.imag) < 1e-6 and r.real >= 0]
        if valid_plot:
            t_conc = min(valid_plot, key=lambda r: abs(r - np.mean(x)))
            ax.axhline(y=t_abs, color='green', linestyle='--', alpha=0.6)
            ax.axvline(x=t_conc, color='green', linestyle='--', alpha=0.6)
            ax.scatter([t_conc], [t_abs], color='green', zorder=6, s=120,
                       marker='*', label=f'Test ({t_conc:.1f} → {t_abs:.4f})')

    ax.set_xlabel('Concentration')
    ax.set_ylabel('Absorbance')
    ax.legend()
    ax.grid(True, alpha=0.3)
    st.pyplot(fig)

    # ── One Point End ──────────────────────────────────────
    st.write("---")
    st.write("### 📊 هل ينفع التحليل يشتغل بـ One Point End؟")

    # فاكتور One Point = Absorbance / Concentration لكل نقطة (بدون البلانك)
    mask = x > 0
    x_nz = x[mask]
    y_nz = y[mask]
    factors = y_nz / x_nz   # K = Abs / Conc
    mean_factor = np.mean(factors)
    cv_factor = (np.std(factors) / mean_factor) * 100

    factor_df = pd.DataFrame({
        'Concentration': x_nz,
        'Absorbance': y_nz,
        'Factor K (Abs/Conc)': np.round(factors, 6)
    })
    st.dataframe(factor_df, use_container_width=True)

    THRESHOLD_CV = 5.0
    col_f1, col_f2, col_f3 = st.columns(3)
    col_f1.metric("متوسط الفاكتور (Mean K)", f"{mean_factor:.6f}")
    col_f2.metric("CV% للفاكتور", f"{cv_factor:.2f}%")

    if cv_factor <= THRESHOLD_CV:
        col_f3.metric("الحكم", "✅ ينفع", delta="One Point OK")
        st.success(
            f"✅ **نعم** — الفاكتور ثابت (CV = {cv_factor:.2f}% ≤ {THRESHOLD_CV}%).\n\n"
            f"يمكن استخدام **One Point End** بمعامل **K = {mean_factor:.6f}**\n\n"
            f"المعادلة: `Concentration = Absorbance ÷ {mean_factor:.6f}`"
        )
    else:
        col_f3.metric("الحكم", "❌ لا ينفع", delta=f"CV = {cv_factor:.2f}%")
        st.error(
            f"❌ **لا** — الفاكتور غير ثابت (CV = {cv_factor:.2f}% > {THRESHOLD_CV}%).\n\n"
            f"يجب استخدام **Cubic Fit** مع Par A, B, C, D.\n\n"
            f"الفاكتور التقريبي لو احتجته: **K = {mean_factor:.6f}**\n\n"
            f"⚠️ استخدامه سيعطي نتائج غير دقيقة."
        )

    # رسم ثبات الفاكتور
    st.write("#### رسم ثبات الفاكتور K:")
    fig2, ax2 = plt.subplots(figsize=(8, 3))
    ax2.plot(x_nz, factors, 'o-', color='purple', linewidth=2, markersize=7, label='K per point')
    ax2.axhline(y=mean_factor, color='orange', linestyle='--', linewidth=2,
                label=f'Mean K = {mean_factor:.6f}')
    ax2.fill_between(x_nz,
                     mean_factor * (1 - THRESHOLD_CV / 100),
                     mean_factor * (1 + THRESHOLD_CV / 100),
                     alpha=0.15, color='green', label=f'±{THRESHOLD_CV}% zone')
    ax2.set_xlabel('Concentration')
    ax2.set_ylabel('Factor K (Abs/Conc)')
    ax2.set_title('ثبات الفاكتور عبر نطاق المعايرة')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    st.pyplot(fig2)

st.write("---")
st.caption("Biobase BK280 — Cubic Fit: Absorbance = A·Conc³ + B·Conc² + C·Conc + D")
