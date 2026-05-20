import tkinter as tk
from tkinter import messagebox
import numpy as np
import matplotlib.pyplot as plt

def calculate_parameters():
    concentrations = []
    absorbances = []
    
    # سحب البيانات من الخانات
    for i in range(8):
        conc_str = conc_entries[i].get().strip()
        abs_str = abs_entries[i].get().strip()
        
        if conc_str and abs_str:
            try:
                concentrations.append(float(conc_str))
                absorbances.append(float(abs_str))
            except ValueError:
                messagebox.showerror("خطأ", f"الرجاء إدخال أرقام صحيحة في السطر {i+1}")
                return
                
    if len(concentrations) < 4:
        messagebox.showwarning("تنبيه", "هذا النوع من المعايرة (Cubic) يحتاج 4 نقاط على الأقل لحساب 4 معاملات.")
        return
        
    x = np.array(absorbances)
    y = np.array(concentrations)
    
    try:
        # حساب معادلة الانحدار من الدرجة الثالثة (Cubic Polynomial Fit)
        # x = Absorbance, y = Concentration
        coefficients = np.polyfit(x, y, 3)
        
        # استخراج المعاملات
        par_a = coefficients[0]
        par_b = coefficients[1]
        par_c = coefficients[2]
        par_d = coefficients[3]
        
        # عرض النتائج في الخانات السفلية
        entry_par_a.config(state='normal')
        entry_par_b.config(state='normal')
        entry_par_c.config(state='normal')
        entry_par_d.config(state='normal')
        
        entry_par_a.delete(0, tk.END)
        entry_par_b.delete(0, tk.END)
        entry_par_c.delete(0, tk.END)
        entry_par_d.delete(0, tk.END)
        
        # تنسيق الأرقام لتشبه دقة الجهاز
        entry_par_a.insert(0, f"{par_a:.2f}")
        entry_par_b.insert(0, f"{par_b:.2f}")
        entry_par_c.insert(0, f"{par_c:.2f}")
        entry_par_d.insert(0, f"{par_d:.4f}")
        
        entry_par_a.config(state='readonly')
        entry_par_b.config(state='readonly')
        entry_par_c.config(state='readonly')
        entry_par_d.config(state='readonly')

        # رسم الكيرف للتأكد
        plot_curve(x, y, coefficients)
        
    except Exception as e:
        messagebox.showerror("خطأ", f"حدث خطأ أثناء الحساب: {str(e)}")

def plot_curve(x_data, y_data, coeffs):
    # إنشاء نقاط وهمية لرسم المنحنى بسلاسة
    x_smooth = np.linspace(min(x_data)*0.8, max(x_data)*1.1, 100)
    # تطبيق المعادلة: y = Ax^3 + Bx^2 + Cx + D
    y_smooth = np.polyval(coeffs, x_smooth)
    
    plt.figure("Calibration Curve", figsize=(8, 5))
    plt.plot(x_smooth, y_smooth, 'b-', label='Calculated Curve (Cubic Fit)')
    plt.plot(x_data, y_data, 'ro', label='Standards Data', markersize=8)
    
    plt.title('Calibration Curve (Concentration vs Absorbance)')
    plt.xlabel('Absorbance')
    plt.ylabel('Concentration')
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.show()

# ==========================================
# تصميم واجهة المستخدم
# ==========================================
root = tk.Tk()
root.title("Analyzer Calibration Calculator")
root.geometry("600x600")
root.configure(padx=20, pady=20)

tk.Label(root, text="إدخال معطيات الـ Standards", font=("Arial", 16, "bold")).pack(pady=(0, 15))

# جدول الإدخال
frame_inputs = tk.Frame(root)
frame_inputs.pack(fill="x")

tk.Label(frame_inputs, text="Standard No.", font=("Arial", 10, "bold")).grid(row=0, column=0, padx=5, pady=5)
tk.Label(frame_inputs, text="Absorbance", font=("Arial", 10, "bold")).grid(row=0, column=1, padx=5, pady=5)
tk.Label(frame_inputs, text="Concentration", font=("Arial", 10, "bold")).grid(row=0, column=2, padx=5, pady=5)

conc_entries = []
abs_entries = []

for i in range(8):
    tk.Label(frame_inputs, text=str(i+1)).grid(row=i+1, column=0)
    
    abs_e = tk.Entry(frame_inputs, width=15, font=("Arial", 12), justify="center")
    abs_e.grid(row=i+1, column=1, padx=10, pady=3)
    abs_entries.append(abs_e)
    
    conc_e = tk.Entry(frame_inputs, width=15, font=("Arial", 12), justify="center")
    conc_e.grid(row=i+1, column=2, padx=10, pady=3)
    conc_entries.append(conc_e)

# زر الحساب
tk.Button(root, text="احسب المعاملات (Calculate)", font=("Arial", 12, "bold"), bg="#2196F3", fg="white", command=calculate_parameters).pack(pady=20, fill="x")

# عرض النتائج
frame_results = tk.LabelFrame(root, text=" النتائج النهائية (تُنقل للجهاز) ", font=("Arial", 12, "bold"), padx=10, pady=10)
frame_results.pack(fill="x")

labels = ["Par A", "Par B", "Par C", "Par D"]
entries = []

for i, label in enumerate(labels):
    tk.Label(frame_results, text=label, font=("Arial", 11, "bold")).grid(row=0, column=i, padx=10)
    e = tk.Entry(frame_results, width=12, font=("Arial", 12, "bold"), justify="center", state='readonly')
    e.grid(row=1, column=i, padx=10, pady=5)
    entries.append(e)

entry_par_a, entry_par_b, entry_par_c, entry_par_d = entries

root.mainloop()
