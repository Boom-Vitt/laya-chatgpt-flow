# ติดตั้งบน Windows, Linux และ macOS

ใช้ **ChatGPT Desktop → Work locally เป็นตัวคิด** และ Python/Laya บน CPU เป็นตัวรัน ไม่ต้องใช้ model API key หรือการ์ดจอแยก ต้องมีบัญชี ChatGPT ที่ใช้คำสั่งในเครื่องได้ และบัญชี Google Flow พร้อมเครดิตของตัวเอง

## ระบบและขอบเขตการตรวจ

| เครื่อง | แนวทางติดตั้ง | การตรวจตัวรัน |
|:---|:---|:---|
| Windows x64 | PowerShell บน Windows โดยตรง | GitHub Actions: Windows Server 2025 x64 |
| Linux x64 แบบ Desktop | เริ่มจาก Ubuntu 24.04 LTS | GitHub Actions: Ubuntu 24.04 x64 |
| macOS Apple Silicon | Terminal | GitHub Actions: macOS 15 ARM64 และเครื่องพัฒนา macOS 26.4 |

ดูสถานะจริงใน [การทดสอบทั้งสามระบบ](https://github.com/Boom-Vitt/laya-chatgpt-flow/actions/workflows/compatibility.yml) ซึ่งตรวจการติดตั้งจาก lockfile, import Laya/PyTorch, คำนวณ CPU, เปิด Chrome/เชื่อม CDP, ไฟล์ภาษาไทย, ล็อกข้าม process, บัญชีเครดิต และต่อคลิปด้วย FFmpeg โดยไม่ใช้บัญชีหรือเครดิต Flow

**คลิป Flow จริงและ benchmark ใน README มาจาก Mac Apple Silicon เท่านั้น** CI ไม่ได้ล็อกอิน ChatGPT/Google, โหลด checkpoint เพื่อวัดความแม่นยำ หรือสร้างคลิปจริงบน Windows/Linux จึงยังไม่มีผลความเร็วหรือ QC ของ Flow บนสองระบบนั้น

- แนะนำ RAM 16 GB ตามเครื่องที่ใช้สาธิต ไม่ใช่ผลพิสูจน์ว่าต้องมีขั้นต่ำเท่านี้ เตรียมพื้นที่หลาย GB สำหรับ Python, PyTorch, โมเดล และวิดีโอ
- `uv` จัดการ Python 3.12 ให้ตามโปรเจกต์ ไม่ต้องติดตั้ง Python แยกหรือ activate venv เอง
- Linux ต้องมีหน้าจอ Desktop สำหรับล็อกอินและตรวจคลิป รุ่นแอป ChatGPT สำหรับ Linux ยังเป็น preview และมีรายชื่อ distro ที่รองรับตาม [เอกสาร OpenAI](https://learn.chatgpt.com/docs/linux/linux-app)
- ตัวรันควบคุม Chrome ผ่าน Playwright/CDP ไม่ได้ใช้ native Computer Use ของแอป Linux หากหน้า Flow บางส่วนเกินคำสั่งที่รองรับ ให้ผู้ใช้ตั้งค่าหรือเปิดเมนูใน Chrome แล้วดำเนินงานต่อ
- Linux ARM64, Windows ARM64 และ Mac Intel ยังไม่อยู่ในชุดทดสอบนี้; dependency ที่ล็อกไว้บางตัวไม่มี wheel สำหรับทุกสถาปัตยกรรม โดยเฉพาะ PyTorch 2.14 บน Mac Intel ไม่ควรถือว่าติดตั้งได้เพียงเพราะมี Python
- Android/iOS ไม่ใช่เครื่องรันของเวิร์กโฟลว์นี้ และยังไม่มีตัวติดตั้งแบบคลิกเดียว

## Windows — PowerShell

ติดตั้ง [ChatGPT Desktop สำหรับ Windows](https://learn.chatgpt.com/docs/windows/windows-app) แล้วเปิด PowerShell ติดตั้งส่วนที่ยังไม่มี:

```powershell
winget install --id Git.Git --exact
winget install --id astral-sh.uv --exact
winget install --id Google.Chrome --exact
winget install --id Gyan.FFmpeg --exact
```

ปิดแล้วเปิด PowerShell และ ChatGPT ใหม่เพื่อรับ PATH ที่อัปเดต เก็บ repo บนไดรฟ์ Windows ปกติ และให้ ChatGPT รันคำสั่งใน Windows เช่นกัน ไม่จำเป็นต้องใช้ WSL หรือ Docker; คู่มือนี้ไม่ครอบคลุมการใช้ Python ใน WSL ต่อไปยัง Chrome ฝั่ง Windows

หากไม่มี `winget` ใช้ตัวติดตั้งจาก [Git](https://git-scm.com/install/windows), [uv](https://docs.astral.sh/uv/getting-started/installation/), [Chrome](https://www.google.com/chrome/) และ [FFmpeg](https://ffmpeg.org/download.html#build-windows) โดยให้ทั้ง `ffmpeg` และ `ffprobe` อยู่ใน PATH

## Linux — Ubuntu 24.04 Desktop

ติดตั้ง ChatGPT ตาม [คู่มือ Linux ของ OpenAI](https://learn.chatgpt.com/docs/linux/linux-app) และ [Google Chrome](https://www.google.com/chrome/) รุ่น Linux จากนั้น:

```bash
sudo apt update
sudo apt install -y git ffmpeg curl
curl -LsSf https://astral.sh/uv/install.sh | sh
```

เปิด Terminal ใหม่ให้พบ `uv` ส่วน Debian/Fedora/Arch ให้เลือกแพ็กเกจ Git, FFmpeg และ Chrome ที่ตรงกับ distro ตัว launcher ค้นหา Chromium ได้ด้วย แต่การล็อกอิน Google/Flow ผ่าน Chromium ยังไม่ได้ตรวจรับ

## macOS — Apple Silicon

ติดตั้ง [ChatGPT Desktop](https://learn.chatgpt.com/docs/quickstart?setup=app), [Google Chrome](https://www.google.com/chrome/) และ [Homebrew](https://brew.sh/) หากยังไม่มี จากนั้น:

```bash
brew install git uv ffmpeg
```

## ขั้นตอนร่วม — ใช้คำสั่งเดียวกันทั้งสามระบบ

รันทีละบรรทัดใน PowerShell หรือ Terminal:

```text
git clone https://github.com/Boom-Vitt/laya-chatgpt-flow.git
cd laya-chatgpt-flow
uv sync --locked
uv run python flow.py doctor
uv run python flow.py open-browser
```

`doctor` ควรแสดง path ของ Chrome, `ffmpeg: true`, `ffprobe: true` และเวอร์ชัน package ครบ `open-browser` จะเปิดโปรไฟล์แยกใน `runs/browser-profile` พร้อม debugger ที่ `127.0.0.1:9223` เท่านั้น

ล็อกอิน Google ในหน้าต่างนี้และเข้าโปรเจกต์ Flow จากนั้นเปิดโฟลเดอร์ repo ใน **ChatGPT Desktop → Work locally** และใช้ [ข้อความเริ่มงานใน README](../README.md#quickstart) ให้แอปเข้าถึงโฟลเดอร์และเรียกคำสั่งที่ต้องใช้ตามระบบ permission ของแอป

เมื่อเรียก Laya ครั้งแรกจะดาวน์โหลดโมเดลจาก Hugging Face และเก็บ cache ในเครื่อง การรันครั้งต่อไปใช้ cache เดิม ค่าเริ่มต้นเป็น CPU; lockfile ใช้ [PyTorch CPU index](https://docs.astral.sh/uv/guides/integration/pytorch/) บน Windows/Linux เพื่อไม่ดาวน์โหลด CUDA libraries โดยไม่จำเป็น ไม่ต้องเปิด MPS หรือ CUDA

## หากเปิด Chrome ไม่ได้

- **ไม่พบ Chrome:** ระบุ executable เอง เช่นบน Windows:

  ```powershell
  uv run python flow.py open-browser --chrome "C:\Program Files\Google\Chrome\Application\chrome.exe"
  ```

  หรือกำหนด `CHROME_BIN` ตาม shell ที่ใช้ Path มีช่องว่างหรือภาษาไทยได้
- **Port 9223 is already in use:** ถ้าเป็น Chrome โปรไฟล์ทดสอบเดิมที่ถูกต้อง ให้ใช้ต่อโดยไม่เปิดซ้ำ หากไม่ใช่ให้ปิดโปรแกรมที่ยึดพอร์ตด้วยตัวเอง ตัวรันจะไม่ฆ่า Chrome หรือเลือกโปรไฟล์อื่นแทน
- **ต้องใช้พอร์ตอื่น:** เปิดด้วย `--port 9323` แล้วเพิ่ม `--cdp http://127.0.0.1:9323` ให้คำสั่ง `open-project`, `observe`, `step`, `delegate`, `wait-video` และ `download` ทุกครั้ง
- **DevTools ไม่พร้อม:** อ่าน `runs/chrome-launch.log`; Linux ต้องเปิดจาก Desktop session หาก Chrome ถูก policy ขององค์กรปิด remote debugging ต้องแก้ที่ policy โดยผู้ดูแล
- **ไฟล์ JSON ภาษาไทยอ่านไม่ออก:** บันทึกเป็น UTF-8; รองรับ UTF-8 BOM ด้วย หลีกเลี่ยงค่าเริ่มต้น UTF-16 ของ Windows PowerShell รุ่นเก่า ใช้ `flow.write_json` หรือ editor ที่เลือก UTF-8

ปิด Chrome โปรไฟล์ทดสอบเมื่อจบงาน เก็บ cookies, logs และคลิปดิบไว้ใน `runs/` ที่ Git ไม่ติดตาม

## ตรวจในเครื่องโดยไม่ใช้เครดิต Flow

ทุกระบบ:

```text
uv run python -m unittest discover -s tests -v
uv run ruff check .
```

ตรวจ Chrome/CDP และ FFmpeg เพิ่มบน **PowerShell**:

```powershell
$env:RUN_BROWSER_CHECKS = "1"
$env:RUN_MEDIA_CHECKS = "1"
uv run python -m unittest discover -s tests -v
```

หรือบน **macOS/Linux**:

```bash
RUN_BROWSER_CHECKS=1 RUN_MEDIA_CHECKS=1 uv run python -m unittest discover -s tests -v
```

การทดสอบใช้ Chrome headless โปรไฟล์ชั่วคราวและภาพ/เสียงสังเคราะห์ ไม่แตะ Chrome ที่คุณล็อกอินอยู่ ส่วน `uv run python flow.py model-check` โหลดโมเดลจริงเพื่อทดสอบการเลือกหนึ่งครั้งบนข้อมูลสังเคราะห์ ผล `passed: false` หมายถึงโมเดลเลือกผิด ไม่ใช่หลักฐานว่า OS ใช้ไม่ได้ และไม่ควรแก้ผลทดสอบให้ดูเหมือนผ่าน
