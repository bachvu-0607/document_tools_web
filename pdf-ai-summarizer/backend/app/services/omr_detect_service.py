import datetime
import json
from dataclasses import dataclass

import cv2
import numpy as np
from fastapi import HTTPException

from app.core.omr_database import get_detection, get_template_marker_layout, save_detection_record
from app.schemas.omr import AnswerBlock, OmrDetectionResponse, OmrTemplateResponse, ZoneRect
from app.services.omr_align_service import align_image_with_template, decode_image_exif_aware
from app.services.omr_storage import get_omr_sheet_file
from app.services.omr_template_service import get_omr_template

# === NGUONG THICH UNG (thay cho hang so co dinh) ===
# Van de cua hang so co dinh: "tran tin hieu" (do dam toi da 1 o TO THAT co
# the dat duoc, sau khi tru nen) khac nhau rat nhieu giua cac anh - anh sach
# co the dat 0.7-0.9, anh bi loa sang/anh sang khong deu chi dat 0.2-0.3 (dan
# du lieu that: 1 cau to that 2 dap an B=0.57 D=0.60 nhung tru nen xong chi
# con ~0.25/0.28). 1 hang so co dinh khong the dung dung cho ca hai.
#
# Thay vao do: DO tran tin hieu THAT cua tung KHOI (SBD/Ma de/moi khoi dap
# an) bang percentile cao cua cac o "thang cuoc" trong khoi do, roi cac
# nguong deu tinh theo % CUA TRAN DO - xem _adaptive_thresholds().
#
# Rieng biet, can them 1 "san chong nhieu" tuyet doi theo DO PHAN GIAI (ban
# kinh o tinh bang pixel) - khong phu thuoc anh sang/toi: o cang nhieu pixel
# lay mau thi sai so ngau nhien cang nho (thong ke: sai so ti le 1/can(so
# pixel)). Neu khong co san nay, 1 khoi ca on la MO (ca o dung cung yeu) se co
# tran tin hieu tu no cung thap, keo nguong %-theo-tran tut xuong duoi muc
# nhieu that - tai dien dung bug "bao to-nhieu-dap-an tran lan" o luoi SBD 10
# ung vien da tung gap.
#
# Nguong cuoi = lon hon giua (theo %-tran, theo san-nhieu-do-phan-giai).
CEILING_PERCENTILE = 85
MIN_FILL_FRACTION = 0.40
AMBIGUOUS_MARGIN_FRACTION = 0.35
MULTI_MARK_FRACTION = 0.70
# San tuyet doi toi thieu cho tran tin hieu - tranh chia % cho so gan 0 neu
# ca khoi khong co dau hieu gi (VD toan bo bo trong / anh qua mo).
MIN_SIGNAL_CEILING = 0.15
# He so cho cong thuc san-nhieu (CHI dung cho multi_mark): nguong tuyet doi
# toi thieu = HANG_SO / can(ban_kinh_pixel). O ban kinh binh thuong (~30-40px)
# san nay chi ~0.08-0.09 (gan nhu khong anh huong, %-theo-tran quyet dinh) -
# chi thuc su "vao cuoc" khi ban kinh rat nho (~10-15px, anh do phan giai
# thap), dung luc muc nhieu ngau nhien dang cao nhat.
NOISE_FLOOR_CONST = 0.5
# Chi coi la BO TRONG THAT SU khi chenh lech giua o "toi nhat" va o "sang
# nhat" trong cung 1 cau gan nhu bang 0 - nghia la khong co bat ky dau hieu
# nao de phan biet. Day la nguong TUYET DOI rieng, khong thich ung theo tran/
# do phan giai nhu 3 nguong tren, vi no dai dien cho "khong co gi ca" thay vi
# "chua du tin cay".
NEAR_ZERO_SIGNAL = 0.02
# Neu baseline (o "sang nhat" - it toi nhat) cua RIENG 1 cau thap hon han so
# voi muc nen binh thuong ca khoi (vd bong tay/ngon tay che lech dung 1 hang,
# lam 1 o vo tinh sang bat thuong so voi 3 o con lai CUNG cau), GHIM baseline
# cau do lai gan muc binh thuong thay vi tin tuyet doi vao chinh no - neu
# khong, mot baseline qua thap se "bom phong" gia tao ca 4 lua chon trong cau
# do, de gay bao nham "to nhieu dap an" (thuc te da gap: 1 cau chi to A, o B
# sang hon binh thuong ~0.17 so voi cac cau xung quanh, bi bao nham la "multi").
BASELINE_CLAMP_FRACTION = 0.5


