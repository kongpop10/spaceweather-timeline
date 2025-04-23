# SpaceWeather App – คำอธิบายการทำงาน และวิธีการใช้งาน

SpaceWeather App ช่วยให้ผู้ใช้งานทั่วไปสามารถดูข้อมูล “สภาพอากาศอวกาศ” (Space Weather) ได้ง่าย ๆ โดยไม่ต้องรู้จักโค้ดหรือฐานข้อมูลเบื้องหลัง รายละเอียดสั้น ๆ มีดังนี้

## 1. ภาพรวมการทำงาน
- **scraper.py** ดึงข้อมูลดิบ (JSON) จากแหล่งออนไลน์
- **data_manager.py** หรือ **supabase_sync.py** ซิงก์หรือจัดเก็บข้อมูลลงไฟล์ในโฟลเดอร์ `data/`
- **app.py** (Streamlit) เปิดขึ้นมาเพื่อ:
  - โหลดข้อมูลจากไฟล์ JSON (หรือฐานข้อมูล Supabase ถ้าเชื่อมไว้)
  - ประมวลผลข้อมูล ออกรายงานสรุป กราฟสถิติ ไทม์ไลน์เหตุการณ์
  - แสดงผลผ่านโฟลเดอร์ `components/` (ตาราง, กราฟ, timeline)
- **session_state.py** เก็บสถานะผู้ใช้ เช่น วันที่ที่เลือก เพื่อไม่ให้รีเฟรชหาย

## 2. วิธีติดตั้งและใช้งาน
1. ติดตั้ง Python ≥ 3.8 และ Git
2. ดาวน์โหลดโค้ด:
   ```bash
   git clone https://github.com/kongpop10/spaceweather-timeline.git
   cd spaceweather-timeline
   ```
3. สร้าง Virtual Environment และติดตั้ง dependencies:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```
4. ตั้งค่าไฟล์ความลับ (ถ้าใช้ Supabase):
   - คัดลอก `secrets.toml.template` → `.streamlit/secrets.toml`
   - ใส่ API keys, URL ตามคู่มือในไฟล์
5. รันแอป:
   - ดับเบิ้ลคลิกไฟล์ `launch_spaceweather_app.bat`
   - หรือใน Terminal:
     ```bash
     streamlit run app.py
     ```
   - เปิดเบราว์เซอร์ไปที่ URL ที่แสดง (เช่น `http://localhost:8501`)

## 3. วิธีใช้งานเบื้องต้น
- เลือกวันที่จาก Date Picker เพื่อดูข้อมูลวันนั้น
- ใช้เมนู Sidebar:
  - **Timeline** : แสดงเหตุการณ์สำคัญ (CME, Auroras)
  - **Statistics** : กราฟดัชนี Geomagnetic และกราฟอนุภาค
  - **Admin** (ถ้ามีสิทธิ์) : อัปโหลดไฟล์ JSON ใหม่, ซิงก์ฐานข้อมูล
- คลิกเหตุการณ์ใน Timeline เพื่อดูรายละเอียดเวลาและความรุนแรง
- ซูมและเลื่อนดูกราฟได้ตามต้องการ

## 4. เคล็ดลับเพิ่มเติม
- โฟลเดอร์ `data/` เก็บไฟล์ JSON รายวัน ถ้าต้องการดูย้อนหลังหลายวัน ให้เลือกวันที่ย้อนหลัง
- ถ้าต้องการอัปเดตข้อมูลอัตโนมัติ ให้ตั้งงานประจำ (Cron Job หรือ Task Scheduler) รัน `scraper.py` ทุกคืน
- สร้าง Shortcut บน Windows ด้วย `create_shortcut.vbs` ตามคู่มือใน `SHORTCUT_INSTRUCTIONS.md`

---

SpaceWeather App ถูกออกแบบมาให้ผู้ที่สนใจสภาพอวกาศสามารถเข้าถึงข้อมูลสภาพอากาศอวกาศได้อย่างรวดเร็วและเข้าใจง่าย