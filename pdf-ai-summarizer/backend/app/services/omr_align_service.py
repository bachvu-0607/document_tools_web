import cv2
import numpy as np

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
    for contour in contours:
        area = cv2.contourArea(contour)
        area_ratio = area / img_area
        if not (MIN_MARKER_AREA_RATIO <= area_ratio <= MAX_MARKER_AREA_RATIO):
            continue
        x, y, box_w, box_h = cv2.boundingRect(contour)
        if box_h == 0:
            continue
        aspect = box_w / box_h
        if not (MIN_ASPECT_RATIO <= aspect <= MAX_ASPECT_RATIO):
            continue
        solidity = area / (box_w * box_h)
        if solidity < MIN_SOLIDITY:
            continue
        candidates.append((x + box_w / 2, y + box_h / 2))

    return np.array(candidates, dtype=np.float32)


def _pick_outer_corners(candidates: np.ndarray) -> np.ndarray | None:
    # Trong so cac o vuong den tim duoc (ca dau goc trang lan dau moc noi bo
    # giua cac khoi), 4 goc THAT cua trang luon la 4 diem CUC BIEN nhat - tong
    # x+y nho nhat/lon nhat va hieu x-y nho nhat/lon nhat - vi moi diem noi bo
    # nam gan tam trang hon nhieu so voi 4 goc ngoai cung.
    if len(candidates) < 4:
        return None

    sums = candidates[:, 0] + candidates[:, 1]
    diffs = candidates[:, 0] - candidates[:, 1]

    top_left = candidates[np.argmin(sums)]
    bottom_right = candidates[np.argmax(sums)]
    top_right = candidates[np.argmax(diffs)]
    bottom_left = candidates[np.argmin(diffs)]

    corners = np.array([top_left, top_right, bottom_right, bottom_left], dtype=np.float32)
    # 4 diem phai thuc su phan biet (khac o vuong bi trung/gan nhau do anh qua
    # it dau moc de chon) - neu 2 "goc" trung gan nhau thi coi nhu khong tim
    # duoc, tranh nan anh ra ket qua vo nghia.
    for i in range(4):
        for j in range(i + 1, 4):
            if np.linalg.norm(corners[i] - corners[j]) < 10:
                return None

    # Kiem tra hinh dang co hop ly khong (2 canh doi dien khong duoc lech qua
    # nhieu) - neu khong, nhieu kha nang thieu mat 1 goc that trong khung hinh
    # va thuat toan da lay nham 1 diem khac lam goc thay the.
    top_len = np.linalg.norm(top_right - top_left)
    bottom_len = np.linalg.norm(bottom_right - bottom_left)
    left_len = np.linalg.norm(bottom_left - top_left)
    right_len = np.linalg.norm(bottom_right - top_right)
    for a, b in ((top_len, bottom_len), (left_len, right_len)):
        if a <= 0 or b <= 0 or max(a, b) / min(a, b) > MAX_SIDE_RATIO:
            return None

    return corners


def check_alignment_bytes(image_bytes: bytes) -> bool:
    array = np.frombuffer(image_bytes, dtype=np.uint8)
    color = cv2.imdecode(array, cv2.IMREAD_COLOR)
    if color is None:
        return False
    return check_alignment(color)


def check_alignment(color: np.ndarray) -> bool:
    # Ban nhe cua align_image() - CHI tra ve co du 4 dau goc hay khong, khong
    # nan/warp gi ca. Dung cho tinh nang camera truc tiep: kiem tra lien tuc
    # moi ~1s xem nguoi dung da canh may khop giay chua, khong can tinh phep
    # bien doi day du moi lan (nhe hon, phan hoi nhanh hon).
    gray = cv2.cvtColor(color, cv2.COLOR_BGR2GRAY)
    for threshold in THRESHOLD_ATTEMPTS:
        candidates = _find_marker_candidates(gray, threshold)
        if _pick_outer_corners(candidates) is not None:
            return True
    return False


def align_image(color: np.ndarray) -> tuple[np.ndarray, bool]:
    # Neu khong tim du 4 dau goc (o bat ky nguong nao) thi tra ve anh GOC
    # khong doi + co "False" - de detect van chay duoc (kem chinh xac hon voi
    # anh bi nghieng) thay vi bao loi cung, nhung noi tren duoc BAO CHO NGUOI
    # DUNG BIET de ho tu doi/chinh lai anh neu can, khong am tham sai.
    gray = cv2.cvtColor(color, cv2.COLOR_BGR2GRAY)

    corners = None
    for threshold in THRESHOLD_ATTEMPTS:
        candidates = _find_marker_candidates(gray, threshold)
        corners = _pick_outer_corners(candidates)
        if corners is not None:
            break

    if corners is None:
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
        return color, False

    dst = np.array(
        [[0, 0], [target_w - 1, 0], [target_w - 1, target_h - 1], [0, target_h - 1]],
        dtype=np.float32,
    )
    matrix = cv2.getPerspectiveTransform(corners, dst)
    warped = cv2.warpPerspective(color, matrix, (target_w, target_h))
    return warped, True