def _adaptive_thresholds(
    ratio_groups: list[list[float]], radius: float,
) -> tuple[float, float, float, float]:
    # Tinh 3 nguong (min_fill, ambiguous_margin, multi_mark) THICH UNG cho 1
    # KHOI (vd het cau SBD, het 1 khoi dap an) dua tren tran tin hieu THAT do
    # duoc tren chinh khoi do va do phan giai (ban kinh pixel), cong voi
    # baseline_floor de ghim baseline cau le. Xem giai thich chi tiet o dau file.
    baselines = [min(ratios) for ratios in ratio_groups]
    winners = [max(ratios) - b for ratios, b in zip(ratio_groups, baselines)]
    signal_ceiling = max(float(np.percentile(winners, CEILING_PERCENTILE)), MIN_SIGNAL_CEILING) if winners else MIN_SIGNAL_CEILING

    min_fill = MIN_FILL_FRACTION * signal_ceiling
    ambiguous_margin = AMBIGUOUS_MARGIN_FRACTION * signal_ceiling
    # San chong nhieu CHI ap dung cho multi_mark - day la nguong duy nhat tung
    # gap bug bao nham hang loat o luoi nhieu ung vien (SBD). min_fill/
    # ambiguous_margin khong can san nay: neu chung tut thap o 1 khoi qua mo,
    # ket qua toi te nhat chi la bi gan "khong chac" (an toan) thay vi "chac
    # chan" - khong tao ra canh bao sai nghiem trong nhu "to nham dap an".
    noise_floor = NOISE_FLOOR_CONST / (radius ** 0.5) if radius > 0 else MIN_SIGNAL_CEILING
    multi_mark = max(MULTI_MARK_FRACTION * signal_ceiling, noise_floor)
    # He so theo SO LUONG UNG VIEN trong 1 nhom (vd 10 cho SBD/Ma de, 4 cho
    # 1 cau trac nghiem A-D) - nhom cang dong thi cang de co it nhat 1 ung
    # vien tinh co vuot nguong do nhieu/gradient anh sang (thay tren du lieu
    # that: ca dai 7/10 o SBD doc gia tri gan bang nhau do bong do dan theo
    # hang, khong phai 1 o le - baseline_floor khong sua duoc vi ca khoi deu
    # bi anh huong). Chuan hoa ve nhom 4 ung vien (dap an trac nghiem, truong
    # hop da kiem chung thuc te la "to that").
    group_size = len(ratio_groups[0]) if ratio_groups else 4
    multi_mark *= (group_size / 4) ** 0.5

    typical_baseline = float(np.median(baselines)) if baselines else 0.0
    baseline_floor = typical_baseline - BASELINE_CLAMP_FRACTION * signal_ceiling
    return min_fill, ambiguous_margin, multi_mark, baseline_floor
# Anh chup thuc te thuong bi nghieng/lech nhe (khong vuong goc 100%), nen toa
# do tinh theo % thuan tuy se le dan cang xa diem goc. Thay vi tin chac vao 1
# toa do co dinh, do them 1 vung nho quanh vi tri du kien va lay diem dam nhat
# trong vung do - bu duoc lech nho ma khong can nan chinh perspective ca anh.
SEARCH_STEPS = 3
SEARCH_RANGE_RATIO = 0.35

# Log chan doan tam thoi - xem tung cau dang tinh ty le "to" the nao, va co
# dang dung luoi o tron THAT do duoc hay bi lui ve cach chia deu (kem chinh
# xac hon). Hien trong Railway Deploy Logs.
DEBUG_DETECT = True


def _dbg(*args) -> None:
    if DEBUG_DETECT:
        print("[OMR-DETECT-DEBUG]", *args, flush=True)


@dataclass
class CellMark:
    cx: float
    cy: float
    radius: float
    # "confident" = chac chan (xanh), "ambiguous" = 1 o duoc chon nhung tin
    # cay chua cao (cam), "multi" = PHAT HIEN >=2 o CUNG TU no da du dam de
    # tinh la da to (do) - khac hang voi "ambiguous": khong phai tin cay thap,
    # ma la ro rang co nhieu hon 1 dap an duoc to cho cung 1 cau.
    status: str


async def _load_images(sheet_bytes: bytes, template_id: str) -> tuple[np.ndarray, np.ndarray, bool]:
    color = decode_image_exif_aware(sheet_bytes)
    if color is None:
        raise HTTPException(status_code=400, detail="Khong doc duoc anh phieu")
    # Nan thang theo 4 dau goc den TRUOC khi doc luoi. Neu mau phieu nay da co
    # san "ban do dau moc" (chup luc tao mau - xem omr_template_service), tinh
    # chinh them 1 buoc qua toan bo dau moc thay vi chi 4 goc, chinh xac hon
    # nhieu voi anh chup nghieng/bi che 1 phan. Luu y: buoc hien thi anh cho
    # man hinh khoanh vung mau (omr_storage.get_omr_sheet_aligned_bytes) VAN
    # dung ban nan tho (chua co template luc do) - 2 he toa do % chi khop nhau
    # khi mau CHUA duoc tinh chinh them, dung nhu truoc gio.
    marker_layout_json = await get_template_marker_layout(template_id)
    template_markers = json.loads(marker_layout_json) if marker_layout_json else None
    aligned, was_aligned = align_image_with_template(color, template_markers)
    gray = cv2.cvtColor(aligned, cv2.COLOR_BGR2GRAY)
    return aligned, gray, was_aligned


