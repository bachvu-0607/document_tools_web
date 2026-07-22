# Frontend Notes

## Chay

```bash
pnpm install
pnpm dev        # http://localhost:3000
pnpm run type-check
```

## File nen doc khi hoc luong chinh

- `app/page.tsx`: man hinh chinh — quan ly toan bo state (upload, chon tham so, ket qua) va lap rap cac panel.
- `app/layout.tsx`: khung HTML/body chung, khai bao font Inter.
- `app/globals.css`: CSS global va Tailwind.
- `lib/api.ts`: tat ca ham goi backend API (fetch), moi endpoint backend co 1 ham tuong ung.
- `types/*.ts`: kieu du lieu frontend mong backend tra ve, khop voi Pydantic schema ben backend.

## Components (`components/`)

- `DocumentPanel.tsx`: upload PDF + xem truoc noi dung.
- `SummaryPanel.tsx`: form tom tat + ket qua.
- `TranslatePanel.tsx`: form dich tai lieu + ket qua.
- `DocxExportPanel.tsx`: chuyen doi PDF sang Word (2 phuong an).
- `PdfToolsPanel.tsx`: cac tien ich nho (xuat anh tung trang, gop PDF, nen PDF).
- `ConnectionBadge.tsx`, `Banner.tsx`: hien trang thai ket noi backend / thong bao loi-thanh cong.
- `ui/`: cac component dung chung (Button, Card, Spinner, icon SVG tu ve).

`page.tsx` dieu khien 4 panel ben tren (Tom tat / Dich tai lieu / Chuyen doi Word / Cong cu PDF) qua 1 cong tac chuyen tab, chi hien 1 panel tai 1 thoi diem canh `DocumentPanel`.

## File cau hinh hau truong

- `package.json`: danh sach thu vien va script.
- `tsconfig.json`: cau hinh TypeScript.
- `next.config.mjs`: cau hinh Next.js.
- `postcss.config.mjs`: cau hinh xu ly CSS cho Tailwind.
- `tailwind.config.ts`: noi Tailwind biet can quet file UI nao, khai bao font Inter lam font mac dinh.
- `pnpm-lock.yaml`: khoa version thu vien, khong can doc.
- `pnpm-workspace.yaml`: cho phep dependency `sharp` build khi cai Next.js.
- `next-env.d.ts`: file type cua Next.js, khong can sua.
