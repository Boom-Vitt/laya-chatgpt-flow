# ใช้จาก ChatGPT Work locally

เปิด repo นี้เป็น working folder ให้ ChatGPT อ่าน Skill ก่อนทำงาน การใช้ ChatGPT หน้าเว็บหรือ Work in cloud ไม่ทำให้เรียกไฟล์/Chrome บนเครื่องนี้ได้เอง งานพัฒนาที่รันจาก Codex ต้องระบุ `--brain codex-development` และจะไม่ถูกรวมในผลเทียบ

ติดตั้งเครื่องมือก่อนตาม [คู่มือ Windows / Linux / macOS](INSTALL.md) คำสั่งด้านล่างใช้ได้ทั้ง PowerShell และ Terminal; ตัวอย่าง JSON ให้บันทึกเป็น UTF-8

## 1. เปิด Chrome และตรวจ Flow

```bash
uv run python flow.py open-browser
```

ล็อกอิน Google ด้วยตัวเอง เปิด/สร้างโปรเจกต์ Flow ใหม่ แล้วคัด URL จริง อย่าใช้ URL ตัวอย่างด้านล่างตรง ๆ อย่าย้าย cookies จาก Chrome ประจำวัน

ตรวจใน UI: Agent ปิด, Video/Frames, Veo 3.1 Lite, 9:16, 720p, 8s, x1 และเครดิตที่แสดง การตั้งค่าไม่ถูกต้องอาจใช้เครดิตมากกว่าที่บันทึก ระบบอาศัยการตรวจ UI โดย ChatGPT/ผู้ใช้ก่อนส่งงาน

```bash
uv run python flow.py init runs/hybrid-1 --url 'https://flow.google.com/project/REAL-PROJECT-ID' --arm hybrid --brain chatgpt-work-local --model-label 'EXACT MODEL AND EFFORT' --pair 1 --cap 20 --budget runs/my-budget.sqlite
uv run python flow.py observe runs/hybrid-1
```

หากโปรเจกต์ยังไม่เปิดในหน้าต่างทดสอบ ใช้ `uv run python flow.py open-project runs/hybrid-1` เพื่อเปิด URL ที่ระบุไว้อย่างเจาะจง โปรแกรมจะไม่สร้างโปรเจกต์ใหม่หรือจัดการล็อกอินให้เอง

ตั้ง `--cap` ตามเครดิตที่ผู้ใช้อนุญาตจริง; ตัวอย่าง 20 เครดิตเป็นเพดานหนึ่งคลิป ไม่ใช่ราคาที่รับประกัน ใช้ชื่อรอบใหม่เพื่อไม่ชนกับหลักฐานที่มีอยู่

ใช้ `--arm baseline` สำหรับ ChatGPT ตัดสินใจเอง; `--arm pilot` สำหรับทดสอบการเชื่อม การเริ่ม run เดิมซ้ำจะไม่เขียนทับหลักฐาน ทุก run ในการเปรียบเทียบต้องใช้ไฟล์ budget เดียวกัน

## 2. ส่งงานให้ Laya

อ่าน `observe` เพื่อใช้ **ชื่อ control จริง** ห้ามเดาตัวเลข target ตัวอย่าง `examples/fill-task.json` และ `submit-task.json` เป็นแม่แบบ ต้องตรวจชื่อและแทนที่หลักฐานราคาใน `submit.evidence` ก่อนใช้

```bash
uv run python flow.py delegate runs/hybrid-1 --task runs/shot-1.json
```

Task ที่กรอกและกดได้ในครั้งเดียวประกอบด้วย:

```json
{
  "id": "shot-1",
  "goal": "Fill the Video prompt field with supplied text, then click Start generation once.",
  "click": ["Start generation"],
  "type": {"Video prompt": "THE EXACT COMPLETE VIDEO PROMPT"},
  "submit": {
    "name": "Start generation",
    "credits": 10,
    "evidence": "Verified current UI: Veo 3.1 Lite, 720p, 8s, 9:16, x1, 10 credits"
  },
  "done_video": 1
}
```

`submitted` หมายถึงกดส่งแล้ว **ยังไม่ใช่คลิปเสร็จ** `task_complete` หมายถึงผ่านเงื่อนไขย่อยที่ระบุ `needs_reasoning` ให้ ChatGPT อ่านหน้าปัจจุบันและแก้ปัญหา ไม่ใช่สั่งซ้ำไปเรื่อย ๆ

เมื่อ Laya ส่งงานแล้ว ตัวรันจะคืนการควบคุมให้ ChatGPT ใช้การรอแบบธรรมดาแทนการให้โมเดลตัดสินใจทุกวินาที:

```bash
uv run python flow.py wait-video runs/hybrid-1 --after 0 --seconds 45
```

สำหรับช็อตถัดไปให้ `--after` เท่ากับจำนวนการ์ดวิดีโอที่สร้างเสร็จก่อนกดส่ง (`video_tiles_before_submit`) อยู่หน้า All media ของโปรเจกต์เดิมโดยไม่เปลี่ยนตัวกรอง ตัวรันคืน `result_visible` เมื่อเห็นการ์ดใหม่ จากนั้นต้องเปิดและดาวน์โหลดเพื่อตรวจไฟล์ การ์ดภาพตัวอย่างยังไม่ใช่หลักฐานว่าได้ไฟล์แล้ว