def _zone_to_px(zone: ZoneRect, img_w: int, img_h: int) -> tuple[float, float, float, float]:
    return zone.x0 * img_w, zone.y0 * img_h, zone.x1 * img_w, zone.y1 * img_h



# Chi lay 70% ban kinh o giua tam - o that in san 1 vong tron VIEN DEN, vien
# nay nam sat mep ban kinh uoc luong nen 1 khung VUONG bao quanh chac chan se
# dinh phai vien o CA 4 CANH (khong chi 4 goc) - moi o, du co to hay khong,
# deu bi tinh mot phan "toi" co dinh tu chinh cai vien in san do (thay tren du
# lieu that: o TRONG cung doc ra ~0.20 "toi" thay vi gan 0, va co vung con bi
# day sat 1.00 het ca 4 lua chon). Thu hep xuong 1 HINH TRON nho nam han vao
# trong long o, tranh dung phai vien in san, chi con do dung phan giay TRANG
# hay bi to den ben trong.
_SAMPLE_RADIUS_FACTOR = 0.85


def _fill_ratio(gray: np.ndarray, cx: float, cy: float, radius: float) -> float:
    inner_radius = radius * _SAMPLE_RADIUS_FACTOR
    x0, y0 = int(cx - inner_radius), int(cy - inner_radius)
    x1, y1 = int(cx + inner_radius), int(cy + inner_radius)
    x0, y0 = max(0, x0), max(0, y0)
    x1, y1 = min(gray.shape[1], x1), min(gray.shape[0], y1)
    if x1 <= x0 or y1 <= y0:
        return 0.0
    patch = gray[y0:y1, x0:x1]
    yy, xx = np.mgrid[y0:y1, x0:x1]
    mask = (xx - cx) ** 2 + (yy - cy) ** 2 <= inner_radius ** 2
    mask_count = int(np.count_nonzero(mask))
    if mask_count == 0:
        return 0.0
    # Do TOI TRUNG BINH lien tuc (0 = trang tinh, 1 = den tuyet doi) thay vi
    # dem so pixel duoi 1 nguong CO DINH (150). Anh chup thuc te co the bi LOA
    # SANG (phan chieu den/flash) o mot vung - luc do muc toi that su cua net
    # but/chi cung bi day len, co the KHONG BAO GIO xuong duoi nguong co dinh
    # (thay tren du lieu that: ca 4 lua chon 1 cau deu doc ra ~0.1-0.2 nhu
    # nhau du 1 o ro rang co to). Trung binh lien tuc van giu duoc phan chenh
    # lech TUONG DOI so voi 3 o con lai trong cung cau (xem _pick_best), du
    # muc do sang toi tuyet doi co bi lech ca vung.
    mean_intensity = float(patch[mask].mean())
    return 1.0 - (mean_intensity / 255.0)


def _best_fill_ratio(
    gray: np.ndarray,
    cx: float,
    cy: float,
    radius: float,
    search_range: float,
    bounds: tuple[float, float, float, float],
) -> tuple[float, float, float]:
    # Do 1 luoi nho (SEARCH_STEPS x SEARCH_STEPS) quanh (cx, cy), tra ve
    # (ty le toi cao nhat, toa do thuc te cho ra ty le do) - de khoanh preview
    # dung ngay vi tri o that thay vi vi tri "ly thuyet" co the bi lech.
    # Vung do bi GIOI HAN trong pham vi khung da ve (bounds) - khong duoc lan
    # ra ngoai, tranh dinh phai chu so thu tu cau/nhan ke sat ben canh khung.
    bound_x0, bound_y0, bound_x1, bound_y1 = bounds
    best_ratio, best_cx, best_cy = -1.0, cx, cy
    offsets = np.linspace(-search_range, search_range, SEARCH_STEPS)
    for dx in offsets:
        for dy in offsets:
            sample_cx = min(max(cx + dx, bound_x0), bound_x1)
            sample_cy = min(max(cy + dy, bound_y0), bound_y1)
            ratio = _fill_ratio(gray, sample_cx, sample_cy, radius)
            if ratio > best_ratio:
                best_ratio, best_cx, best_cy = ratio, sample_cx, sample_cy
    return best_ratio, best_cx, best_cy


