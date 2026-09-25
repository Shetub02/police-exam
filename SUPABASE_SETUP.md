# เปิดใช้ล็อกอิน Google และเก็บประวัติข้ามเครื่อง

ระบบเชื่อมกับโปรเจกต์ Supabase `police-practice` แล้ว และทดสอบ Google login กับฐานข้อมูลจริงสำเร็จเมื่อ 25 ก.ย. 2569
ค่าทดสอบปัจจุบันอนุญาต URL ในเครื่อง `http://127.0.0.1:8765/police_suppression_real_exam_by_subject.html` ต้องเพิ่ม URL เว็บจริงก่อนใช้จากมือถือหรือเครื่องอื่น

## 1. สร้างที่เก็บข้อมูล (ดำเนินการแล้ว)

1. เปิด https://supabase.com/dashboard แล้วสมัครหรือเข้าสู่ระบบด้วยบัญชีของคุณ
2. สร้าง New project ตั้งชื่อ เช่น police-practice เลือกรหัสผ่านฐานข้อมูลเองและเก็บไว้ส่วนตัว เลือกภูมิภาคใกล้ไทย
3. เมื่อพร้อม เปิด SQL Editor แล้ววางเนื้อหาทั้งหมดจาก `supabase/setup.sql` และกด Run
4. ในหน้า Connect / API Keys คัดลอก Project URL กับ Publishable key (หรือ legacy anon key) มาใส่ `police-sync-config.js`

อย่าใส่ database password, service_role หรือ secret key ในไฟล์เว็บไซต์หรือส่งมาในแชต ใช้เฉพาะ public/publishable key เท่านั้น

## 2. เปิด Google login (ดำเนินการแล้วสำหรับบัญชีทดสอบ)

