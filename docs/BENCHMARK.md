# Protocol: mug-v1

คำถาม: เมื่อใช้ ChatGPT Work เป็นตัวคิดเหมือนกัน การให้ Laya เลือกขั้นตอนบนเว็บช่วยลดข้อความที่ต้องส่งกลับ ChatGPT และเวลาใน workflow นี้หรือไม่?

ยังไม่มีคำตอบจากการทดลองครบชุด ห้ามกรอกตัวเลขคาดเดาลงเป็นผลจริง

## การทดลอง

1. ล็อก brief, prompt สองช็อต, ChatGPT model/effort, เครื่อง, Chrome, Flow model, resolution, aspect, duration, output count และบัญชีให้เหมือนกัน
2. ทำ pilot แยกก่อน หาก pilot เริ่มจาก Codex ให้ระบุ development และไม่นับเป็นหนึ่งในสองแขน
3. ทดลอง 3 คู่ในลำดับ `baseline-1 → hybrid-1 → hybrid-2 → baseline-2 → baseline-3 → hybrid-3` ใช้ ChatGPT Work ใหม่แต่ละรอบ เพื่อลดการจำวิธีจากรอบก่อน
4. baseline: ChatGPT เลือกทุก browser action; hybrid: ChatGPT วางแผน/เขียน prompt/แก้ปัญหา ส่วน Laya เลือก action หลายครั้งต่อการ delegate ทั้งคู่ใช้ตัวกรอก กด รอ ดาวน์โหลด และ FFmpeg ชุดเดียวกัน ห้ามทำ baseline ให้เสียเปรียบด้วยการเรียกโมเดลทุกครั้งที่รอ
5. 1 รอบ = วิดีโอสุดท้ายสองช็อต ช็อตละ 8s ผ่าน QC ภาพ/เสียง ไม่ใช่แค่ queued render
6. ไม่เลือกเฉพาะรอบสำเร็จ ทุก failed/blocked/retry ต้องอยู่ในหลักฐาน ถ้าชุดไม่ครบ/มีการ rerun เกินที่ลงทะเบียนไว้ ตัวรายงานจะไม่สร้างเปอร์เซ็นต์ชนะให้

ตัวอย่างราคา 10 เครดิต × 12 ช็อต = 120 เครดิต **ยังไม่รวม pilot แยก** ถ้าเพดานทั้งงานคือ 120 และ pilot ใช้ไปแล้ว 10 จะเหลือไม่พอสำหรับ 12 ช็อตใหม่ ต้องรายงานและรอการเพิ่มเพดานที่ผู้ใช้ระบุเอง อย่าแอบเปลี่ยน budget และอย่านับ development pilot เป็น ChatGPT run

## เวลา

- `elapsed_s`: นาฬิกา monotonic จากคำสั่ง `init` ถึง `finish` บนเครื่องเดียวกัน รวมโหลดโมเดล การแก้ปัญหา Flow wait ดาวน์โหลด ตัดต่อ และการหยุดรอผู้ใช้ที่อยู่ในช่วงนั้น
- เตรียม Python/โมเดล/บัญชี/brief/prompt ที่ตรึงไว้ก่อนช่วงวัด รายงาน setup เหล่านี้แยก ไม่ซ่อนการโหลดโมเดลที่เกิดซ้ำภายใน run
- นี่ไม่ใช่ server latency ของ ChatGPT และไม่ใช่เวลานับจากผู้ใช้กดส่งข้อความ หากต้องการค่านั้นให้จับเพิ่มจากวิดีโอหน้าจอพร้อมขอบเขตเวลาชัดเจน
- รายงาน median, min, max และจำนวน attempts/successes ของทั้งสองแขน พร้อมเวลา Laya, model load, Flow wait, download, assembly ที่สังเกตได้
- ห้ามลบเวลาที่ Laya ผิดหรือ ChatGPT ต้องรับช่วงเพียงเพื่อให้ผลดูดี

## Token

ChatGPT Work ไม่เปิด usage API ให้ repo นี้ จึงนับได้เพียง **ข้อความที่มองเห็นครั้งละหนึ่งครั้ง** ด้วย `tiktoken` encoding `o200k_base` ตามเวอร์ชันใน `uv.lock`:

- `visible_input_tokens_est`: user text + tool outputs ที่เก็บได้
- `visible_output_tokens_est`: assistant text + tool-call arguments ที่เก็บได้
- `visible_total_tokens_est`: ผลรวมของสองรายการ
- ไม่รวม hidden instructions, reasoning, image tokens, cached usage และการส่งประวัติซ้ำภายในระบบ จึงใช้เทียบปริมาณข้อความที่สังเกตได้ ไม่ใช่ยอดใช้ token จริงหรือเงินที่ประหยัด
- Laya รายงาน input token ของ tokenizer ตัวเอง แยกต่างหาก ห้ามบวกกับยอด ChatGPT แล้วเรียกยอดรวม billing

หลังจบแต่ละรอบเก็บ conversation export ที่เข้าถึงได้ลง `RUN/transcript.json` ตามแม่แบบ `examples/transcript.json` ระบุวิธีได้มาใน `source` ข้อความ assistant ที่มี tool call ต้องรวม arguments ถ้ามองเห็นด้วย ไม่ถอดสิ่งที่มองไม่เห็นขึ้นเอง

ตั้ง `complete:true` เฉพาะเมื่อมีข้อความและ tool payload ที่มองเห็นครบในช่วงที่กำหนด หาก export มีเพียง summary/ขาด tool messages ให้เก็บ `complete:false` ตัวเลขยังดูได้ แต่จะไม่เข้าเปอร์เซ็นต์เปรียบเทียบ หากไม่มีไฟล์ ค่า token เป็น `null` ไม่ใช่ศูนย์

```bash
uv run python flow.py report \
  runs/baseline-1 runs/hybrid-1 runs/hybrid-2 \
  runs/baseline-2 runs/baseline-3 runs/hybrid-3 \
  --output results/benchmark.json
```

ตรวจ `source`, `model_label` และชื่อ run ก่อนนำรายงานเผยแพร่ เพราะเป็นข้อความที่ผู้บันทึกใส่เอง อย่าใส่อีเมล path ส่วนตัว หรือ URL แชตส่วนตัวลงใน metadata เหล่านี้

## ข้อจำกัดของข้อสรุป

3 คู่มีขนาดเล็ก ผลสร้างวิดีโอสุ่มและคิว Flow เปลี่ยนได้ การประหยัดอาจมาจากการรวมหลายขั้นตอนใน local worker ร่วมกับ Laya จึงไม่ควรอ้างว่าเกิดจากขนาดโมเดลเพียงอย่างเดียว ผลเร็วขึ้นแต่ QC ตกไม่ใช่ความสำเร็จ และตัวเลขน้อยลงจาก transcript ที่เก็บไม่ครบไม่ใช่การประหยัด
