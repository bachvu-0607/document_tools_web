import io

import cv2
import numpy as np
from PIL import Image, ImageOps

# Nguong loc "o vuong den" lam dau moc goc trang - dua tren kich thuoc THUC TE
# do duoc tren anh mau (khoang 0.0002-0.0005 dien tich anh), chua bien do rong
# de chiu duoc anh chup gan/xa khac nhau. Dau moc trong (giua cac khoi) cung
# co dang vuong den nhung nho hon dau goc that - khong sao, van loc qua duoc,
# vi buoc chon 4 goc ben duoi chi lay 4 diem CUC BIEN, khong quan tam so luong
# ung vien con lai.
MIN_MARKER_AREA_RATIO = 0.00005
MAX_MARKER_AREA_RATIO = 0.01
MIN_ASPECT_RATIO = 0.6
MAX_ASPECT_RATIO = 1.4
MIN_SOLIDITY = 0.8
# 2 canh doi dien cua 1 to giay chup (du hoi nghieng do goc chup) khong the
# lech nhau qua nhieu - neu chenh lech vuot qua ty le nay, nhieu kha nang 1
# trong 4 "goc" chon duoc thuc ra la nham (vd thieu mat 1 goc that trong khung
# hinh, thuat toan lay dai 1 vet den khac lam goc thay the) - tu choi nan anh
# thay vi tao ra ket qua meo lech con te hon ca khong nan.
MAX_SIDE_RATIO = 1.6
# 4 "goc" chon duoc phai trai gan het chieu rong/cao cua ca anh chup - phong
# truong hop phieu co THEM dau vuong den o giua trang (khong chi o 4 goc that,
# vd hang dau moc phu giua trang de can chinh tung khoi rieng). Neu chup thieu
# mat 1 canh (vd cham sat day, cat mat dau goc that o day), thuat toan se lay
# tam dau moc phu o giua trang lam "goc" thay the - ra hinh chu nhat chi phu
# duoc 1 phan anh (vd nua tren), khong phai ca trang giay. Ty le nay bat duoc
# truong hop do: neu hinh chu nhat qua nho so voi khung hinh, coi nhu chua
# tin cay, tu choi thay vi nan sai va am tham doc sai nhung cau o phan bi cat.
MIN_COVERAGE_RATIO = 0.65
# Sau khi nan tho bang 4 goc, doi chieu tung dau moc do duoc voi vi tri ky
# vong (theo ban do dau moc da luu tu mau) - lech duoi nguong nay (ty le %
# theo canh dai hon cua anh) moi coi la khop, tranh ghep nham dau moc gan nhau.
MARKER_MATCH_MAX_DIST_RATIO = 0.035
# Can du nhieu diem khop moi tin cay hon phep nan tho 4 diem - qua it diem thi
# RANSAC de bi nhieu, thua tin cay phep nan tho ban dau con hon.
MIN_REFINE_MATCHES = 6

# Bat/tat log chan doan tam thoi - in ra stdout (hien trong Railway Deploy
# Logs) de xem chinh xac thuat toan dang thay gi tren anh that cua nguoi dung,
# khong can ho gui file anh goc. TAT sau khi chan doan xong, tranh log rac.
DEBUG_ALIGNMENT = True


def _dbg(*args) -> None:
    if DEBUG_ALIGNMENT:
        print("[OMR-ALIGN-DEBUG]", *args, flush=True)


def decode_image_exif_aware(image_bytes: bytes) -> np.ndarray | None:
    # Anh chup tu dien thoai thuong kem theo the EXIF "Orientation" - Photos/
    # trinh duyet tu doc the do va XOAY ANH LUC HIEN THI cho nguoi dung xem
    # dung chieu, nhung DU LIEU DIEM ANH GOC luu trong file van giu nguyen
    # CHUA xoay. cv2.imdecode() doc thang du lieu tho, bo qua hoan toan the
    # EXIF nay - khien thuat toan "nhin" anh o 1 huong khac han so voi nguoi
    # dung dang thay tren man hinh (vd nua tren theo mat nguoi lai nam o 1
    # canh ben trong du lieu tho) - day chinh la nguyen nhan cac lan "bat
    # nham goc" du anh nhin bang mat hoan toan binh thuong, du duoc canh
    # chuan. Dung Pillow doc + ImageOps.exif_transpose() de xoay dung truoc
    # (ham nay tu doc the EXIF va xoay/lat anh cho khop, roi xoa the di), roi
    # moi doi sang mang OpenCV (BGR) de xu ly tiep nhu cu.
    try:
        pil_image = Image.open(io.BytesIO(image_bytes))
        pil_image = ImageOps.exif_transpose(pil_image)
        if pil_image is None:
            return None
        rgb_array = np.array(pil_image.convert("RGB"))
        return cv2.cvtColor(rgb_array, cv2.COLOR_RGB2BGR)
    except Exception:
        return None


