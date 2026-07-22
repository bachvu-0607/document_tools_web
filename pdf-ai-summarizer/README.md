# PDF AI Summarizer

Ung dung web chay local: tai len file PDF, dung OpenAI de tom tat / dich / doc noi dung, luu lich su tom tat vao SQLite, va xuat lai duoi nhieu dinh dang (PDF, Word, anh).

## Tinh nang

- **Upload PDF** + xem truoc noi dung da trich xuat.
- **4 che do doc PDF** (chon duoc o nhieu tinh nang, danh doi giua toc do/chi phi va do day du):
  - `Chi text` — trich text bang PyMuPDF, tu nhan dien bang bieu (chuyen thanh markdown table) va tieu de muc (dua theo co chu), khong goi AI, mien phi.
  - `Text + mo ta anh` — nhu tren, cong them goi AI (vision) mo ta tung anh nhung trong PDF.
  - `Toan trang dang anh` — bo qua buoc trich text, chup nguyen trang thanh anh roi nho AI doc lai (manh nhat voi PDF co cong thuc toan/layout phuc tap, cung ton kem nhat, toi da 15 trang).
- **Tom tat**: tuy chinh kieu tom tat, ngon ngu, do dai, doi tuong doc, trong tam, van phong, ghi chu them; luu lich su vao SQLite; xuat ket qua ra file PDF co giao dien rieng.
- **Dich tai lieu**: dich toan bo noi dung PDF sang ngon ngu khac, giu nguyen cau truc tieu de/bang bieu.
- **Chuyen doi sang Word (.docx)** — 2 phuong an:
  - Mien phi: dung thu vien `pdf2docx`, giu layout goc (hop voi PDF dang van ban/bao cao, PDF dang slide de bi loi cach trang).
  - Dung AI: doc noi dung day du (khong rut gon) roi dung `python-docx` dung lai file Word that, giu heading/bang bieu.
- **Cong cu PDF** (khong dung AI, mien phi):
  - Xuat tung trang PDF thanh anh PNG (dong goi ZIP).
  - Gop nhieu file PDF thanh 1.
  - Nen file PDF (chi hieu qua ro voi PDF nhieu chu; PDF nhieu anh giam dung luong rat it vi anh da duoc nen san).
  - **Xuat bang bieu ra Excel** (khong dung AI, mien phi) — 2 phuong an:
    - Xuat tho: dung `find_tables()` cua PyMuPDF de do tim moi bang trong PDF, moi trang 1 sheet. Hop voi bang bieu bat ky, khong can dung mau co dinh.
    - Xuat theo mau chuan BCTC ngan hang (Thong tu 49/2014 + 27/2021, mau B02a/B03a/B04a/B05a): tu nhan dien trang nao thuoc mau nao, doi chieu tung dong voi danh sach chi tieu chuan cua mau (`financial_extract_service.py`) de sap xep lai dung thu tu, gop nhan bi ngat dong, tach so bi dinh chung o va giu dung in-dam muc cha/muc con — moi mau ra 1 sheet rieng, sach hon ban xuat tho.
  - **Cong cu anh** (khong dung AI, mien phi): doi dinh dang anh (JPG/PNG/WebP) va chinh chat luong nen (chi ap dung voi JPG/WebP).