def _find_circle_grid(
    gray: np.ndarray, px0: float, py0: float, px1: float, py1: float, n_rows: int, n_cols: int,
) -> list[list[tuple[float, float]]] | None:
    # Thay vi tin tuyet doi khung da khoanh chia deu thanh luoi, tu DO vi tri
    # THAT cua tung o tron (Hough Circle) roi gom thanh hang/cot - de dung
    # ngay ca khi khung khoanh tay hoi rong/hep hon thuc te vai %, hoac cac
    # cot/nhom khong cach deu nhau tren giay. Tra ve None neu khong dang tin
    # (thieu/thua o so voi so luong ky vong) - ben goi se tu chuyen sang cach
    # chia deu cu lam phuong an du phong.
    x0, y0, x1, y1 = int(px0), int(py0), int(px1), int(py1)
    crop = gray[max(0, y0):y1, max(0, x0):x1]
    h, w = crop.shape[:2]
    _dbg(f"_find_circle_grid: vung {w}x{h}px, ky vong {n_rows}x{n_cols}={n_rows*n_cols} o")
    if h < 10 or w < 10:
        _dbg("  -> vung qua nho, bo qua luoi o tron")
        return None

    approx_cell_w = w / n_cols
    approx_cell_h = h / n_rows
    approx_radius = min(approx_cell_w, approx_cell_h) * 0.4
    min_radius = max(int(approx_radius * 0.55), 3)
    max_radius = max(int(approx_radius * 1.45), min_radius + 1)
    min_dist = max(int(min(approx_cell_w, approx_cell_h) * 0.6), 1)

    blurred = cv2.GaussianBlur(crop, (5, 5), 0)
    circles = cv2.HoughCircles(
        blurred, cv2.HOUGH_GRADIENT, dp=1, minDist=min_dist,
        param1=50, param2=25, minRadius=min_radius, maxRadius=max_radius,
    )
    if circles is None:
        _dbg("  -> HoughCircles khong tim thay vong tron nao, LUI VE cach chia deu")
        return None

    raw_points = [(float(cx) + x0, float(cy) + y0) for cx, cy, _ in circles[0]]

    # Hough hay tra ve vai vong tron gan trung nhau cho CUNG 1 o thuc te (vi
    # du dinh o vien day net) - gop nhung diem qua gan nhau lai thanh 1 truoc
    # khi gom hang/cot, tranh 1 o bi dem thanh 2.
    points: list[tuple[float, float]] = []
    dedupe_dist_sq = (min_dist * 0.6) ** 2
    for point in raw_points:
        if all((point[0] - k[0]) ** 2 + (point[1] - k[1]) ** 2 > dedupe_dist_sq for k in points):
            points.append(point)

    expected_count = n_rows * n_cols
    _dbg(f"  Hough tim {len(raw_points)} vong tron tho, sau gop trung con {len(points)} (ky vong {expected_count})")
    if not (expected_count * 0.85 <= len(points) <= expected_count * 1.15):
        _dbg("  -> so luong vong tron lech qua nhieu so voi ky vong, LUI VE cach chia deu")
        return None

    # Gom hang/cot bang K-means (chia dung K cum) thay vi noi chuoi theo
    # khoang cach lien tiep - noi chuoi de bi "bac cau" dinh 2 hang/cot lien
    # ke lam mot khi co diem nhieu nam giua ranh gioi.
    def _cluster_1d(values: list[float], k: int) -> tuple[list[int], list[float]]:
        data = np.array([[v] for v in values], dtype=np.float32)
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 50, 0.5)
        _, labels, centers = cv2.kmeans(data, k, None, criteria, 10, cv2.KMEANS_PP_CENTERS)
        # Sap xep lai nhan cum theo dung thu tu tang dan cua tam cum (kmeans
        # tra ve nhan theo thu tu ngau nhien, khong theo vi tri).
        order = np.argsort(centers[:, 0])
        rank_of_label = {int(old): rank for rank, old in enumerate(order)}
        sorted_centers = [float(centers[old][0]) for old in order]
        return [rank_of_label[int(label)] for label in labels.flatten()], sorted_centers

    if len(set(points)) < max(n_rows, n_cols):
        _dbg("  -> qua it diem phan biet, LUI VE cach chia deu")
        return None

    row_labels, row_centers = _cluster_1d([p[1] for p in points], n_rows)
    col_labels, col_centers = _cluster_1d([p[0] for p in points], n_cols)

    # Hough hay tra du vai vong tron "gia" (nhieu/chu bi hieu nham la hinh
    # tron) - neu 2 diem cung roi vao 1 o, giu diem nao GAN TAM O (giao diem
    # hang/cot) hon, loai diem con lai thay vi bo cuoc ngay.
    grid: list[list[tuple[float, float] | None]] = [[None] * n_cols for _ in range(n_rows)]
    for point, row_label, col_label in zip(points, row_labels, col_labels):
        existing = grid[row_label][col_label]
        if existing is None:
            grid[row_label][col_label] = point
            continue
        center = (col_centers[col_label], row_centers[row_label])
        existing_dist = (existing[0] - center[0]) ** 2 + (existing[1] - center[1]) ** 2
        new_dist = (point[0] - center[0]) ** 2 + (point[1] - center[1]) ** 2
        if new_dist < existing_dist:
            grid[row_label][col_label] = point

    if any(cell is None for row in grid for cell in row):
        _dbg("  -> co o trong luoi khong ghep duoc diem nao, LUI VE cach chia deu")
        return None

    _dbg("  -> DUNG luoi o tron THAT (khong lui ve chia deu)")
    return grid  # type: ignore[return-value]


