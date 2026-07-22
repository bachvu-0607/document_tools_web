FROM python:3.13-slim

# WeasyPrint (xuat PDF tom tat) can cairo/pango/gdk-pixbuf/libffi; OpenCV (OMR)
# can libgomp1 de chay da luong - tren macOS cai qua Homebrew, tren Linux (container
# nay) phai apt-get thu cong vi pip khong cai duoc thu vien he thong.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi8 \
    shared-mime-info \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Thu muc du lieu ben vung - gan Volume vao /app/data tren Railway de khong mat
# du lieu (SQLite + anh upload) moi lan redeploy.
RUN mkdir -p /app/data/database /app/data/uploads /app/data/outputs /app/data/omr_uploads

EXPOSE 8000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