# Anh sang/do phoi sang khac nhau giua cac lan chup khien 1 nguong co dinh
# khong phai luc nao cung tach duoc dau goc den khoi nen - thu lan luot vai
# nguong (bao gom Otsu tu dieu chinh theo tung anh) truoc khi bo cuoc.
THRESHOLD_ATTEMPTS = [100, 130, 70, "otsu"]


def _find_marker_candidates(gray: np.ndarray, threshold: int | str) -> np.ndarray:
    img_area = gray.shape[0] * gray.shape[1]
    if threshold == "otsu":
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    else:
        _, binary = cv2.threshold(gray, threshold, 255, cv2.THRESH_BINARY_INV)
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    candidates = []
    rejected_by_area = 0
    rejected_by_aspect = 0
    rejected_by_solidity = 0
    for contour in contours:
        area = cv2.contourArea(contour)
        area_ratio = area / img_area
        if not (MIN_MARKER_AREA_RATIO <= area_ratio <= MAX_MARKER_AREA_RATIO):
            if area_ratio > 0:
                rejected_by_area += 1
            continue
        x, y, box_w, box_h = cv2.boundingRect(contour)
        if box_h == 0:
            continue
        aspect = box_w / box_h
        if not (MIN_ASPECT_RATIO <= aspect <= MAX_ASPECT_RATIO):
            rejected_by_aspect += 1
            continue
        solidity = area / (box_w * box_h)
        if solidity < MIN_SOLIDITY:
            rejected_by_solidity += 1
            continue
        candidates.append((x + box_w / 2, y + box_h / 2))

    _dbg(
        f"threshold={threshold}: {len(candidates)} ung vien hop le"
        f" (loai vi sai/qua/thieu dien tich={rejected_by_area},"
        f" sai ty le canh={rejected_by_aspect}, khong dac hinh vuong={rejected_by_solidity})",
    )
    for cx, cy in candidates:
        _dbg(f"    ung vien tai ({cx:.0f}, {cy:.0f})")

    return np.array(candidates, dtype=np.float32)


def _pick_outer_corners(candidates: np.ndarray, img_w: int, img_h: int) -> np.ndarray | None:
    # Trong so cac o vuong den tim duoc (ca dau goc trang lan dau moc noi bo
    # giua cac khoi), 4 goc THAT cua trang luon la 4 diem CUC BIEN nhat - tong
    # x+y nho nhat/lon nhat va hieu x-y nho nhat/lon nhat - vi moi diem noi bo
    # nam gan tam trang hon nhieu so voi 4 goc ngoai cung.
    if len(candidates) < 4:
        _dbg(f"chi co {len(candidates)} ung vien (< 4), bo qua nguong nay")
        return None

    sums = candidates[:, 0] + candidates[:, 1]
    diffs = candidates[:, 0] - candidates[:, 1]

    top_left = candidates[np.argmin(sums)]
    bottom_right = candidates[np.argmax(sums)]
    top_right = candidates[np.argmax(diffs)]
    bottom_left = candidates[np.argmin(diffs)]

    corners = np.array([top_left, top_right, bottom_right, bottom_left], dtype=np.float32)
    _dbg(
        f"4 goc cuc bien chon duoc: TL=({top_left[0]:.0f},{top_left[1]:.0f})"
        f" TR=({top_right[0]:.0f},{top_right[1]:.0f})"
        f" BR=({bottom_right[0]:.0f},{bottom_right[1]:.0f})"
        f" BL=({bottom_left[0]:.0f},{bottom_left[1]:.0f})"
        f" | kich thuoc anh {img_w}x{img_h}",
    )

    # 4 diem phai thuc su phan biet (khac o vuong bi trung/gan nhau do anh qua
    # it dau moc de chon) - neu 2 "goc" trung gan nhau thi coi nhu khong tim
    # duoc, tranh nan anh ra ket qua vo nghia.
    for i in range(4):
        for j in range(i + 1, 4):
            if np.linalg.norm(corners[i] - corners[j]) < 10:
                _dbg("tu choi: 2 trong 4 goc qua gan nhau (trung diem)")
                return None

    # Kiem tra hinh dang co hop ly khong (2 canh doi dien khong duoc lech qua
    # nhieu) - neu khong, nhieu kha nang thieu mat 1 goc that trong khung hinh
    # va thuat toan da lay nham 1 diem khac lam goc thay the.
    top_len = np.linalg.norm(top_right - top_left)
    bottom_len = np.linalg.norm(bottom_right - bottom_left)
    left_len = np.linalg.norm(bottom_left - top_left)
    right_len = np.linalg.norm(bottom_right - top_right)
    _dbg(f"do dai 4 canh: tren={top_len:.0f} duoi={bottom_len:.0f} trai={left_len:.0f} phai={right_len:.0f}")
    for a, b in ((top_len, bottom_len), (left_len, right_len)):
        if a <= 0 or b <= 0 or max(a, b) / min(a, b) > MAX_SIDE_RATIO:
            _dbg(f"tu choi: 2 canh doi dien lech qua nhieu (ty le > {MAX_SIDE_RATIO})")
            return None

    # 4 goc phai trai gan het khung anh, khong chi la 1 hinh chu nhat nho lot
    # thom ben trong (dau hieu bi thieu mat 1 canh that, thuat toan lay tam
    # dau moc phu giua trang lam goc thay the - xem giai thich o MIN_COVERAGE_RATIO).
    xs = corners[:, 0]
    ys = corners[:, 1]
    width_ratio = (xs.max() - xs.min()) / img_w
    height_ratio = (ys.max() - ys.min()) / img_h
    _dbg(f"ty le bao phu khung anh: rong={width_ratio:.2f} cao={height_ratio:.2f} (can >= {MIN_COVERAGE_RATIO})")
    if width_ratio < MIN_COVERAGE_RATIO or height_ratio < MIN_COVERAGE_RATIO:
        _dbg("tu choi: 4 goc khong bao phu du khung anh")
        return None

    _dbg("CHAP NHAN 4 goc nay")
    return corners