- **Cham trac nghiem tu anh chup phieu tra loi (OMR)** (khong dung AI, dung OpenCV, mien phi) — quy trinh 5 buoc, moi buoc 1 tab rieng:
  1. **Upload bai lam**: tai len nhieu anh/1 thu muc cung luc (giu ten file goc), hoac **chup truc tiep bang camera** — tu dong nhan biet phieu da can thang vao khung (dua vao 4 o vuong den o goc phieu) roi tu dong chup + upload, khong can bam nut, co doi phieu duoc rut ra truoc khi chup phieu tiep theo de tranh chup trung.
  2. **Doc phieu mau**: chon 1 anh lam mau, keo chuot khoanh vung SBD / Ma de / (toi da 3) khoi cau hoi — luu lai de dung chung cho ca xap phieu cung mau.
  3. **Tao dap an**: chon 1 anh phieu da to dung + mau tuong ung, may tu doc, cho sua tay truc tiep (go chu A/B/C/D) neu doc sai, roi luu thanh dap an chuan.
  4. **Cham bai**: chon dap an chuan + nhieu phieu hoc sinh, cham hang loat 1 lan, luot nhanh tung bai bang nut hoac phim `← →`, xem preview khoanh mau (xanh=dung, do=sai, cam=khong chac), sua khoanh neu can va cham lai rieng bai do.
  5. **Bang diem**: nhap ten Lop roi bam luu de **chot ket qua vao SQLite** (khong tu dong luu) — xem lai/loc theo lop/SBD/ma de, xoa tung dong.
  - Xoa duoc: phieu da upload, mau phieu, dap an, ket qua da chot (co chan xoa neu dang bi phieu/dap an khac phu thuoc).
  - Nhan dien o tron bang OpenCV (Hough Circle + K-means gom cum hang/cot), tu nan thang anh nghieng dua vao 4 dau moc den in san tren phieu; cau/chu so nao ti le to giua 2 lua chon gan nhau qua sit se duoc gan co "khong chac" thay vi doan lieu.

## Cong nghe su dung

**Backend:** FastAPI, PyMuPDF (`fitz`), OpenAI API (text + vision), `aiosqlite`, WeasyPrint + Jinja2 + `markdown` (xuat PDF), `pdf2docx` + `python-docx` (xuat Word), `openpyxl` (xuat Excel), Pillow (cong cu anh), OpenCV (`opencv-python-headless`) + NumPy (nhan dien o tron OMR).

**Frontend:** Next.js 16 (App Router), React 18, TypeScript, Tailwind CSS.

## Yeu cau he thong

- Python 3.13, Node.js + `pnpm`.
- WeasyPrint (xuat PDF tom tat) can vai thu vien he thong — tren macOS cai qua Homebrew:
  ```bash
  brew install cairo pango gdk-pixbuf libffi
  ```

## Chay backend

> **Luu y quan trong:** cac lenh ben duoi gia dinh ban dang dung trong thu muc **goc cua project nay** (`pdf-ai-summarizer/`, thu muc chua ca `backend/` va `frontend/`). Neu `cd backend` bi loi "No such file or directory", tuc la ban dang dung sai cho — go `pwd` de kiem tra, hoac `cd` thang toi day bang duong dan day du truoc khi chay tiep. Chay nham thu muc se khien `uvicorn --reload` quet nham phai thu muc khac (co the treo may, CPU cao) ma khong bao loi ro rang.

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # dien OPENAI_API_KEY that vao file .env
uvicorn app.main:app --reload --port 8000
```

Kiem tra health check:

```bash
curl http://localhost:8000/api/health
```

Xem toan bo API (Swagger UI): `http://localhost:8000/docs`

### Bien moi truong backend (`backend/.env`)

| Bien | Y nghia | Mac dinh |
|---|---|---|
| `OPENAI_API_KEY` | API key OpenAI, bat buoc | (trong) |
| `OPENAI_MODEL` | Model dung de tom tat/dich/doc anh | `gpt-5-mini` |
| `MAX_UPLOAD_MB` | Gioi han dung luong file upload | `50` |
| `DATABASE_URL` | Duong dan file SQLite luu lich su tom tat (dung chung cho ca du lieu OMR) | `../data/database/app.sqlite3` |
| `CORS_ORIGINS` | Danh sach origin frontend duoc phep goi API | `http://localhost:3000,http://127.0.0.1:3000` |
| `OMR_UPLOAD_DIR` | Thu muc luu anh phieu tra loi (OMR) | `../data/omr_uploads` |

## Chay frontend

> Tuong tu backend: dam bao dang dung tai thu muc goc `pdf-ai-summarizer/` truoc khi `cd frontend`.

```bash
cd frontend
pnpm install
cp .env.local.example .env.local   # neu can doi dia chi backend
pnpm dev
```

Frontend mac dinh chay tai: `http://localhost:3000`

## Cau truc

