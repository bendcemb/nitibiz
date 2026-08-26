import pandas as pd
import os
import sys

# รองรับการรันทั้งจาก root และจาก scripts/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


# 1. โหลดข้อมูล
mt_csv = os.path.join(config.DATA_DIR, 'mt_comp.csv')
sp_csv = os.path.join(config.DATA_DIR, 'sp_company.csv')

df_mt = pd.read_csv(mt_csv)
df_sp = pd.read_csv(sp_csv)

# 2. ฟังก์ชันสำหรับทำความสะอาดชื่อบริษัท (Data Cleaning)
def clean_company_name(name):
    if pd.isna(name):
        return ""
    name = str(name).strip()
    # ตัดคำทั่วไปออกเพื่อเน้นการจับคู่ชื่อหลัก
    words_to_remove = ["บริษัท", "จำกัด", "มหาชน", "(มหาชน)", "บมจ.", "บจก.", "หจก.", " ", "."]
    for word in words_to_remove:
        name = name.replace(word, "")
    return name.lower()

# สร้างคอลัมน์ชื่อบริษัทที่ทำความสะอาดแล้วสำหรับการเปรียบเทียบ
df_mt['clean_name'] = df_mt['company'].apply(clean_company_name)
df_sp['clean_name'] = df_sp['Company'].apply(clean_company_name)

# 3. สร้าง Dictionary สำหรับ Mapping (ชื่อที่ทำความสะอาดแล้ว -> company_id)
# เก็บเฉพาะรายการที่มีชื่อไม่ว่างเปล่า
mt_dict = dict(zip(df_mt[df_mt['clean_name'] != '']['clean_name'], df_mt[df_mt['clean_name'] != '']['company_id']))

# 4. ฟังก์ชันสำหรับการจับคู่
def find_matching_id(row):
    # หากมี new_company_id อยู่แล้ว ให้ใช้ค่าเดิม
    if pd.notna(row['new_company_id']) and str(row['new_company_id']).strip() != '' and str(row['new_company_id']).strip() != 'NULL':
        return row['new_company_id']
    
    clean_sp_name = row['clean_name']
    if clean_sp_name in mt_dict:
        return mt_dict[clean_sp_name]
    
    # หากต้องการเพิ่มการจับคู่แบบเทียบคำบางส่วน (Substring) สามารถเพิ่มลอจิกตรงนี้ได้
    for mt_name, mt_id in mt_dict.items():
        if len(clean_sp_name) > 3 and len(mt_name) > 3:
            if clean_sp_name in mt_name or mt_name in clean_sp_name:
                return mt_id
                
    return row['new_company_id'] # ไม่พบข้อมูลจับคู่

# 5. ทำการอัปเดตข้อมูล
df_sp['new_company_id'] = df_sp.apply(find_matching_id, axis=1)

# ลบคอลัมน์ชั่วคราวออก
df_sp = df_sp.drop(columns=['clean_name'])

# 6. บันทึกผลลัพธ์เป็นไฟล์ CSV ใหม่
out_path = os.path.join(config.DATA_DIR, 'sp_company_updated.csv')
df_sp.to_csv(out_path, index=False, encoding='utf-8-sig')
print(f"สร้างไฟล์ {out_path} เรียบร้อยแล้ว!")