## 3. ChatGPT baseline หรือรับช่วงแก้ปัญหา

ใช้ browser primitive เดียวกัน แต่ ChatGPT เลือก `operation` และ `target` เอง:

```bash
uv run python flow.py observe runs/baseline-1
# บันทึก action.json จาก snapshot ล่าสุด เช่น:
# {"snapshot":"ACTUAL_HASH","operation":"TYPE_TEXT","target":"ACTUAL_ID"}
uv run python flow.py step runs/baseline-1 --task runs/shot-1.json --action runs/action.json
```

รองรับ `CLICK`, `TYPE_TEXT`, `WAIT`, `DONE`, `BLOCKED` เท่านั้น ข้อความที่กรอกมาจาก task; Laya ไม่สร้าง/เปลี่ยนข้อความเอง ปุ่มเสี่ยง เช่น Delete, Publish, Buy, Share ถูกปฏิเสธ และส่งงานไม่ได้หากข้อความที่จำเป็นยังไม่ตรง

หากต้องใช้ native browser tools เพื่อเปิดเมนู/เลื่อนหาช่อง ให้เก็บขั้นตอนนั้นใน transcript ด้วย **ห้ามกดสร้างผ่าน native tool เพื่อข้ามบัญชีเครดิต** ตัวรันจองเครดิตก่อนกดและไม่คืนอัตโนมัติหากเกิด crash หรือไม่แน่ใจว่าส่งสำเร็จหรือไม่

รุ่นนี้ไม่มีการแก้ไข/reset budget ผ่าน CLI หากใช้หมดให้หยุดและรายงาน อย่าลบฐานข้อมูลหรือเปลี่ยนไฟล์ budget เพื่อหลบเพดาน

## 4. ดาวน์โหลดและต่อคลิป

เปิดเมนูดาวน์โหลดของช็อตที่ถูกต้องจาก UI แล้วใช้ชื่อ original/720p ที่ `observe` พบ ต้องมีปุ่มตรงชื่อนั้นเพียงหนึ่งปุ่ม:

```bash
uv run python flow.py download runs/hybrid-1 --name 'EXACT ORIGINAL DOWNLOAD LABEL' --output shot-1.mp4
uv run python flow.py download runs/hybrid-1 --name 'EXACT ORIGINAL DOWNLOAD LABEL' --output shot-2.mp4
uv run python flow.py assemble runs/hybrid-1 runs/hybrid-1/shot-1.mp4 runs/hybrid-1/shot-2.mp4
```

ตัวต่อคลิปตรวจทั้งสองช็อตเป็น 8 วินาที แนวตั้ง 9:16 และมี audio stream แล้วตรวจไฟล์ปลายทางอีกครั้ง ไม่มีการลบลายน้ำหรือเขียนทับ `final.mp4` เดิม

ดูและฟังไฟล์ครบทั้งคลิป แล้วคัด `examples/qc.json` ไปกรอกตามจริง:

```bash
uv run python flow.py finish runs/hybrid-1 --status passed --qc runs/review.json
# หากไม่สำเร็จ:
uv run python flow.py finish runs/hybrid-1 --status failed
```

pilot แบบหนึ่งช็อตใช้ `uv run python flow.py finish runs/pilot --status pilot_downloaded` หลังได้ `shot-1.mp4` 8 วินาที สถานะนี้ยืนยันรูปแบบไฟล์เท่านั้น ไม่ได้ยืนยัน QC เสียงและไม่นับเป็นรอบ benchmark ที่ passed

## ปัญหาที่พบได้

- `404 /json/version`: Chrome พอร์ตนั้นไม่ใช่ DevTools ที่เปิดใช้งาน ใช้หน้าต่างจาก launcher ที่พอร์ต 9223 อย่าเปลี่ยน Chrome ปกติให้เปิด debugger
- `open exactly one matching...`: เปิด URL โปรเจกต์ที่ระบุในหน้าต่างทดสอบเพียงแท็บเดียว
- `stale snapshot`: หน้าเปลี่ยนแล้ว ให้ observe ใหม่และเลือก target ใหม่
- `already reserved`: อาจส่งไปแล้ว ตรวจงานใน Flow ก่อน ห้ามสุ่ม task ID ใหม่เพื่อส่งซ้ำ
- `needs_reasoning`: โมเดลไม่ก้าวหน้าหรือเงื่อนไขไม่ตรง ให้ ChatGPT แก้/ยุติรอบ
- ชื่อ control ว่าง/หลายปุ่มตรงกัน: เปิดหน้า/เมนูให้ตรงบริบทก่อน รุ่นนี้ไม่เดาพิกัดและไม่เข้าถึง API ภายในของ Flow
- คำเตือน Laya calibration: checkpoint มี temperature สูงกว่าเพดานเล็กน้อย ไลบรารี clamp ค่านั้น ผลความมั่นใจจึงไม่ใช่เกณฑ์ตัดสินความสำเร็จ

ปิดหน้าต่าง Chrome ทดสอบเมื่อจบงานเพื่อลดเวลาที่ debugger เปิดอยู่ ให้เก็บ profile ไว้เฉพาะเครื่องเพื่อไม่ต้องล็อกอินใหม่; อย่าใส่บัญชีอื่นที่ไม่เกี่ยวกับการทดสอบใน profile นี้