```text
pdf-ai-summarizer/
├── frontend/           # Next.js UI
│   ├── app/
│   ├── components/      # ... + OmrUploadPanel, OmrTemplatePanel, OmrAnswerKeyPanel,
│   │                     #     OmrGradePanel, OmrResultsPanel, OmrCameraCapture, OmrZoneCanvas...
│   ├── lib/
│   └── types/
├── backend/             # FastAPI
│   ├── app/
│   │   ├── api/         # cac router: documents, images, summaries, translations, health, omr
│   │   ├── core/        # config, ket noi database (app + omr_database)
│   │   ├── prompts/      # bang anh xa lua chon -> chi dan prompt chi tiet
│   │   ├── schemas/      # Pydantic request/response (... + omr.py)
│   │   ├── services/     # logic nghiep vu: doc PDF, goi OpenAI, xuat Word/PDF/Excel,
│   │   │                 # cong cu PDF (gop/nen/xuat anh), cong cu anh, trich xuat BCTC ngan hang,
│   │   │                 # OMR (omr_storage, omr_align_service, omr_template_service,
│   │   │                 # omr_detect_service, omr_answer_key_service, omr_grade_service,
│   │   │                 # omr_results_service)
│   │   └── templates/    # template HTML dung de xuat PDF tom tat
│   └── requirements.txt
├── data/
│   ├── uploads/          # file PDF nguoi dung tai len
│   ├── database/         # file SQLite luu lich su tom tat + toan bo du lieu OMR
│   ├── omr_uploads/       # anh phieu tra loi da tai len / chup bang camera
│   └── outputs/
├── .gitignore
├── README.md
└── start-local.sh
```

## Ghi chu / gioi han da biet

- `reportlab` con trong `requirements.txt` nhung khong con duoc dung (da chuyen sang WeasyPrint cho phan xuat PDF) — co the go bo sau.
- Chuyen doi Word ban mien phi (`pdf2docx`) khong xu ly tot PDF dang slide (khoang trang lon giua cac phan) — nen dung phuong an AI cho loai file nay.
- Cac tinh nang doc PDF hien khong ho tro OCR mien phi (Tesseract) cho PDF dang anh scan — che do "Toan trang dang anh" dung AI de doc thay, nhung ton chi phi.
- `Pillow` (dung cho cong cu anh) chua duoc khai bao rieng trong `requirements.txt`, hien chi co san vi la dependency giao cua `pymupdf`/`pdf2docx` — neu go cac goi do, can them `pillow` thu cong.
- Xuat Excel theo mau chuan (`convert-excel-template`) hien chi ho tro dung 4 mau BCTC hop nhat cua ngan hang theo Thong tu 49/2014 + 27/2021 (B02a, B03a, B04a, B05a) — danh sach chi tieu duoc khai bao cung trong `financial_extract_service.py`, PDF khac mau nay se khong nhan dien duoc trang nao va bao loi.
- **OMR** can phieu giay co san **4 o vuong den in san o 4 goc** de lam dau moc can thang anh (chup nghieng/xa gan van doc duoc nho buoc nay) — phieu khong co du 4 dau moc nay se bi bao "khong can thang duoc", ket qua doc kem tin cay hon va nen kiem tra lai bang mat.
- Tinh nang camera OMR yeu cau trinh duyet ho tro `getUserMedia` o do phan giai cao (`~3840px`) — anh chup qua thap do phan giai la nguyen nhan pho bien nhat khien can thang/nhan dien sai; da co nut xoay 90/180/270 do va chon thiet bi camera thu cong (ho tro ca Continuity Camera tren macOS, nhung co the bi mat khoi danh sach neu iPhone khoa man hinh/mat ket noi).
- Ket qua "Bang diem" chi luu khi nguoi dung chu dong bam "Luu" o tab Cham bai (khong tu dong luu khi cham) — moi phieu chi giu 1 dong ket qua cho moi dap an (luu lai se de/update dong cu, khong tao trung).
- Deploy: **Vercel chi phu hop cho phan frontend Next.js** (serverless, khong co o dia ben vung) — backend FastAPI can host o noi giu duoc file/SQLite lau dai (vd Railway/Render/Fly.io), chua duoc thiet lap san trong repo nay.