def check_alignment_bytes(image_bytes: bytes) -> bool:
    color = decode_image_exif_aware(image_bytes)
    if color is None:
        return False
    return check_alignment(color)


def check_alignment(color: np.ndarray) -> bool:
    # Ban nhe cua align_image() - CHI tra ve co du 4 dau goc hay khong, khong
    # nan/warp gi ca. Dung cho tinh nang camera truc tiep: kiem tra lien tuc
    # moi ~1s xem nguoi dung da canh may khop giay chua, khong can tinh phep
    # bien doi day du moi lan (nhe hon, phan hoi nhanh hon).
    gray = cv2.cvtColor(color, cv2.COLOR_BGR2GRAY)
    img_h, img_w = gray.shape[:2]
    for threshold in THRESHOLD_ATTEMPTS:
        candidates = _find_marker_candidates(gray, threshold)
        if _pick_outer_corners(candidates, img_w, img_h) is not None:
            return True
    return False


def align_image(color: np.ndarray) -> tuple[np.ndarray, bool]:
    # Neu khong tim du 4 dau goc (o bat ky nguong nao) thi tra ve anh GOC
    # khong doi + co "False" - de detect van chay duoc (kem chinh xac hon voi
    # anh bi nghieng) thay vi bao loi cung, nhung noi tren duoc BAO CHO NGUOI
    # DUNG BIET de ho tu doi/chinh lai anh neu can, khong am tham sai.
    gray = cv2.cvtColor(color, cv2.COLOR_BGR2GRAY)
    img_h, img_w = gray.shape[:2]
    _dbg(f"===== align_image() bat dau, anh goc {img_w}x{img_h} =====")

    corners = None
    for threshold in THRESHOLD_ATTEMPTS:
        candidates = _find_marker_candidates(gray, threshold)
        corners = _pick_outer_corners(candidates, img_w, img_h)
        if corners is not None:
            _dbg(f"thanh cong o nguong={threshold}")
            break

    if corners is None:
        _dbg("THAT BAI: khong nguong nao tim duoc 4 goc hop le -> aligned=False")
        return color, False

    top_left, top_right, bottom_right, bottom_left = corners
    target_w = int(max(
        np.linalg.norm(top_right - top_left),
        np.linalg.norm(bottom_right - bottom_left),
    ))
    target_h = int(max(
        np.linalg.norm(bottom_left - top_left),
        np.linalg.norm(bottom_right - top_right),
    ))
    if target_w < 10 or target_h < 10:
        _dbg("THAT BAI: kich thuoc nan ra qua nho")
        return color, False

    dst = np.array(
        [[0, 0], [target_w - 1, 0], [target_w - 1, target_h - 1], [0, target_h - 1]],
        dtype=np.float32,
    )
    matrix = cv2.getPerspectiveTransform(corners, dst)
    warped = cv2.warpPerspective(color, matrix, (target_w, target_h))
    _dbg(f"THANH CONG: anh nan ra co kich thuoc {target_w}x{target_h}")
    return warped, True


