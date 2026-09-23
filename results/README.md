# ผลที่ตรวจได้จริง

สถานะ ณ 23 กันยายน 2026: **ยังไม่มี benchmark ChatGPT Work ครบ 3 คู่ / 6 คลิป** จึงยังไม่รายงานเปอร์เซ็นต์ประหยัด token หรือเวลา

| การตรวจ | ผล | ขอบเขตหลักฐาน |
|---|---|---|
| Unit + Chrome fixture + FFmpeg | ผ่าน (ดูคำสั่งตรวจใน README) | HTML และสัญญาณภาพ/เสียงทดสอบในเครื่อง ไม่ใช้เครดิต Flow |
| Laya v10 บน CPU, โจทย์กรอกแล้วกดที่มี Create พร้อมใช้ | ไม่ผ่าน | เลือก CLICK ก่อนกรอก; [JSON](model-compound-check.json) |
| Laya v10 บน CPU, โจทย์กรอกช่องว่างอย่างเดียว | ผ่าน | เลือก TYPE_TEXT target 0; [JSON](model-fill-check.json) |
| Laya กรอก prompt บน Flow จริง | ผ่าน | local worker เลือก TYPE_TEXT และตรวจค่าช่องหลังกรอก |
| การสร้าง/ดาวน์โหลด Flow pilot | ผ่านทางเทคนิค | 8.0s, 720×1280, มี audio stream; ยังไม่ผ่าน QC เสียงไทย/การดูครบทุกเฟรม |
| ChatGPT Work baseline-1 | ได้ไฟล์ 16s; รอ QC | 616.768s, 20 เครดิต; [JSON](baseline-1.json) |
| ChatGPT Work baseline vs hybrid | ยังไม่ครบ | baseline 1 รอบ; hybrid ยังไม่มี จึงไม่มีเปอร์เซ็นต์เปรียบเทียบ |

เครื่องตรวจ: macOS 26.4, arm64, RAM 16 GB, Python 3.12.13; Laya 0.3.6, PyTorch 2.14.0, Transformers 4.57.6, Playwright 1.63.0, tiktoken 0.14.0 โมเดล `cklxx/laya-browser/v10` revision ตาม JSON

ตัวอย่างการตัดสินใจจำลองใช้เวลาประมาณ 0.405 และ 0.557 วินาที/ครั้งบน CPU ข้างต้น **ไม่ใช่เวลาเฉลี่ยจาก benchmark** การโหลดโมเดลประมาณ 21.68 และ 25.00 วินาทีในสองครั้งนี้อยู่ใน JSON ด้วย ห้ามตัด overhead นี้ออกเมื่อตีความความเร็วจริง

การทดสอบและตั้งค่าใน task พัฒนาระบุ `brain=codex-development` จึงไม่นับเป็น ChatGPT Work แม้ UI/สิทธิ์บัญชีจะคล้ายกัน ไม่มีการเผยแพร่ raw transcript, profile หรือภาพบัญชี

[รายงาน pilot จริง](development-pilot.json): Laya ตัดสินใจสองครั้ง ใช้ input ของ tokenizer Laya รวม 2,143 tokens, inference รวม 1.986s, โหลดโมเดลสองครั้งรวม 49.49s จองเครดิต 10 มี action error หนึ่งครั้งขณะตรวจและแก้การรองรับเส้นทางหน้าวิดีโอ ข้อผิดพลาดนี้ยังอยู่ในรายงาน

เวลาทั้ง run ประมาณ 1,916.9s **รวมเวลาที่เขียน/แก้โค้ดและรอผู้ใช้ล็อกอิน** จึงใช้เปรียบเทียบความเร็วไม่ได้ `visible_*_tokens_est` ของ ChatGPT และเปอร์เซ็นต์เปรียบเทียบยังเป็น null ไม่ใช่ศูนย์

Fresh code review พบและแก้: ไม่ให้คลิปเก่าผ่านเงื่อนไขงานใหม่, ต้องมี Laya execution evidence ก่อนเปรียบเทียบ, และบันทึก action errors ของทั้งสองแขนอย่างเท่ากัน

ตรวจ frontmatter และ UI metadata ของ Skill โดยอ่าน YAML จริงแล้ว ตัว validator ที่มากับ skill-creator หายจากตำแหน่งที่ติดตั้งระหว่าง session จึงไม่ได้อ้างว่ารัน validator ตัวนั้นสำเร็จ

## Baseline แรก — 6 Astra / xhigh

ผู้ใช้ยืนยันว่าเปิด ChatGPT Desktop → Work locally; local runtime metadata ยืนยัน `gpt-6-astra` / `xhigh` และ backing kind เป็น `codex` เก็บแหล่งหลักฐานแยกกัน ไม่ใช้ชื่อภายในอย่างเดียวตัดสินโหมด UI

ได้คลิป 16.0s, 720×1280 และมี audio stream ใช้เวลา 616.768s (10 นาที 17 วินาที), 19 browser steps, 20 เครดิต, ไม่มี Laya decisions หรือ action errors สถานะ `blocked` หมายถึงรอผู้ใช้ดู/ฟังครบเพื่อยืนยัน QC ภาพตัวอย่าง 32 เฟรมยังไม่พิสูจน์เสียงไทยหรือการเคลื่อนไหวทั้งหมด

| มาตรวัด | Input | Output | รวม |
|---|---:|---:|---:|
| Visible-text estimate, นับข้อความที่เก็บได้ครั้งเดียว | 16,872 | 9,325 | 26,197 |
| Host-reported token usage, 35 response records | 4,884,089 | 13,866 | 4,897,955 |

**สองแถวนี้เป็นคนละมาตรวัด ห้ามเทียบตรง ๆ หรืออ่านเป็นยอดเงิน** แถว host รวมการส่งบริบทซ้ำ โดย input 4,844,544 เป็น cached tokens อยู่ในยอด input แล้ว (uncached input 39,545); reasoning 4,193 อยู่ในยอด output แล้ว รอบแรกมีบริบทจากการเตรียมงานติดมาด้วย จึงเป็นตัวแปรที่กระทบการเปรียบเทียบ

ตัวอ่าน [capture_rollout.py](../capture_rollout.py) เลือกตาม timestamp ช่วง init–finish และตัด response ID ซ้ำ สถิตินี้ยังไม่ได้ตรวจเทียบกับบิลหรือ usage API ส่วน transcript ยังคง `complete:false` เพราะยังไม่ยืนยันความครบของ log จึงไม่คำนวณเปอร์เซ็นต์ชนะ ผลนี้ไม่ใช่ benchmark ครบชุดและไม่นำไปอ้างว่าประหยัดแล้ว