1. ใน Supabase เปิด Authentication → Sign In / Providers → Google
2. เปิด Google Cloud Console (https://console.cloud.google.com/) สร้างโปรเจกต์และตั้ง OAuth consent screen พร้อมชื่อแอป อีเมลติดต่อ และ audience
3. สร้าง OAuth Client ID ชนิด Web application
4. Authorized JavaScript origins ใส่ต้นทางเว็บจริง เช่น `https://your-site.example`
5. Authorized redirect URIs ใส่ Callback URL ที่ Supabase แสดง เช่น `https://PROJECT.supabase.co/auth/v1/callback`
6. นำ Google Client ID และ Client Secret ไปใส่ในหน้าผู้ให้บริการ Google ของ Supabase แล้วเปิดใช้งาน (ไม่ใส่ Client Secret ในเว็บ)
7. หาก Google app ยังเป็น Testing เพิ่มอีเมลที่จะใช้ใน Test users
8. ใน Supabase Authentication → URL Configuration ตั้ง Site URL เป็นเว็บจริง และเพิ่ม Redirect URL แบบเต็มที่ลงท้าย `/police_suppression_real_exam_by_subject.html`

สำหรับทดสอบในเครื่อง เพิ่ม `http://127.0.0.1:8765/police_suppression_real_exam_by_subject.html` ใน Redirect URLs ด้วย เปิดผ่าน HTTP server ไม่ใช่ดับเบิลคลิกไฟล์

## 3. เปิดใช้กับ URL เว็บจริง

เพิ่ม URL เต็มของหน้า `police_suppression_real_exam_by_subject.html` ใน Supabase Authentication → URL Configuration ทั้ง Site URL และ Redirect URLs แล้วนำไฟล์เว็บที่แก้แล้วทั้งหมดขึ้นโฮสต์เดิม รวมไฟล์ police-sync*.js / police-sync.css จากนั้น:

1. เข้าสู่ระบบ Google บนคอม กด “นำประวัติเดิมของเครื่องเข้าบัญชี” หากต้องการย้ายข้อมูลเดิม (ระบบแยกข้อมูลเดิมไว้ ไม่ย้ายอัตโนมัติ)
2. รอคำว่า “ซิงก์แล้ว” เปิดเว็บเดียวกันบนมือถือและเข้าบัญชี Google เดียวกัน
3. ตรวจคะแนน ประวัติ ชุดที่ค้าง และข้อปักหมุดในชุดล่าสุด ลองตอบเพิ่มแล้วรอซิงก์ ตรวจอีกเครื่อง
4. ทดสอบตัดเน็ต ตอบเพิ่ม ต่อเน็ต และกดซิงก์ การเปลี่ยนข้อมูลสองเครื่องพร้อมกันต้องขึ้นตัวเลือกข้อมูล ไม่เขียนทับอัตโนมัติ
5. ถ้าจะให้บัญชีอื่นเข้าใช้ระหว่าง Google OAuth ยังเป็น Testing ต้องเพิ่มบัญชีนั้นใน Google Auth Platform → Audience → Test users ก่อน
6. เข้าบัญชี Google อีกบัญชี ต้องไม่เห็นข้อมูลของบัญชีแรก ตรวจ RLS โดยใช้ JWT คนละบัญชี: SELECT ของอีกบัญชีต้องได้ศูนย์แถว และ RPC ต้องเขียนได้เฉพาะเจ้าของ JWT

ผลทดสอบจริง: ล็อกอินผ่าน Google สำเร็จ เว็บแสดงสถานะ “ซิงก์แล้ว” และฐานข้อมูลมี history 3 รายการ, completed attempts 1 รายการ และ session ที่ทำค้าง 1 ชุด

## พฤติกรรมระบบ

- บันทึกในเครื่องทันที ซิงก์หลังเปลี่ยนคำตอบประมาณ 1 วินาที และตรวจข้อมูลเมื่อกลับมาหน้าเว็บ/ทุก 30 วินาทีขณะเปิดหน้า
- คะแนนและรายการชุดที่ทำแล้วเก็บ 30 ชุดล่าสุดตามระบบเดิม ชุดที่ค้างและปักหมุดเป็นของชุดล่าสุด
- เวลาข้อสอบยังนับตามเส้นตายเดิม หากต้องการพักต้องกดหยุดเวลาในหน้าแบบทดสอบ
- แต่ละบัญชีมีแคชแยกกัน ออกจากระบบจะกลับไปแสดงข้อมูลก่อนล็อกอิน สามารถฝึกแบบไม่ล็อกอินต่อได้
- เมื่อข้อมูลขัดกัน เลือกข้อมูลเครื่องนี้หรือออนไลน์ทั้งชุด ไม่มีการรวมคำตอบสองชุดโดยเดา ชุดที่ถูกแทนจะมีสำรองล่าสุดในเครื่อง กด “สำรองข้อมูล” เพื่อดาวน์โหลดรวมออกมาได้ (ยังไม่มีหน้ากู้คืนจากไฟล์)
- ใช้หนึ่งแท็บต่อเครื่องระหว่างทำข้อสอบ เพื่อลดการแก้ข้อมูลพร้อมกัน
- บัญชีและประวัติยังค้างในเบราว์เซอร์ได้ อย่าใช้ร่วมกับผู้อื่นโดยไม่ออกจากระบบ/ล้างข้อมูลไซต์
- หากโหลดบริการล็อกอินไม่ได้ ยังใช้ข้อมูลแบบไม่ล็อกอินในเครื่องได้ ไม่มีการอ้างว่าซิงก์สำเร็จ
- ยังต้องทดสอบ Google OAuth และสิทธิ์ฐานข้อมูลกับโปรเจกต์จริงก่อนถือว่าเปิดใช้งานออนไลน์ครบถ้วน

อ้างอิงการตั้งค่าทางการ:
- https://supabase.com/docs/guides/auth/social-login/auth-google
- https://supabase.com/docs/guides/auth/redirect-urls
- https://supabase.com/docs/guides/database/postgres/row-level-security
