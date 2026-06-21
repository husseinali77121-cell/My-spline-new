import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import json
from datetime import datetime

st.set_page_config(page_title="Calibration Spline Curve Tool", page_icon="🧪", layout="wide")

st.title("🧪 Calibration Spline Curve Tool")
st.write("أدخل قيم الامتصاصية والتركيز للحصول على Par A, B, C, D")

# ══════════════════════════════════════════════════════════════
# SESSION STATE INIT
# ══════════════════════════════════════════════════════════════
if 'df' not in st.session_state:
    st.session_state.df = pd.DataFrame({
        'Absorbance':    [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        'Concentration': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    })
if 'coeffs' not in st.session_state:
    st.session_state.coeffs = None
if 'archive' not in st.session_state:
    st.session_state.archive = []   # list of dicts
if 'prev_coeffs' not in st.session_state:
    st.session_state.prev_coeffs = None

# ══════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ══════════════════════════════════════════════════════════════
def compute_r2(y_actual, y_predicted):
    ss_res = np.sum((y_actual - y_predicted) ** 2)
    ss_tot = np.sum((y_actual - np.mean(y_actual)) ** 2)
    return 1 - ss_res / ss_tot if ss_tot != 0 else 0

def compute_residuals(x, y, coeffs):
    y_pred = np.polyval(coeffs, x)
    return y - y_pred

def compute_linearity(x, y):
    # R² of linear fit vs cubic
    lin_coeffs = np.polyfit(x, y, 1)
    y_lin = np.polyval(lin_coeffs, x)
    r2_lin = compute_r2(y, y_lin)
    return r2_lin

def validation_score(r2, max_residual_pct, r2_lin):
    """
    Returns (grade, color, description)
    """
    score = 0
    if r2 >= 0.9999:   score += 3
    elif r2 >= 0.999:  score += 2
    elif r2 >= 0.99:   score += 1

    if max_residual_pct <= 1:   score += 3
    elif max_residual_pct <= 3: score += 2
    elif max_residual_pct <= 5: score += 1

    if r2_lin >= 0.999:   score += 2
    elif r2_lin >= 0.995: score += 1

    if score >= 7:
        return "🟢 Excellent", "#28a745", "معايرة ممتازة — جاهزة للاستخدام"
    elif score >= 5:
        return "🔵 Good", "#007bff", "معايرة جيدة — مقبولة للاستخدام"
    elif score >= 3:
        return "🟡 Acceptable", "#ffc107", "معايرة مقبولة — يُنصح بإعادة التحقق"
    else:
        return "🔴 Failed", "#dc3545", "معايرة فاشلة — أعد المعايرة"

def detect_outliers(x, y, coeffs, threshold_pct=15):
    """Returns list of outlier indices"""
    y_pred = np.polyval(coeffs, x)
    outliers = []
    for i in range(len(y)):
        if y_pred[i] != 0:
            pct = abs((y[i] - y_pred[i]) / y_pred[i]) * 100
            if pct > threshold_pct:
                outliers.append((i, pct))
    return outliers

# ══════════════════════════════════════════════════════════════
# DATA ENTRY
# ══════════════════════════════════════════════════════════════
st.write("### 📋 جدول بيانات المعايرة")
col_table, col_hint = st.columns([3, 1])
with col_hint:
    st.info("أدخل قيم الـ Standards\nمن أقل لأعلى تركيز")

edited_df = st.data_editor(st.session_state.df, num_rows="dynamic", use_container_width=True)

cal_name = st.text_input("اسم هذه المعايرة (اختياري):", placeholder="مثال: Ferritin Run#1 — 2025-06-21")

if st.button("🔬 احسب المعاملات (Calculate)", type="primary"):
    df_clean = edited_df.dropna()
    df_clean = df_clean[(df_clean['Absorbance'] != 0) | (df_clean['Concentration'] != 0)]
    x = df_clean['Absorbance'].values
    y = df_clean['Concentration'].values

    if len(x) < 4:
        st.error("الرجاء إدخال 4 نقاط على الأقل.")
    else:
        try:
            coeffs = np.polyfit(x, y, 3)
            # Save previous before updating
            if st.session_state.coeffs is not None:
                st.session_state.prev_coeffs = st.session_state.coeffs
            st.session_state.coeffs = coeffs
            st.session_state.x = x
            st.session_state.y = y
        except Exception as e:
            st.error(f"خطأ: {e}")

# ══════════════════════════════════════════════════════════════
# RESULTS SECTION
# ══════════════════════════════════════════════════════════════
if st.session_state.coeffs is not None:
    coeffs = st.session_state.coeffs
    x = st.session_state.x
    y = st.session_state.y
    par_a, par_b, par_c, par_d = coeffs

    y_pred = np.polyval(coeffs, x)
    r2 = compute_r2(y, y_pred)
    residuals = compute_residuals(x, y, coeffs)
    max_residual_pct = np.max(np.abs(residuals / y * 100)) if np.all(y != 0) else 0
    r2_lin = compute_linearity(x, y)
    grade, grade_color, grade_desc = validation_score(r2, max_residual_pct, r2_lin)

    # ── TAB LAYOUT ──────────────────────────────────────────
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 النتائج",
        "🏆 Validation Score",
        "⚠️ Outlier Detection",
        "🔄 Delta Check",
        "🗂️ Archive",
        "🔍 Sample Simulator"
    ])

    # ────────────────────────────────────────────────────────
    # TAB 1 — النتائج الأساسية
    # ────────────────────────────────────────────────────────
    with tab1:
        st.write("### النتائج النهائية (تُنقل للجهاز):")
        st.info("المعادلة: `Concentration = A·Abs³ + B·Abs² + C·Abs + D`")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Par A", f"{par_a:.6f}")
        c2.metric("Par B", f"{par_b:.6f}")
        c3.metric("Par C", f"{par_c:.6f}")
        c4.metric("Par D", f"{par_d:.6f}")

        # Curve
        st.write("---")
        st.write("### رسم المنحنى:")
        fig, ax = plt.subplots(figsize=(9, 4))
        x_range = np.linspace(min(x), max(x), 300)
        y_fit = np.polyval(coeffs, x_range)
        ax.plot(x_range, y_fit, label='Cubic Spline Fit', color='blue', linewidth=2)
        ax.scatter(x, y, color='red', zorder=5, s=60, label='Calibrators')
        # Residual lines
        for i in range(len(x)):
            ax.plot([x[i], x[i]], [y[i], y_pred[i]], 'gray', linestyle=':', linewidth=1)
        ax.set_xlabel('Absorbance')
        ax.set_ylabel('Concentration')
        ax.set_title('Calibration Spline Curve')
        ax.legend()
        ax.grid(True, alpha=0.3)
        st.pyplot(fig)

        # Residuals table
        st.write("#### جدول المتبقيات (Residuals):")
        res_df = pd.DataFrame({
            'Standard #':    [f"Std {i+1}" for i in range(len(x))],
            'Absorbance':    np.round(x, 4),
            'Actual Conc':   np.round(y, 3),
            'Fitted Conc':   np.round(y_pred, 3),
            'Residual':      np.round(residuals, 4),
            'Residual %':    np.round(residuals / y * 100, 2) if np.all(y != 0) else residuals
        })
        st.dataframe(res_df, use_container_width=True)

        # One Point End
        st.write("---")
        st.write("### 📊 One Point End Analysis")
        mask = (x > 0) & (y > 0)
        x_nz = x[mask]
        y_nz = y[mask]
        factors = y_nz / x_nz
        mean_factor = np.mean(factors)
        cv_factor = (np.std(factors) / mean_factor) * 100
        THRESHOLD_CV = 5.0

        factor_df = pd.DataFrame({
            'Absorbance':          np.round(x_nz, 4),
            'Concentration':       np.round(y_nz, 2),
            'Factor K (Conc/Abs)': np.round(factors, 2)
        })
        st.dataframe(factor_df, use_container_width=True)

        col_f1, col_f2, col_f3 = st.columns(3)
        col_f1.metric("Mean K", f"{mean_factor:.2f}")
        col_f2.metric("CV%", f"{cv_factor:.2f}%")
        if cv_factor <= THRESHOLD_CV:
            col_f3.metric("الحكم", "✅ ينفع", delta="One Point OK")
            st.success(f"✅ يمكن استخدام One Point End — K = {mean_factor:.2f}\nالمعادلة: `Concentration = Absorbance × {mean_factor:.2f}`")
        else:
            col_f3.metric("الحكم", "❌ لا ينفع", delta=f"CV = {cv_factor:.2f}%")
            st.error(f"❌ الفاكتور غير ثابت (CV = {cv_factor:.2f}%) — يجب Cubic Fit.")

        fig2, ax2 = plt.subplots(figsize=(8, 3))
        ax2.plot(x_nz, factors, 'o-', color='purple', linewidth=2, markersize=7, label='K per point')
        ax2.axhline(y=mean_factor, color='orange', linestyle='--', linewidth=2, label=f'Mean K = {mean_factor:.2f}')
        ax2.fill_between(x_nz,
                         mean_factor * (1 - THRESHOLD_CV / 100),
                         mean_factor * (1 + THRESHOLD_CV / 100),
                         alpha=0.15, color='green', label=f'±{THRESHOLD_CV}% zone')
        ax2.set_xlabel('Absorbance')
        ax2.set_ylabel('Factor K')
        ax2.set_title('ثبات الفاكتور K')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        st.pyplot(fig2)

    # ────────────────────────────────────────────────────────
    # TAB 2 — Calibration Validation Score
    # ────────────────────────────────────────────────────────
    with tab2:
        st.write("### 🏆 Calibration Validation Score")
        st.write("تقييم تلقائي لجودة المعايرة بناءً على 4 معايير:")

        # Big grade display
        st.markdown(
            f"""
            <div style='text-align:center; padding:20px; border-radius:12px;
                        background-color:{grade_color}22; border:2px solid {grade_color}'>
                <h1 style='color:{grade_color}; margin:0'>{grade}</h1>
                <p style='font-size:18px; color:#333'>{grade_desc}</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        st.write("")

        col_v1, col_v2, col_v3 = st.columns(3)

        # R²
        r2_color = "normal" if r2 >= 0.999 else "inverse"
        col_v1.metric(
            "R² (Cubic Fit)",
            f"{r2:.6f}",
            delta="Excellent" if r2 >= 0.9999 else ("Good" if r2 >= 0.999 else "Check"),
            delta_color=r2_color
        )

        # Max Residual %
        res_color = "normal" if max_residual_pct <= 3 else "inverse"
        col_v2.metric(
            "Max Residual %",
            f"{max_residual_pct:.2f}%",
            delta="OK" if max_residual_pct <= 5 else "HIGH",
            delta_color=res_color
        )

        # Linearity R²
        lin_color = "normal" if r2_lin >= 0.995 else "inverse"
        col_v3.metric(
            "Linearity (R² Linear)",
            f"{r2_lin:.6f}",
            delta="Linear" if r2_lin >= 0.999 else "Non-linear",
            delta_color=lin_color
        )

        st.write("---")
        st.write("#### معايير التقييم:")
        criteria_df = pd.DataFrame({
            'المعيار': ['R² (Cubic)', 'Max Residual %', 'Linearity R²'],
            'القيمة الحالية': [f"{r2:.6f}", f"{max_residual_pct:.2f}%", f"{r2_lin:.6f}"],
            'Excellent': ['≥ 0.9999', '≤ 1%', '≥ 0.999'],
            'Good': ['≥ 0.999', '≤ 3%', '≥ 0.995'],
            'Acceptable': ['≥ 0.99', '≤ 5%', '≥ 0.99'],
            'Failed': ['< 0.99', '> 5%', '< 0.99'],
        })
        st.dataframe(criteria_df, use_container_width=True, hide_index=True)

        # Save to archive button
        st.write("---")
        if st.button("💾 حفظ هذه المعايرة في الأرشيف", key="save_archive"):
            entry = {
                "name": cal_name if cal_name else f"Calibration {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "par_a": round(par_a, 6),
                "par_b": round(par_b, 6),
                "par_c": round(par_c, 6),
                "par_d": round(par_d, 6),
                "r2": round(r2, 6),
                "max_residual_pct": round(max_residual_pct, 2),
                "r2_lin": round(r2_lin, 6),
                "grade": grade,
                "n_points": len(x)
            }
            st.session_state.archive.append(entry)
            st.success(f"✅ تم حفظ '{entry['name']}' في الأرشيف!")

    # ────────────────────────────────────────────────────────
    # TAB 3 — Auto Outlier Detection
    # ────────────────────────────────────────────────────────
    with tab3:
        st.write("### ⚠️ Auto Outlier Detection")
        st.write("اكتشاف تلقائي للنقاط الشاذة في الـ Standards")

        threshold_pct = st.slider("حد الشذوذ (%)", min_value=5, max_value=30, value=15, step=1)
        outliers = detect_outliers(x, y, coeffs, threshold_pct)

        if not outliers:
            st.success("✅ لا توجد نقاط شاذة — جميع الـ Standards ضمن الحدود المقبولة.")
        else:
            st.warning(f"⚠️ تم اكتشاف {len(outliers)} نقطة شاذة!")
            for idx, pct in outliers:
                st.error(
                    f"🔴 **Standard #{idx+1}** — Absorbance: {x[idx]:.4f} | "
                    f"Concentration: {y[idx]:.3f} | "
                    f"Deviation: **{pct:.1f}%** ← Recommended Re-run"
                )

        # Visual
        fig3, ax3 = plt.subplots(figsize=(9, 4))
        x_range2 = np.linspace(min(x), max(x), 300)
        y_fit2 = np.polyval(coeffs, x_range2)
        ax3.plot(x_range2, y_fit2, color='blue', linewidth=2, label='Cubic Fit')

        outlier_indices = [o[0] for o in outliers]
        for i in range(len(x)):
            if i in outlier_indices:
                ax3.scatter(x[i], y[i], color='red', zorder=6, s=150, marker='X',
                           label=f'Outlier Std#{i+1}' if i == outlier_indices[0] else "")
                ax3.annotate(f'Std#{i+1}\n⚠️', (x[i], y[i]),
                            textcoords="offset points", xytext=(8, 8),
                            color='red', fontsize=9)
            else:
                ax3.scatter(x[i], y[i], color='green', zorder=5, s=60)

        # Tolerance band
        y_upper = np.polyval(coeffs, x_range2) * (1 + threshold_pct/100)
        y_lower = np.polyval(coeffs, x_range2) * (1 - threshold_pct/100)
        ax3.fill_between(x_range2, y_lower, y_upper, alpha=0.1, color='green',
                        label=f'±{threshold_pct}% tolerance')
        ax3.set_xlabel('Absorbance')
        ax3.set_ylabel('Concentration')
        ax3.set_title('Outlier Detection')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        st.pyplot(fig3)

        st.write("#### جدول الانحرافات:")
        dev_df = pd.DataFrame({
            'Standard #': [f"Std {i+1}" for i in range(len(x))],
            'Absorbance': np.round(x, 4),
            'Actual Conc': np.round(y, 3),
            'Expected Conc': np.round(y_pred, 3),
            'Deviation %': np.round(np.abs((y - y_pred) / y_pred * 100) if np.all(y_pred != 0) else np.zeros(len(y)), 2),
            'Status': ['🔴 Outlier' if i in outlier_indices else '✅ OK' for i in range(len(x))]
        })
        st.dataframe(dev_df, use_container_width=True, hide_index=True)

    # ────────────────────────────────────────────────────────
    # TAB 4 — Delta Check
    # ────────────────────────────────────────────────────────
    with tab4:
        st.write("### 🔄 Delta Check — مقارنة المعايرة الجديدة بالقديمة")

        if st.session_state.prev_coeffs is None:
            st.info("ℹ️ لا توجد معايرة سابقة للمقارنة.\n\nاحسب معايرة جديدة بعد تغيير البيانات لتظهر المقارنة هنا.\nأو أدخل المعاملات القديمة يدوياً:")

            st.write("#### إدخال يدوي لمعاملات المعايرة السابقة:")
            mc1, mc2, mc3, mc4 = st.columns(4)
            man_a = mc1.number_input("Par A (قديم)", format="%.6f", key="man_a")
            man_b = mc2.number_input("Par B (قديم)", format="%.6f", key="man_b")
            man_c = mc3.number_input("Par C (قديم)", format="%.6f", key="man_c")
            man_d = mc4.number_input("Par D (قديم)", format="%.6f", key="man_d")

            if st.button("تطبيق المعاملات القديمة", key="apply_prev"):
                st.session_state.prev_coeffs = np.array([man_a, man_b, man_c, man_d])
                st.success("✅ تم تعيين المعايرة القديمة!")
                st.rerun()
        else:
            prev = st.session_state.prev_coeffs
            curr = coeffs
            prev_a, prev_b, prev_c, prev_d = prev
            curr_a, curr_b, curr_c, curr_d = curr

            def delta_pct(old, new):
                if old == 0:
                    return 0
                return ((new - old) / abs(old)) * 100

            da = delta_pct(prev_a, curr_a)
            db = delta_pct(prev_b, curr_b)
            dc = delta_pct(prev_c, curr_c)
            dd = delta_pct(prev_d, curr_d)

            DRIFT_THRESHOLD = 15.0

            st.write("#### مقارنة المعاملات:")
            dc1, dc2, dc3, dc4 = st.columns(4)
            dc1.metric("Par A", f"{curr_a:.6f}", delta=f"{da:+.1f}%", delta_color="inverse" if abs(da) > DRIFT_THRESHOLD else "normal")
            dc2.metric("Par B", f"{curr_b:.6f}", delta=f"{db:+.1f}%", delta_color="inverse" if abs(db) > DRIFT_THRESHOLD else "normal")
            dc3.metric("Par C", f"{curr_c:.6f}", delta=f"{dc:+.1f}%", delta_color="inverse" if abs(dc) > DRIFT_THRESHOLD else "normal")
            dc4.metric("Par D", f"{curr_d:.6f}", delta=f"{dd:+.1f}%", delta_color="inverse" if abs(dd) > DRIFT_THRESHOLD else "normal")

            # Overall drift detection
            max_drift = max(abs(da), abs(db), abs(dc), abs(dd))
            st.write("---")
            if max_drift > DRIFT_THRESHOLD:
                st.error(
                    f"🚨 **Calibration Drift Detected!**\n\n"
                    f"أقصى تغيير في المعاملات: **{max_drift:.1f}%** (حد التنبيه: {DRIFT_THRESHOLD}%)\n\n"
                    f"يُنصح بـ:\n"
                    f"- مراجعة الـ Reagent (هل تغير الـ Lot؟)\n"
                    f"- فحص الـ Standards (هل انتهت صلاحيتها؟)\n"
                    f"- مراجعة درجة حرارة التحليل"
                )
            else:
                st.success(
                    f"✅ **لا يوجد Drift معتد به**\n\n"
                    f"أقصى تغيير: {max_drift:.1f}% — ضمن الحدود الطبيعية (< {DRIFT_THRESHOLD}%)"
                )

            # Table
            delta_df = pd.DataFrame({
                'Parameter': ['Par A', 'Par B', 'Par C', 'Par D'],
                'Previous': [f"{prev_a:.6f}", f"{prev_b:.6f}", f"{prev_c:.6f}", f"{prev_d:.6f}"],
                'Current':  [f"{curr_a:.6f}", f"{curr_b:.6f}", f"{curr_c:.6f}", f"{curr_d:.6f}"],
                'Δ Change %': [f"{da:+.1f}%", f"{db:+.1f}%", f"{dc:+.1f}%", f"{dd:+.1f}%"],
                'Status': [
                    '🔴 Drift' if abs(d) > DRIFT_THRESHOLD else '✅ OK'
                    for d in [da, db, dc, dd]
                ]
            })
            st.dataframe(delta_df, use_container_width=True, hide_index=True)

            # Curve comparison
            st.write("#### مقارنة المنحنيين:")
            fig4, ax4 = plt.subplots(figsize=(9, 4))
            x_r = np.linspace(min(x), max(x), 300)
            ax4.plot(x_r, np.polyval(prev, x_r), 'b--', linewidth=2, label='Previous Calibration')
            ax4.plot(x_r, np.polyval(curr, x_r), 'r-', linewidth=2, label='Current Calibration')
            ax4.scatter(x, y, color='red', zorder=5, s=60)
            ax4.set_xlabel('Absorbance')
            ax4.set_ylabel('Concentration')
            ax4.set_title('Delta Check — Curve Comparison')
            ax4.legend()
            ax4.grid(True, alpha=0.3)
            st.pyplot(fig4)

            if st.button("🔄 مسح المعايرة القديمة", key="clear_prev"):
                st.session_state.prev_coeffs = None
                st.rerun()

    # ────────────────────────────────────────────────────────
    # TAB 5 — Archive
    # ────────────────────────────────────────────────────────
    with tab5:
        st.write("### 🗂️ Multi Calibration Archive")

        if not st.session_state.archive:
            st.info("لا يوجد أرشيف بعد. احفظ المعايرات من تبويب Validation Score.")
        else:
            archive = st.session_state.archive
            arch_df = pd.DataFrame(archive)
            display_cols = ['name', 'timestamp', 'par_a', 'par_b', 'par_c', 'par_d',
                           'r2', 'max_residual_pct', 'grade', 'n_points']
            arch_df_display = arch_df[display_cols].rename(columns={
                'name': 'الاسم', 'timestamp': 'التاريخ',
                'par_a': 'Par A', 'par_b': 'Par B', 'par_c': 'Par C', 'par_d': 'Par D',
                'r2': 'R²', 'max_residual_pct': 'Max Res%',
                'grade': 'التقييم', 'n_points': 'عدد النقاط'
            })
            st.dataframe(arch_df_display, use_container_width=True, hide_index=True)

            # Time-series charts
            st.write("#### تطور المعاملات عبر الزمن:")
            fig5, axes = plt.subplots(2, 2, figsize=(12, 8))
            params = ['par_a', 'par_b', 'par_c', 'par_d']
            colors = ['blue', 'red', 'green', 'purple']
            names = [a['name'] for a in archive]

            for idx, (param, color) in enumerate(zip(params, colors)):
                ax = axes[idx//2][idx%2]
                vals = [a[param] for a in archive]
                ax.plot(range(len(vals)), vals, 'o-', color=color, linewidth=2, markersize=8)
                ax.set_xticks(range(len(vals)))
                ax.set_xticklabels([n[:12] for n in names], rotation=30, ha='right', fontsize=7)
                ax.set_title(f'Par {param[-1].upper()} over time')
                ax.grid(True, alpha=0.3)

            plt.tight_layout()
            st.pyplot(fig5)

            # R² trend
            st.write("#### تطور جودة المعايرة (R²):")
            fig6, ax6 = plt.subplots(figsize=(9, 3))
            r2_vals = [a['r2'] for a in archive]
            ax6.plot(range(len(r2_vals)), r2_vals, 'o-', color='teal', linewidth=2, markersize=8)
            ax6.axhline(y=0.999, color='orange', linestyle='--', label='Good threshold (0.999)')
            ax6.axhline(y=0.9999, color='green', linestyle='--', label='Excellent threshold (0.9999)')
            ax6.set_xticks(range(len(r2_vals)))
            ax6.set_xticklabels([n[:12] for n in names], rotation=30, ha='right', fontsize=7)
            ax6.set_ylim([max(0.98, min(r2_vals) - 0.001), 1.0001])
            ax6.set_title('R² Trend')
            ax6.legend(fontsize=8)
            ax6.grid(True, alpha=0.3)
            st.pyplot(fig6)

            # Export archive
            if st.button("📥 تصدير الأرشيف كـ CSV"):
                csv = arch_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    "⬇️ تحميل CSV",
                    csv,
                    "calibration_archive.csv",
                    "text/csv"
                )

            if st.button("🗑️ مسح الأرشيف كله", type="secondary"):
                st.session_state.archive = []
                st.rerun()

    # ────────────────────────────────────────────────────────
    # TAB 6 — Virtual Sample Simulator
    # ────────────────────────────────────────────────────────
    with tab6:
        st.write("### 🔍 Virtual Sample Simulator")
        st.write("أدخل Absorbance لأي عينة واحسب التركيز المتوقع من معادلة المعايرة الحالية")

        col_in, col_out = st.columns(2)
        with col_in:
            test_abs = st.number_input(
                "أدخل قيمة Absorbance:",
                min_value=0.0,
                format="%.4f",
                step=0.0001,
                key="test_absorbance"
            )

        if test_abs > 0:
            calc_conc = np.polyval(coeffs, test_abs)
            with col_out:
                st.metric("Concentration المحسوب", f"{calc_conc:.3f}")

            if test_abs < min(x) or test_abs > max(x):
                st.warning(
                    f"⚠️ القيمة {test_abs:.4f} خارج نطاق المعايرة "
                    f"({min(x):.4f} → {max(x):.4f}) — النتيجة تقريبية (Extrapolation)."
                )
            else:
                st.success(f"✅ القيمة ضمن نطاق المعايرة ({min(x):.4f} → {max(x):.4f})")

            # Visual on curve
            fig7, ax7 = plt.subplots(figsize=(9, 4))
            x_r2 = np.linspace(min(x) * 0.9, max(x) * 1.1, 300)
            y_f2 = np.polyval(coeffs, x_r2)
            ax7.plot(x_r2, y_f2, color='blue', linewidth=2, label='Calibration Curve')
            ax7.scatter(x, y, color='red', zorder=5, s=60, label='Calibrators')
            ax7.axvline(x=test_abs, color='green', linestyle='--', alpha=0.7, linewidth=1.5)
            ax7.axhline(y=calc_conc, color='green', linestyle='--', alpha=0.7, linewidth=1.5)
            ax7.scatter([test_abs], [calc_conc], color='green', zorder=6, s=200,
                       marker='*', label=f'Sample: {test_abs:.4f} → {calc_conc:.3f}')
            ax7.set_xlabel('Absorbance')
            ax7.set_ylabel('Concentration')
            ax7.set_title('Sample Result on Calibration Curve')
            ax7.legend()
            ax7.grid(True, alpha=0.3)
            st.pyplot(fig7)

        # Batch input
        st.write("---")
        st.write("#### 📋 Batch Simulator — أدخل عدة عينات مرة واحدة:")
        batch_input = st.text_area(
            "أدخل قيم Absorbance (كل قيمة في سطر):",
            placeholder="مثال:\n0.245\n0.512\n0.789",
            height=150
        )
        if st.button("احسب Batch", key="batch_calc"):
            try:
                lines = [l.strip() for l in batch_input.strip().split('\n') if l.strip()]
                abs_vals = [float(v) for v in lines]
                conc_vals = [np.polyval(coeffs, a) for a in abs_vals]
                in_range = ['✅ In Range' if min(x) <= a <= max(x) else '⚠️ Extrapolation' for a in abs_vals]
                batch_df = pd.DataFrame({
                    'Sample #': [f"S{i+1}" for i in range(len(abs_vals))],
                    'Absorbance': abs_vals,
                    'Concentration': [round(c, 3) for c in conc_vals],
                    'Status': in_range
                })
                st.dataframe(batch_df, use_container_width=True, hide_index=True)

                # Export
                csv2 = batch_df.to_csv(index=False).encode('utf-8')
                st.download_button("⬇️ تحميل النتائج CSV", csv2, "batch_results.csv", "text/csv")
            except Exception as e:
                st.error(f"خطأ في الإدخال: {e}")

# ══════════════════════════════════════════════════════════════
st.write("---")
st.caption("🧪 Calibration Spline Curve Tool — Concentration = A·Abs³ + B·Abs² + C·Abs + D")