def _pick_best(
    ratios: list[float],
    min_fill_ratio: float,
    ambiguous_margin: float,
    multi_mark_min_ratio: float,
    baseline_floor: float = float("-inf"),
) -> tuple[int | None, str, list[int]]:
    # Tra ve (chi so o duoc chon, trang thai, danh sach cac o KHAC cung TU NO
    # DA DU DAM de tinh la da to - khong phai chi vi gan bang o duoc chon).
    # Trang thai: "blank" (khong chenh lech gi - xem NEAR_ZERO_SIGNAL), "multi"
    # (>=2 o cung ro rang da to - hoc sinh to nham/to nhieu dap an cho 1 cau,
    # KHAC voi "khong chac" ve ban chat: khong phai tin cay thap, ma la that
    # su co nhieu hon 1 dau to), "ambiguous" (tin cay chua du cao), "confident".
    # 3 nguong (min_fill_ratio, ambiguous_margin, multi_mark_min_ratio) do
    # _adaptive_thresholds() tinh rieng cho tung KHOI - xem giai thich o dau
    # file, khong con la hang so co dinh chung cho moi anh nua.
    #
    # Tru di ty le THAP NHAT trong nhom truoc khi so nguong: cac o trong 1
    # nhom (vd 4 lua chon A-D cung 1 cau) nam sat nhau nen chiu chung 1 dieu
    # kien anh sang - neu vung giay bi bong rop/toi hon, TAT CA cac o (ke ca o
    # trong) cung bi day ty le "toi" len deu nhau (tung thay tren anh chup
    # thuc te: ca 4 lua chon cung cau doc ra ~1.00 dai gan nhu bang nhau, du
    # chi 1 o duoc to that). Tru baseline nay di se giu lai dung phan chenh
    # lech do MUC THUC gay ra, bat ke vung do sang hay toi.
    #
    # baseline_floor (tu _adaptive_thresholds): ghim baseline khong duoc thap
    # hon muc binh thuong ca khoi - phong truong hop RIENG cau nay bi bong che
    # lam 1 o sang bat thuong, "bom phong" gia tao ca cau (xem giai thich o
    # BASELINE_CLAMP_FRACTION).
    baseline = max(min(ratios), baseline_floor)
    adjusted = [r - baseline for r in ratios]
    ranked = sorted(range(len(adjusted)), key=lambda i: adjusted[i], reverse=True)
    best_index = ranked[0]
    if adjusted[best_index] < NEAR_ZERO_SIGNAL:
        return None, "blank", []

    other_marked = [i for i in ranked[1:] if adjusted[i] >= multi_mark_min_ratio]
    if other_marked:
        return best_index, "multi", other_marked
    if adjusted[best_index] < min_fill_ratio:
        return best_index, "ambiguous", []
    if len(ranked) > 1 and adjusted[best_index] - adjusted[ranked[1]] < ambiguous_margin:
        return best_index, "ambiguous", []
    return best_index, "confident", []


