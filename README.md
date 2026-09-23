# Laya + ChatGPT → Google Flow

ให้ **ChatGPT Desktop โหมด Work locally เป็นตัวคิด** และให้ **Laya v10 ขนาด 421M ในเครื่องเลือกการกดเว็บ** เพื่อทำคลิปสินค้าใน Google Flow แล้วดาวน์โหลดมาต่อเป็นคลิป 16 วินาที

ได้แรงบันดาลใจจาก [ChatGPT × Google Flow ทำหนังสั้นจีนแนวตั้ง](https://youtu.be/7ZbYX93n4GY) เปลี่ยนส่วนลงมือกดเป็น Laya โดยไม่ใช้ Codex เป็นตัวคิด ไม่เรียก OpenAI API ไม่ดึงคำตอบจากหน้าเว็บ ChatGPT และไม่โพสต์คลิปอัตโนมัติ

**สถานะ: รุ่นทดลอง — คู่แรกสร้างคลิป 16 วินาทีสำเร็จทั้ง ChatGPT และ Laya + ChatGPT ผู้ใช้ตรวจภาพ/เสียงผ่านแล้วทั้งคู่ ยังเหลืออีก 2 คู่จากแผน 6 คลิป** ผลตรวจและตัวเลขที่วัดได้อยู่ใน [results](results/README.md) ยังสรุปการประหยัด token หรือเวลาไม่ได้ เพราะข้อมูลยังไม่ครบและวิธีนำทางหน้าเว็บต่างกันบางส่วน

```text
ผู้ใช้ → ChatGPT Work locally → brief / prompt / แก้ปัญหา
                              ↓ เรียกคำสั่งในเครื่อง
                    Laya v10 เลือก operation + target
                              ↓
                     Chrome → Google Flow
                              ↓
                  ดาวน์โหลด 2 ช็อต → FFmpeg → final.mp4
```

Laya เป็นโมเดลเลือกคำตอบ ไม่ใช่โมเดลเขียนบท: ChatGPT ส่งข้อความที่จะกรอกให้ แล้ว Laya เลือกช่อง/ปุ่มจากหน้าปัจจุบัน หากทำต่อไม่ได้จะส่ง `needs_reasoning` กลับให้ ChatGPT แก้

## เริ่มใช้บน Mac

ต้องมี ChatGPT Desktop ที่ใช้ **Work locally + คำสั่งในเครื่อง** ได้, Google Chrome, บัญชี Flow/เครดิต, [uv](https://docs.astral.sh/uv/getting-started/installation/) และ FFmpeg โปรแกรมนี้ทดสอบบน Apple Silicon, RAM 16 GB ใช้ CPU inference ไม่ต้องมี GPU NVIDIA

```bash
git clone https://github.com/Boom-Vitt/laya-chatgpt-flow.git
cd laya-chatgpt-flow
uv sync --locked
uv run python flow.py doctor
sh scripts/open-chrome-mac.sh
```

ล็อกอิน Google ใน **Chrome หน้าต่างทดสอบ** แล้วเปิดโปรเจกต์ Flow ที่จะใช้ โปรไฟล์นี้แยกจาก Chrome ประจำวัน และรับคำสั่งบน `127.0.0.1:9223` เท่านั้น ห้ามนำโฟลเดอร์ `runs/browser-profile` ไปแชร์

ใน ChatGPT Desktop เลือก **Work locally** และโฟลเดอร์ repo นี้ แล้วพิมพ์:

> อ่าน `.agents/skills/laya-chatgpt-flow/SKILL.md` แล้วใช้ Laya + ChatGPT ทำคลิปสินค้าตัวอย่างจาก `examples/product.md` ให้จบที่ไฟล์วิดีโอ ตรวจรุ่นและราคา Flow ปัจจุบันก่อนสร้าง จำกัดเครดิตรวม 120 ไม่โพสต์คลิป และรายงานทุกครั้งที่ต้องให้ ChatGPT รับช่วงแทน Laya

ถ้า Skill ปรากฏในเมนู `@` สามารถเลือก **Laya + ChatGPT Flow** ได้ เอกสารทางการรองรับ standalone skills ใน Desktop แต่การค้นหาโฟลเดอร์/ความสามารถขึ้นกับเวอร์ชันและบัญชี การสั่งให้อ่านไฟล์ด้านบนเป็นทางเข้าโดยตรง ไม่ต้องติดตั้ง MCP server หรือ API key

ดู [วิธีใช้คำสั่งและตัวอย่าง](docs/WORKFLOW.md) และ [วิธีวัดผลอย่างเทียบกันได้](docs/BENCHMARK.md)

## ขอบเขตและค่าใช้จ่าย

- โมเดล Laya ดาวน์โหลดจาก Hugging Face แล้วประมวลผลในเครื่องฟรี ไม่ใช้ hosted inference; ครั้งแรกใช้พื้นที่และเวลาดาวน์โหลด
- ChatGPT ใช้สิทธิ์จากบัญชี/แผนของคุณ ส่วน Google Flow ใช้เครดิตของ Flow จึง **ไม่ใช่ระบบทำวิดีโอฟรีทั้งหมด**
- เครดิต Flow เป็นโควตาสร้างงาน ไม่ใช่หน่วยบาท ส่วน `--cap` เป็นเพดานที่อนุญาตให้สคริปต์ใช้ ไม่ใช่ยอดคงเหลือในบัญชี ต้องตรวจยอดจริงด้วย [รายละเอียดโควตาและเครดิต](https://support.google.com/flow/answer/16526234?hl=en)
- ตัวอย่างใช้ Veo 3.1 Lite, 720p, 9:16, 8s, x1 ราคาที่ตรวจใน UI วันที่ 23 ก.ย. 2026 คือ 10 เครดิต/ช็อต ต้องตรวจใหม่ก่อนสร้าง
- 6 คลิป × 2 ช็อต = 12 renders หรืออย่างน้อย 120 เครดิตที่ราคานี้ การทดลองเพิ่ม/งานล้มเหลวอาจใช้เครดิตเพิ่ม ห้ามเพิ่มเพดานเอง
- ไม่มีการซื้อเครดิต ลบโปรเจกต์ เผยแพร่คลิป หรือปักตะกร้า TikTok โพสต์และตรวจรายละเอียดสินค้าด้วยตัวเอง
- รุ่นแรกเป็น text-to-video ของสินค้าสมมติ ยังไม่มีขั้นตอนอัปโหลดภาพสินค้าจริง ต้องตรวจความคงที่ของสินค้าในคลิปเอง
- Laya v10 อาจเลือกผิดและบาง task ต้องส่งกลับ ChatGPT ค่าความมั่นใจของ checkpoint มีคำเตือน calibration จึงไม่ใช้ confidence เป็นหลักฐานว่างานถูกต้อง
- UI ของ Flow เปลี่ยนได้ หากตัวรันหา control ไม่พบจะหยุดและส่งเหตุผลกลับ ไม่รับประกันทุกบัญชี/ทุกหน้า

## ตรวจตัวรันโดยไม่ใช้เครดิต

```bash
uv run python -m unittest discover -s tests -v
RUN_BROWSER_CHECKS=1 uv run python -m unittest discover -s tests -v
RUN_BROWSER_CHECKS=1 RUN_MEDIA_CHECKS=1 uv run python -m unittest discover -s tests -v
uv run ruff check .
uv run python flow.py model-check
```

คำสั่ง browser check ใช้ Chrome ใหม่แบบ headless กับ HTML ในเครื่อง ไม่มีการเรียกสร้างคลิปจริง ส่วน `model-check` โหลดโมเดลจริงและแสดงว่าการตัดสินใจในโจทย์จำลองผ่านหรือไม่ ผลโมเดลผิดไม่ได้ถูกซ่อนหรือแก้ด้วยคำตอบตายตัว

ไฟล์ `runs/` เก็บ transcript, ภาพหน้าจอ, event log, เครดิตที่จองและวิดีโอเฉพาะเครื่อง ไม่อยู่ใน Git ตัวรายงานส่งออกเฉพาะตัวเลขรวมและ provenance ที่ผ่านการตรวจแล้ว

โค้ด MIT; โมเดลและไลบรารี Laya เป็น Apache-2.0 ดู [แหล่งที่มาและสิทธิ์](THIRD_PARTY_NOTICES.md)