def detect_all_markers_normalized(color: np.ndarray) -> list[tuple[float, float]]:
    # Do TOAN BO o vuong den tim duoc tren 1 anh (khong chi 4 goc), tra ve toa
    # do % (0..1) theo kich thuoc anh do - dung de "chup lai" ban do dau moc
    # cua 1 mau phieu luc tao template, va de doi chieu luc nan tinh chinh o
    # duoi. Chi lay ket qua o nguong dau tien tim du >=4 ung vien (nhat quan
    # voi cach chon goc o tren).
    gray = cv2.cvtColor(color, cv2.COLOR_BGR2GRAY)
    img_h, img_w = gray.shape[:2]
    for threshold in THRESHOLD_ATTEMPTS:
        candidates = _find_marker_candidates(gray, threshold)
        if len(candidates) >= 4:
            return [(float(x / img_w), float(y / img_h)) for x, y in candidates]
    return []


def _refine_with_markers(rough_warped: np.ndarray, template_markers: list[tuple[float, float]]) -> np.ndarray | None:
    gray = cv2.cvtColor(rough_warped, cv2.COLOR_BGR2GRAY)
    img_h, img_w = gray.shape[:2]
    _dbg(f"--- _refine_with_markers(): {len(template_markers)} dau moc trong ban do mau ---")

    detected = np.array([], dtype=np.float32).reshape(0, 2)
    for threshold in THRESHOLD_ATTEMPTS:
        candidates = _find_marker_candidates(gray, threshold)
        if len(candidates) >= 4:
            detected = candidates
            break
    if len(detected) == 0:
        _dbg("khong tim duoc dau moc nao tren anh da nan tho, bo qua tinh chinh")
        return None

    max_dist = MARKER_MATCH_MAX_DIST_RATIO * max(img_w, img_h)
    matched_detected = []
    matched_expected = []
    for norm_x, norm_y in template_markers:
        expected = np.array([norm_x * img_w, norm_y * img_h], dtype=np.float32)
        dists = np.linalg.norm(detected - expected, axis=1)
        best_idx = int(np.argmin(dists))
        if dists[best_idx] <= max_dist:
            matched_detected.append(detected[best_idx])
            matched_expected.append(expected)

    _dbg(f"khop duoc {len(matched_detected)}/{len(template_markers)} dau moc (can >= {MIN_REFINE_MATCHES})")
    if len(matched_detected) < MIN_REFINE_MATCHES:
        return None

    src = np.array(matched_detected, dtype=np.float32)
    dst = np.array(matched_expected, dtype=np.float32)
    homography, _ = cv2.findHomography(src, dst, cv2.RANSAC, 5.0)
    if homography is None:
        _dbg("findHomography that bai")
        return None

    _dbg("tinh chinh THANH CONG")
    return cv2.warpPerspective(rough_warped, homography, (img_w, img_h))


def align_image_with_template(
    color: np.ndarray, template_markers: list[tuple[float, float]] | None,
) -> tuple[np.ndarray, bool]:
    # Nan 2 buoc: (1) nan tho bang 4 goc cuc bien nhu align_image() thuong -
    # cho 1 uoc luong ban dau du gan de khop dau moc; (2) neu mau phieu co san
    # "ban do dau moc" (tu luc tao template), do lai TOAN BO dau moc tren anh
    # da nan tho, ghep cap voi ban do do, roi tinh lai 1 phep nan CHINH XAC
    # hon qua toan bo cac diem khop (RANSAC tu loai diem ghep nham). Nhieu diem
    # neo rai khap trang (khong chi 4 goc xa) nen chiu duoc truong hop 1 vai
    # diem bi che/mat net ma khong lam hong ca phep nan, va sua duoc hien tuong
    # "cang xuong duoi cang lech" do phep nan 4 diem khong bat duoc sai lech cuc
    # bo giua trang.
    rough, was_aligned = align_image(color)
    if not was_aligned:
        return color, False
    if not template_markers:
        _dbg("mau chua co ban do dau moc, dung nguyen ban nan tho")
        return rough, True

    refined = _refine_with_markers(rough, template_markers)
    if refined is not None:
        return refined, True
    # Khop dau moc that bai (vd mau chua co ban do, hoac anh qua xau khong doi
    # chieu duoc) - dung tam ban nan tho, van bao aligned=True vi da tim du 4
    # goc that.
    return rough, True