def _detect_digit_grid(
    gray: np.ndarray, zone: ZoneRect, digits: int, img_w: int, img_h: int, marks: list[CellMark], label: str = "",
) -> tuple[str, list[int]]:
    px0, py0, px1, py1 = _zone_to_px(zone, img_w, img_h)
    col_width = (px1 - px0) / digits
    row_height = (py1 - py0) / 10
    radius = min(col_width, row_height) * 0.35

    # Uu tien vi tri o tron THAT do duoc (khong phu thuoc khung khoanh tay co
    # khit tuyet doi hay khong) - chi khi khong tim duoc du so o mong doi moi
    # quay lai chia deu theo % nhu truoc.
    circle_grid = _find_circle_grid(gray, px0, py0, px1, py1, n_rows=10, n_cols=digits)

    result_digits: list[str] = []
    ambiguous_positions: list[int] = []

    # Vong 1 - do het, chua quyet dinh gi.
    columns_data: list[tuple[list[float], list[tuple[float, float]]]] = []
    for col in range(digits):
        ratios = []
        positions = []
        for row in range(10):
            if circle_grid is not None:
                cx, cy = circle_grid[row][col]
                bounds = (cx - radius, cy - radius, cx + radius, cy + radius)
                search_range = radius * 0.3
            else:
                cx = px0 + (col + 0.5) * col_width
                cy = py0 + (row + 0.5) * row_height
                bounds = (px0 + col * col_width, py0, px0 + (col + 1) * col_width, py1)
                search_range = min(col_width, row_height) * SEARCH_RANGE_RATIO
            ratio, best_cx, best_cy = _best_fill_ratio(gray, cx, cy, radius, search_range, bounds)
            ratios.append(ratio)
            positions.append((best_cx, best_cy))
        columns_data.append((ratios, positions))

    min_fill_ratio, ambiguous_margin, multi_mark_min_ratio, baseline_floor = _adaptive_thresholds(
        [ratios for ratios, _ in columns_data], radius,
    )
    _dbg(
        f"khoi {label or 'so'}: nguong thich ung min_fill={min_fill_ratio:.2f}"
        f" ambiguous_margin={ambiguous_margin:.2f} multi_mark={multi_mark_min_ratio:.2f}"
        f" baseline_floor={baseline_floor:.2f} (radius={radius:.0f}px)",
    )

    # Vong 2 - da biet nguong thich ung, quyet dinh tung cot.
    for col, (ratios, positions) in enumerate(columns_data):
        best_row, status, other_marked = _pick_best(
            ratios, min_fill_ratio, ambiguous_margin, multi_mark_min_ratio, baseline_floor,
        )
        if best_row is None:
            result_digits.append("?")
            # Khong doc duoc so nao ro rang - VAN ve 1 vong cam o vi tri "toi
            # nhat trong so cac o toi" tren preview, thay vi im lang khong ve
            # gi (de nguoi dung de dang thay ngay cot nao can xem lai bang mat,
            # khong bi lam tuong la "chac chan khong co gi o day").
            fallback_row = max(range(len(ratios)), key=lambda i: ratios[i])
            fallback_cx, fallback_cy = positions[fallback_row]
            marks.append(CellMark(fallback_cx, fallback_cy, radius, "ambiguous"))
        else:
            result_digits.append(str(best_row))
            mark_cx, mark_cy = positions[best_row]
            marks.append(CellMark(mark_cx, mark_cy, radius, status))
            for extra_row in other_marked:
                extra_cx, extra_cy = positions[extra_row]
                marks.append(CellMark(extra_cx, extra_cy, radius, status))
        if status in ("ambiguous", "multi"):
            ambiguous_positions.append(col)
        ratio_str = ", ".join(f"{r:.2f}" for r in ratios)
        chosen = str(best_row) if best_row is not None else "(bo trong)"
        _dbg(f"{label or 'so'} cot {col}: [{ratio_str}] -> chon={chosen} status={status}")

    return "".join(result_digits), ambiguous_positions


def _detect_answer_blocks(
    gray: np.ndarray,
    blocks: list[AnswerBlock],
    num_choices: int,
    img_w: int,
    img_h: int,
    marks: list[CellMark],
) -> tuple[list[str], list[int]]:
    answers: list[str] = []
    ambiguous_questions: list[int] = []
    question_number = 1

    for block in blocks:
        px0, py0, px1, py1 = _zone_to_px(block.zone, img_w, img_h)
        rows_per_column = block.num_questions // block.num_columns
        col_width = (px1 - px0) / block.num_columns
        row_height = (py1 - py0) / rows_per_column
        choice_width = col_width / num_choices
        radius = min(choice_width, row_height) * 0.35

        # Coi ca khoi la 1 luoi (rows_per_column hang x [so cot * so lua chon]
        # cot) roi do 1 lan duy nhat - khong con phu thuoc khung khoanh tay
        # chia deu dung ty le giua cac nhom cot hay khong (day chinh la nguyen
        # nhan cac loi lech cot da gap truoc do).
        combined_cols = block.num_columns * num_choices
        circle_grid = _find_circle_grid(gray, px0, py0, px1, py1, n_rows=rows_per_column, n_cols=combined_cols)

        block_answers: list[str] = [""] * block.num_questions
        block_ambiguous: list[bool] = [False] * block.num_questions

        # Vong 1 - do het ca khoi, chua quyet dinh gi.
        cells_data: list[tuple[list[float], list[tuple[float, float]], list[tuple[float, float]], int]] = []
        for row in range(rows_per_column):
            for strip in range(block.num_columns):
                ratios = []
                positions = []
                raw_positions = []
                for choice in range(num_choices):
                    if circle_grid is not None:
                        combined_col = strip * num_choices + choice
                        cx, cy = circle_grid[row][combined_col]
                        bounds = (cx - radius, cy - radius, cx + radius, cy + radius)
                        search_range = radius * 0.3
                    else:
                        strip_x0 = px0 + strip * col_width
                        cx = strip_x0 + (choice + 0.5) * choice_width
                        cy = py0 + (row + 0.5) * row_height
                        bounds = (
                            strip_x0 + choice * choice_width, py0,
                            strip_x0 + (choice + 1) * choice_width, py1,
                        )
                        search_range = min(choice_width, row_height) * SEARCH_RANGE_RATIO
                    ratio, best_cx, best_cy = _best_fill_ratio(gray, cx, cy, radius, search_range, bounds)
                    ratios.append(ratio)
                    positions.append((best_cx, best_cy))
                    raw_positions.append((cx, cy))
                local_index = strip * rows_per_column + row
                cells_data.append((ratios, positions, raw_positions, local_index))

        min_fill_ratio, ambiguous_margin, multi_mark_min_ratio, baseline_floor = _adaptive_thresholds(
            [ratios for ratios, _, _, _ in cells_data], radius,
        )
        _dbg(
            f"khoi cau {question_number}-{question_number + block.num_questions - 1}:"
            f" nguong thich ung min_fill={min_fill_ratio:.2f}"
            f" ambiguous_margin={ambiguous_margin:.2f} multi_mark={multi_mark_min_ratio:.2f}"
            f" baseline_floor={baseline_floor:.2f} (radius={radius:.0f}px)",
        )

        # Vong 2 - da biet nguong thich ung cua khoi nay, quyet dinh tung cau.
        for ratios, positions, raw_positions, local_index in cells_data:
            best_choice, status, other_marked = _pick_best(
                ratios, min_fill_ratio, ambiguous_margin, multi_mark_min_ratio, baseline_floor,
            )
            if best_choice is None:
                block_answers[local_index] = ""
                # Khong doc duoc dap an nao ro rang - van ve 1 vong cam o
                # vi tri "toi nhat trong so cac o toi" tren preview, thay
                # vi im lang khong ve gi (de nguoi dung de dang thay ngay
                # cau nao can xem lai bang mat).
                fallback_choice = max(range(len(ratios)), key=lambda i: ratios[i])
                fallback_cx, fallback_cy = positions[fallback_choice]
                marks.append(CellMark(fallback_cx, fallback_cy, radius, "ambiguous"))
            else:
                block_answers[local_index] = chr(ord("A") + best_choice)
                mark_cx, mark_cy = positions[best_choice]
                marks.append(CellMark(mark_cx, mark_cy, radius, status))
                # "multi": hoc sinh to nham/to hon 1 dap an cho cung 1 cau -
                # ve vong DO cho TAT CA cac o cung ro rang da to, khong chi
                # o duoc chon, de nguoi xem thay het cac cho bi to thay vi
                # chi thay 1 vong roi tuong nham la doc thieu.
                for extra_choice in other_marked:
                    extra_cx, extra_cy = positions[extra_choice]
                    marks.append(CellMark(extra_cx, extra_cy, radius, status))
            block_ambiguous[local_index] = status in ("ambiguous", "multi")
            ratio_str = ", ".join(
                f"{chr(ord('A') + i)}={r:.2f}@({raw_positions[i][0]:.0f},{raw_positions[i][1]:.0f})"
                for i, r in enumerate(ratios)
            )
            chosen = block_answers[local_index] or "(bo trong)"
            _dbg(
                f"cau {question_number + local_index}: [{ratio_str}]"
                f" -> chon={chosen} status={status}"
                f" (dung_luoi_o_tron={circle_grid is not None})",
            )

        for local_index in range(block.num_questions):
            answers.append(block_answers[local_index])
            if block_ambiguous[local_index]:
                ambiguous_questions.append(question_number + local_index)

        question_number += block.num_questions

    return answers, ambiguous_questions


def _run_detection_core(
    template: OmrTemplateResponse, gray: np.ndarray,
) -> tuple[str, list[int], str, list[int], list[str], list[int], list[CellMark]]:
    img_h, img_w = gray.shape[:2]
    marks: list[CellMark] = []

    sbd, sbd_ambiguous = _detect_digit_grid(gray, template.sbd_zone, template.sbd_digits, img_w, img_h, marks, "SBD")
    made, made_ambiguous = _detect_digit_grid(gray, template.made_zone, template.made_digits, img_w, img_h, marks, "Ma de")
    answers, ambiguous_questions = _detect_answer_blocks(
        gray, template.answer_blocks, template.num_choices, img_w, img_h, marks,
    )

    return sbd, sbd_ambiguous, made, made_ambiguous, answers, ambiguous_questions, marks


async def run_detection(template_id: str, sheet_id: str, user_id: str) -> OmrDetectionResponse:
    template = await get_omr_template(template_id, user_id)
    sheet_bytes, _ = await get_omr_sheet_file(sheet_id, user_id)
    _, gray, was_aligned = await _load_images(sheet_bytes, template_id)

    sbd, sbd_ambiguous, made, made_ambiguous, answers, ambiguous_questions, _ = _run_detection_core(template, gray)

    detected_at = datetime.datetime.now().isoformat()
    await save_detection_record(
        sheet_id=sheet_id,
        user_id=user_id,
        template_id=template_id,
        sbd=sbd,
        sbd_ambiguous_digits=json.dumps(sbd_ambiguous),
        made=made,
        made_ambiguous_digits=json.dumps(made_ambiguous),
        answers=json.dumps(answers),
        ambiguous_questions=json.dumps(ambiguous_questions),
        detected_at=detected_at,
        aligned=was_aligned,
    )

    return OmrDetectionResponse(
        sheet_id=sheet_id,
        template_id=template_id,
        sbd=sbd,
        sbd_ambiguous_digits=sbd_ambiguous,
        made=made,
        made_ambiguous_digits=made_ambiguous,
        answers=answers,
        ambiguous_questions=ambiguous_questions,
        detected_at=detected_at,
        aligned=was_aligned,
    )


async def get_saved_detection(sheet_id: str, user_id: str) -> OmrDetectionResponse:
    row = await get_detection(sheet_id, user_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Detection not found")
    return OmrDetectionResponse(
        sheet_id=row["sheet_id"],
        template_id=row["template_id"],
        sbd=row["sbd"],
        sbd_ambiguous_digits=json.loads(row["sbd_ambiguous_digits"]),
        made=row["made"],
        made_ambiguous_digits=json.loads(row["made_ambiguous_digits"]),
        answers=json.loads(row["answers"]),
        ambiguous_questions=json.loads(row["ambiguous_questions"]),
        detected_at=row["detected_at"],
        aligned=bool(row["aligned"]),
    )


async def get_or_run_detection(template_id: str, sheet_id: str, user_id: str) -> OmrDetectionResponse:
    # Chi dung lai ket qua da luu neu la ban NGUOI DUNG DA TU SUA tay (is_manual)
    # - tranh viec cham hang loat vo tinh ghi de mat cong sua tay. Ban DOC TU
    # DONG thi luon chay lai OpenCV moi lan cham, de luon phan anh dung thuat
    # toan detect MOI NHAT (thuat toan con dang duoc tinh chinh lien tuc - neu
    # cu dung cache cu, sua thuat toan xong test lai se van thay ket qua CU,
    # gay hieu lam la fix khong co tac dung).
    row = await get_detection(sheet_id, user_id)
    if row is not None and row["is_manual"]:
        return await get_saved_detection(sheet_id, user_id)
    return await run_detection(template_id, sheet_id, user_id)


async def override_detection(
    sheet_id: str, template_id: str, sbd: str, made: str, answers: list[str], user_id: str,
) -> OmrDetectionResponse:
    # Nguoi dung tu sua lai ket qua doc sau khi xem preview thay may doc sai -
    # coi nhu da xac nhan bang mat nen khong con o nao "khong chac" nua.
    detected_at = datetime.datetime.now().isoformat()
    await save_detection_record(
        sheet_id=sheet_id,
        user_id=user_id,
        template_id=template_id,
        sbd=sbd,
        sbd_ambiguous_digits=json.dumps([]),
        made=made,
        made_ambiguous_digits=json.dumps([]),
        answers=json.dumps(answers),
        ambiguous_questions=json.dumps([]),
        detected_at=detected_at,
        is_manual=True,
    )
    return OmrDetectionResponse(
        sheet_id=sheet_id,
        template_id=template_id,
        sbd=sbd,
        sbd_ambiguous_digits=[],
        made=made,
        made_ambiguous_digits=[],
        answers=answers,
        ambiguous_questions=[],
        detected_at=detected_at,
        aligned=True,
    )


async def render_preview_image(template_id: str, sheet_id: str, user_id: str) -> bytes:
    template = await get_omr_template(template_id, user_id)
    sheet_bytes, _ = await get_omr_sheet_file(sheet_id, user_id)
    color, gray, _ = await _load_images(sheet_bytes, template_id)

    _, _, _, _, _, _, marks = _run_detection_core(template, gray)

    # BGR: cam = khong chac (tin cay thap), do = phat hien nhieu hon 1 o duoc
    # to cho cung 1 cau/cot (nghiem trong hon - can xem lai chac chan), xanh
    # duong = chac chan.
    MARK_COLORS = {"ambiguous": (0, 165, 255), "multi": (0, 0, 255), "confident": (255, 140, 0)}
    for mark in marks:
        color_bgr = MARK_COLORS.get(mark.status, (255, 140, 0))
        cv2.circle(color, (int(mark.cx), int(mark.cy)), int(mark.radius), color_bgr, 3)

    success, buffer = cv2.imencode(".png", color)
    if not success:
        raise HTTPException(status_code=500, detail="Khong tao duoc anh preview")
    return buffer.tobytes()
