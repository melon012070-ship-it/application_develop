import hashlib
import json
import os
import re
import sys
import time
from collections import Counter
from difflib import SequenceMatcher

import easyocr
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ImageOps

from config import (
    IMAGE_DIR,
    OCR_CACHE_ENABLED,
    OCR_CONFIDENCE_THRESHOLD,
    OCR_FAST_MODE,
    OCR_MAX_INPUT_WIDTH,
    OCR_NUMERIC_REREAD,
    OCR_TABLE_FIRST,
    OCR_TABLE_MIN_WIDTH_RATIO,
    OCR_PADDLE_FALLBACK_THRESHOLD,
    OCR_TILE_HEIGHT,
    OCR_TILE_OVERLAP,
    OCR_USE_PADDLE_FALLBACK,
    TEXT_DIR,
)

try:
    import cv2
except ImportError:
    cv2 = None

# PaddleOCR는 저신뢰 결과에만 사용하는 선택 기능이다. 일부 설치 조합은 import 단계에서
# ImportError가 아닌 NumPy/SciPy 관련 예외를 발생시키므로, 프로그램 시작 시 import하지 않는다.
PaddleOCR = None
paddle_import_attempted = False


ROW_TOLERANCE = 18
SPEC_ALLOWLIST = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.,:/-+%()×x±°㎜㎝ "
easy_reader = easyocr.Reader(["ko", "en"], gpu=False)
paddle_reader = None


def get_paddle_reader():
    global paddle_reader, PaddleOCR, paddle_import_attempted
    if not OCR_USE_PADDLE_FALLBACK:
        return None
    if not paddle_import_attempted:
        paddle_import_attempted = True
        try:
            from paddleocr import PaddleOCR as PaddleOCRClass
            PaddleOCR = PaddleOCRClass
        except Exception as error:
            print(f"   PaddleOCR 사용 불가 → EasyOCR만 계속 사용: {error}")
            PaddleOCR = None
    if PaddleOCR is None:
        return None
    if paddle_reader is None:
        try:
            paddle_reader = PaddleOCR(
                lang="korean",
                use_doc_orientation_classify=False,
                use_doc_unwarping=False,
                use_textline_orientation=False,
            )
        except TypeError:
            paddle_reader = PaddleOCR(lang="korean", use_angle_cls=True, show_log=False)
    return paddle_reader


def find_captured_images():
    """상품 영역을 우선하고, 상품 영역이 없을 때만 전체 화면을 사용한다."""
    products = []
    full_pages = []
    if not os.path.isdir(IMAGE_DIR):
        return []
    for root, _, files in os.walk(IMAGE_DIR):
        for filename in files:
            lower = filename.lower()
            path = os.path.join(root, filename)
            if lower.endswith("_product.png"):
                products.append(path)
            elif lower.endswith("_full_page.png"):
                full_pages.append(path)
    product_prefixes = {path.removesuffix("_product.png") for path in products}
    full_pages = [path for path in full_pages if path.removesuffix("_full_page.png") not in product_prefixes]
    return sorted(products + full_pages)


def source_prefix(image_path):
    for suffix in ("_product.png", "_full_page.png"):
        if image_path.endswith(suffix):
            return image_path.removesuffix(suffix)
    return os.path.splitext(image_path)[0]


def output_prefix(image_path):
    relative = os.path.relpath(source_prefix(image_path), IMAGE_DIR)
    return os.path.join(TEXT_DIR, relative)


def file_hash(path):
    digest = hashlib.sha256()
    with open(path, "rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    digest.update(
        f"v7-unit-aware|{OCR_TILE_HEIGHT}|{OCR_TILE_OVERLAP}|{OCR_CONFIDENCE_THRESHOLD}|{OCR_TABLE_FIRST}".encode()
    )
    return digest.hexdigest()


def load_cache():
    path = os.path.join(TEXT_DIR, ".ocr_cache.json")
    try:
        with open(path, "r", encoding="utf-8") as source:
            return json.load(source)
    except (OSError, ValueError):
        return {}


def save_cache(cache):
    os.makedirs(TEXT_DIR, exist_ok=True)
    with open(os.path.join(TEXT_DIR, ".ocr_cache.json"), "w", encoding="utf-8") as output:
        json.dump(cache, output, ensure_ascii=False, indent=2)


def normalize(text):
    replacements = {"㎜": "mm", "㎝": "cm", "×": "x", "–": "-", "—": "-"}
    for old, new in replacements.items():
        text = text.replace(old, new)
    return re.sub(r"\s+", " ", text).strip()


def preprocessing_variants(tile):
    """원본과 문서 강화 이미지를 모두 판독한다."""
    original = np.array(tile)
    gray = ImageOps.grayscale(tile)
    gray = ImageOps.autocontrast(gray, cutoff=1)
    gray = ImageEnhance.Contrast(gray).enhance(1.35)
    gray = gray.filter(ImageFilter.SHARPEN)
    if OCR_FAST_MODE:
        return [("enhanced_fast", np.array(gray))]
    variants = [("original", original), ("enhanced", np.array(gray))]

    if cv2 is not None:
        array = np.array(gray)
        binary = cv2.adaptiveThreshold(
            array, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 31, 15
        )
        # 긴 표 선만 제거하고 글자 획은 보존한다.
        horizontal = cv2.morphologyEx(
            255 - binary, cv2.MORPH_OPEN,
            cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
        )
        vertical = cv2.morphologyEx(
            255 - binary, cv2.MORPH_OPEN,
            cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))
        )
        cleaned = cv2.add(binary, horizontal)
        cleaned = cv2.add(cleaned, vertical)
        variants.append(("binary_no_lines", cleaned))
    return variants


def _cluster_positions(indices, max_gap=4):
    if not len(indices):
        return []
    groups = [[int(indices[0])]]
    for value in indices[1:]:
        value = int(value)
        if value - groups[-1][-1] <= max_gap:
            groups[-1].append(value)
        else:
            groups.append([value])
    return [round(sum(group) / len(group)) for group in groups]


def _grid_masks(gray):
    binary = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV, 31, 12
    )
    height, width = gray.shape
    horizontal = cv2.morphologyEx(
        binary, cv2.MORPH_OPEN,
        cv2.getStructuringElement(cv2.MORPH_RECT, (max(30, width // 18), 1))
    )
    vertical = cv2.morphologyEx(
        binary, cv2.MORPH_OPEN,
        cv2.getStructuringElement(cv2.MORPH_RECT, (1, max(15, min(height // 8, width // 45))))
    )
    return binary, horizontal, vertical


def _table_candidates(image):
    """축소 영상에서 격자선이 많은 사각 영역을 찾는다."""
    scale = min(1.0, 1600 / image.width)
    work = image.resize(
        (max(1, int(image.width * scale)), max(1, int(image.height * scale))),
        Image.Resampling.LANCZOS,
    )
    gray = np.array(ImageOps.grayscale(work))
    _, horizontal, vertical = _grid_masks(gray)
    grid = cv2.bitwise_or(horizontal, vertical)
    joined = cv2.morphologyEx(
        grid, cv2.MORPH_CLOSE,
        cv2.getStructuringElement(cv2.MORPH_RECT, (9, 9)), iterations=2
    )
    contours, _ = cv2.findContours(joined, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    boxes = []
    for contour in contours:
        x, y, width, height = cv2.boundingRect(contour)
        if width < work.width * OCR_TABLE_MIN_WIDTH_RATIO or height < 55:
            continue
        if height > work.height * 0.35 or width / max(1, height) > 12:
            continue
        padding = 12
        x1 = max(0, int((x - padding) / scale))
        y1 = max(0, int((y - padding) / scale))
        x2 = min(image.width, int((x + width + padding) / scale))
        y2 = min(image.height, int((y + height + padding) / scale))
        boxes.append((x1, y1, x2, y2))
    # 큰 후보부터 최대 12개만 빠르게 헤더 판독한다.
    return sorted(boxes, key=lambda box: (box[2] - box[0]) * (box[3] - box[1]), reverse=True)[:12]


def _candidate_header_score(crop):
    preview = crop.copy()
    if preview.width > 1400:
        ratio = 1400 / preview.width
        preview = preview.resize((1400, max(1, int(preview.height * ratio))), Image.Resampling.LANCZOS)
    try:
        texts = easy_reader.readtext(
            np.array(ImageOps.autocontrast(ImageOps.grayscale(preview))),
            detail=0, paragraph=False, canvas_size=1600, mag_ratio=1.0,
        )
    except Exception:
        return 0, []
    joined = " ".join(normalize(str(text)) for text in texts).casefold()
    keywords = ("상품코드", "규격", "l1", "l2", "mm", "비고")
    return sum(keyword in joined for keyword in keywords), texts


def _decimal_dot_visible(gray):
    if cv2 is None:
        return False
    array = np.array(gray)
    _, binary = cv2.threshold(array, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    height, width = array.shape
    for contour in contours:
        x, y, box_width, box_height = cv2.boundingRect(contour)
        area = cv2.contourArea(contour)
        if (
            1 <= area <= max(20, height * height * 0.025)
            and box_width <= height * 0.22
            and box_height <= height * 0.22
            and y >= height * 0.52
            and x <= width * 0.70
        ):
            return True
    return False


def _numeric_candidates(cell, cell_kind):
    """연속 숫자 축약을 막기 위해 숫자만 가로로 크게 벌려 여러 번 판독한다."""
    gray = ImageOps.autocontrast(ImageOps.grayscale(cell), cutoff=1)
    decimal_visible = cell_kind == "measurement" and _decimal_dot_visible(gray)
    target_height = max(100, gray.height * 4)
    target_width = max(240, gray.width * 5)
    stretched = gray.resize((target_width, target_height), Image.Resampling.LANCZOS)
    arrays = [("gray_stretched", np.array(stretched))]
    if cv2 is not None:
        array = np.array(stretched)
        _, otsu = cv2.threshold(array, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        adaptive = cv2.adaptiveThreshold(
            array, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 41, 13
        )
        arrays.extend([("otsu_stretched", otsu), ("adaptive_stretched", adaptive)])

    candidates = []
    for variant, array in arrays:
        allowlist = "0123456789.m" if cell_kind == "measurement" else "0123456789"
        results = easy_reader.readtext(
            array,
            detail=1,
            paragraph=False,
            decoder="beamsearch",
            allowlist=allowlist,
            canvas_size=1600,
            mag_ratio=1.0,
            width_ths=0.05,
            add_margin=0.20,
            min_size=3,
        )
        if not results:
            continue
        ordered = sorted(results, key=lambda result: box_center(result[0])[0])
        raw_value = "".join(str(result[1]) for result in ordered).replace(" ", "").lower()
        if cell_kind == "measurement":
            # 단위 mm를 숫자 7로 강제 해석하지 않게 m을 허용한 뒤 숫자 접두부만 취한다.
            match = re.match(r"(\d+(?:\.\d+)?)", raw_value)
            value = match.group(1) if match else ""
        else:
            value = re.sub(r"\D", "", raw_value)
        if value.count(".") > 1:
            first = value.find(".")
            value = value[: first + 1] + value[first + 1 :].replace(".", "")
        confidence = sum(float(result[2]) for result in ordered) / len(ordered)
        score = confidence
        if cell_kind == "product_code":
            score += 1.2 if len(value) == 7 and value.isdigit() else -0.8 * abs(len(value) - 7)
        elif cell_kind == "measurement":
            score += 0.45 if "m" in raw_value else -0.20
            if decimal_visible:
                score += 0.8 if "." in value else -0.8
            score += 0.15 if 1 <= len(value.replace(".", "")) <= 4 else -0.3
        elif cell_kind == "integer":
            score += 0.2 if value.isdigit() and 2 <= len(value) <= 4 else -0.3
        candidates.append((score, confidence, value, variant, decimal_visible))
    return sorted(candidates, reverse=True)


def _cell_text(cell, cell_kind="text"):
    if cell.width < 4 or cell.height < 4:
        return "", 0.0
    if cell_kind in ("product_code", "measurement", "integer"):
        candidates = _numeric_candidates(cell, cell_kind)
        if not candidates:
            return "", 0.0
        _, confidence, value, _, _ = candidates[0]
        if cell_kind == "measurement" and value:
            value += "mm"
        return value, confidence

    scale = min(3.0, max(1.5, 90 / max(1, cell.height)))
    enlarged = cell.resize(
        (max(1, int(cell.width * scale)), max(1, int(cell.height * scale))),
        Image.Resampling.LANCZOS,
    )
    enhanced = ImageOps.autocontrast(ImageOps.grayscale(enlarged), cutoff=1)
    enhanced = ImageEnhance.Contrast(enhanced).enhance(1.35)
    kwargs = {
        "detail": 1,
        "paragraph": False,
        "decoder": "beamsearch",
        "canvas_size": 1600,
        "mag_ratio": 1.0,
    }
    results = easy_reader.readtext(np.array(enhanced), **kwargs)
    if not results:
        return "", 0.0
    ordered = sorted(results, key=lambda result: box_center(result[0])[0])
    text = normalize(" ".join(str(result[1]) for result in ordered))
    confidence = sum(float(result[2]) for result in ordered) / len(ordered)
    return text, confidence


def _normalize_table_rows(rows):
    """알려진 규격표 열 형식으로 OCR 결과를 정규화한다."""
    if not rows:
        return rows
    column_count = max(len(row) for row in rows)
    header_joined = " ".join(rows[0]).casefold()
    is_product_spec = column_count == 6 and (
        "상품" in header_joined or "규격" in header_joined or "l1" in header_joined
    )
    if not is_product_spec:
        return rows

    rows[0] = ["상품코드", "규격(mm)", "L1(mm)", "L2(mm)", "A(mm)", "비고"]
    corrections = {
        "작은침": "작은힘",
        "근효과": "큰효과",
        "소랑생산": "소량생산",
        "책점": "책정",
    }
    for row in rows[1:]:
        while len(row) < 6:
            row.append("")
        row[0] = re.sub(r"\D", "", row[0])
        for column in (1, 2):
            value = row[column].replace(" ", "")
            match = re.search(r"\d+(?:\.\d+)?", value)
            row[column] = f"{match.group(0)}mm" if match else value
        for column in (3, 4):
            match = re.search(r"\d+", row[column].replace(" ", ""))
            row[column] = match.group(0) if match else row[column]
        for wrong, correct in corrections.items():
            row[5] = row[5].replace(wrong, correct)
    return rows


def extract_spec_table(image_path):
    """규격표를 찾아 원본 해상도에서 셀별 OCR한다."""
    if not OCR_TABLE_FIRST or cv2 is None:
        return None
    with Image.open(image_path) as source:
        image = source.convert("RGB")
    ranked = []
    for box in _table_candidates(image):
        crop = image.crop(box)
        score, preview_text = _candidate_header_score(crop)
        ranked.append((score, (box[2] - box[0]) * (box[3] - box[1]), box, preview_text))
    if not ranked:
        return None
    ranked.sort(key=lambda value: (value[0], value[1]), reverse=True)
    score, _, box, preview_text = ranked[0]
    if score < 2:
        return None

    crop = image.crop(box)
    gray = np.array(ImageOps.grayscale(crop))
    _, horizontal, vertical = _grid_masks(gray)
    x_projection = np.count_nonzero(vertical, axis=0)
    y_projection = np.count_nonzero(horizontal, axis=1)
    x_lines = _cluster_positions(np.where(x_projection >= crop.height * 0.28)[0])
    y_lines = _cluster_positions(np.where(y_projection >= crop.width * 0.28)[0])
    if len(x_lines) < 3 or len(y_lines) < 3:
        return None

    rows = []
    details = []
    for row_index, (top, bottom) in enumerate(zip(y_lines, y_lines[1:])):
        if bottom - top < 10:
            continue
        row = []
        for column_index, (left, right) in enumerate(zip(x_lines, x_lines[1:])):
            if right - left < 10:
                continue
            margin = 3
            cell = crop.crop((left + margin, top + margin, right - margin, bottom - margin))
            if row_index > 0 and column_index == 0:
                cell_kind = "product_code"
            elif row_index > 0 and column_index in (3, 4):
                cell_kind = "integer"
            elif row_index > 0 and column_index in (1, 2):
                cell_kind = "measurement"
            else:
                cell_kind = "text"
            text, confidence = _cell_text(cell, cell_kind=cell_kind)
            row.append(text)
            details.append(
                {
                    "text": text,
                    "confidence": confidence,
                    "row": row_index,
                    "column": column_index,
                    "x": float(box[0] + (left + right) / 2),
                    "y": float(box[1] + (top + bottom) / 2),
                    "box": [
                        [float(box[0] + left), float(box[1] + top)],
                        [float(box[0] + right), float(box[1] + top)],
                        [float(box[0] + right), float(box[1] + bottom)],
                        [float(box[0] + left), float(box[1] + bottom)],
                    ],
                    "engine": "easyocr_cell",
                    "variant": f"table_cell_{cell_kind}",
                }
            )
        if any(value for value in row):
            rows.append(row)

    if len(rows) < 2:
        return None
    rows = _normalize_table_rows(rows)
    crop_path = source_prefix(image_path) + "_table_crop.png"
    crop.save(crop_path)
    table_text = "\n".join("\t".join(row) for row in rows)
    return {
        "text": table_text,
        "details": details,
        "box": box,
        "crop_path": crop_path,
        "header_score": score,
        "preview_text": [str(value) for value in preview_text],
        "rows": rows,
    }


def box_center(box):
    return (
        sum(point[0] for point in box) / len(box),
        sum(point[1] for point in box) / len(box),
    )


def easy_read(array, top, variant, inverse_scale=1.0):
    results = easy_reader.readtext(
        array,
        detail=1,
        paragraph=False,
        decoder="beamsearch",
        canvas_size=2048,
        mag_ratio=1.0,
        contrast_ths=0.05,
        adjust_contrast=0.7,
        text_threshold=0.6,
        low_text=0.3,
        link_threshold=0.3,
    )
    items = []
    for box, text, confidence in results:
        x, y = box_center(box)
        x *= inverse_scale
        y *= inverse_scale
        items.append(
            {
                "text": normalize(text),
                "confidence": float(confidence),
                "x": float(x),
                "y": float(y + top),
                "box": [
                    [float(px * inverse_scale), float(py * inverse_scale + top)]
                    for px, py in box
                ],
                "engine": "easyocr",
                "variant": variant,
            }
        )
    return items


def same_position(left, right, tolerance=28):
    return abs(left["x"] - right["x"]) <= tolerance and abs(left["y"] - right["y"]) <= tolerance


def fuse_candidates(items):
    """같은 위치 후보 중 신뢰도가 높은 판독을 선택한다."""
    fused = []
    for item in sorted(items, key=lambda value: value["confidence"], reverse=True):
        existing = next((old for old in fused if same_position(old, item)), None)
        if existing is None:
            fused.append(item)
        elif normalize(existing["text"]).casefold() == normalize(item["text"]).casefold():
            existing["confidence"] = max(existing["confidence"], item["confidence"])
        elif item["confidence"] > existing["confidence"] + 0.08:
            fused.remove(existing)
            fused.append(item)
    return sorted(fused, key=lambda value: (value["y"], value["x"]))


def looks_numeric_spec(text):
    compact = re.sub(r"\s+", "", text)
    if len(compact) < 2:
        return False
    digit_ratio = sum(char.isdigit() for char in compact) / len(compact)
    return digit_ratio >= 0.40 or bool(re.fullmatch(r"(?i)(IP|GTIN)?[0-9OILUS.,:/+%×x-]+", compact))


def crop_from_box(image, item, padding=8):
    xs = [point[0] for point in item["box"]]
    ys = [point[1] for point in item["box"]]
    return image.crop(
        (
            max(0, int(min(xs)) - padding),
            max(0, int(min(ys)) - padding),
            min(image.width, int(max(xs)) + padding),
            min(image.height, int(max(ys)) + padding),
        )
    )


def reread_numeric_specs(image, items):
    if not OCR_NUMERIC_REREAD:
        return items
    for item in items:
        if not looks_numeric_spec(item["text"]):
            continue
        crop = crop_from_box(image, item).resize(
            (max(80, crop_from_box(image, item).width * 2), max(40, crop_from_box(image, item).height * 2))
        )
        results = easy_reader.readtext(
            np.array(crop), detail=1, paragraph=False,
            decoder="beamsearch", allowlist=SPEC_ALLOWLIST
        )
        if not results:
            continue
        _, candidate, confidence = max(results, key=lambda result: result[2])
        candidate = normalize(candidate)
        # 제한 문자 재판독이 더 확실하거나 기존 값의 모호 문자를 없앤 경우에만 교체한다.
        ambiguous_before = len(re.findall(r"[OUIl]", item["text"]))
        ambiguous_after = len(re.findall(r"[OUIl]", candidate))
        if confidence >= item["confidence"] + 0.05 or (
            confidence >= 0.55 and ambiguous_after < ambiguous_before
        ):
            item["alternatives"] = [{"text": item["text"], "confidence": item["confidence"]}]
            item["text"] = candidate
            item["confidence"] = float(confidence)
            item["variant"] = "numeric_reread"
    return items


def paddle_read_crop(crop):
    engine = get_paddle_reader()
    if engine is None:
        return None
    try:
        result = engine.ocr(np.array(crop), cls=True)
        candidates = []
        for page in result or []:
            for entry in page or []:
                if isinstance(entry, (list, tuple)) and len(entry) >= 2:
                    value = entry[1]
                    if isinstance(value, (list, tuple)) and len(value) >= 2:
                        candidates.append((normalize(str(value[0])), float(value[1])))
        return max(candidates, key=lambda value: value[1]) if candidates else None
    except Exception:
        return None


def apply_paddle_fallback(image, items):
    if not OCR_USE_PADDLE_FALLBACK:
        return items
    if get_paddle_reader() is None:
        return items
    for item in items:
        if item["confidence"] >= OCR_PADDLE_FALLBACK_THRESHOLD:
            continue
        candidate = paddle_read_crop(crop_from_box(image, item, padding=12))
        if candidate and candidate[1] > item["confidence"] + 0.05:
            item.setdefault("alternatives", []).append(
                {"text": item["text"], "confidence": item["confidence"]}
            )
            item["text"], item["confidence"] = candidate
            item["engine"] = "paddleocr"
            item["variant"] = "low_confidence_fallback"
    return items


def group_rows(items):
    rows = []
    for item in sorted(items, key=lambda value: (value["y"], value["x"])):
        row = next((candidate for candidate in rows if abs(candidate["y"] - item["y"]) <= ROW_TOLERANCE), None)
        if row is None:
            rows.append({"y": item["y"], "items": [item]})
        else:
            row["items"].append(item)
            row["y"] = sum(value["y"] for value in row["items"]) / len(row["items"])
    return [sorted(row["items"], key=lambda value: value["x"]) for row in sorted(rows, key=lambda row: row["y"])]


def run_ocr(image_path):
    with Image.open(image_path) as source:
        image = source.convert("RGB")
    step = OCR_TILE_HEIGHT - OCR_TILE_OVERLAP
    candidates = []
    for tile_index, top in enumerate(range(0, image.height, step), 1):
        bottom = min(top + OCR_TILE_HEIGHT, image.height)
        tile = image.crop((0, top, image.width, bottom))
        scale = min(1.0, OCR_MAX_INPUT_WIDTH / max(1, tile.width))
        if scale < 1.0:
            tile = tile.resize(
                (max(1, int(tile.width * scale)), max(1, int(tile.height * scale))),
                Image.Resampling.LANCZOS,
            )
        inverse_scale = 1.0 / scale
        count = 0
        for variant, array in preprocessing_variants(tile):
            values = easy_read(array, top, variant, inverse_scale)
            candidates.extend(values)
            count += len(values)
        print(f"    타일 {tile_index}: 후보 {count}개")
        if bottom == image.height:
            break

    items = fuse_candidates(candidates)
    items = reread_numeric_specs(image, items)
    items = apply_paddle_fallback(image, items)
    accepted = [item for item in items if item["confidence"] >= OCR_CONFIDENCE_THRESHOLD]
    rejected = [item for item in items if item["confidence"] < OCR_CONFIDENCE_THRESHOLD]
    lines = ["\t".join(item["text"] for item in row) for row in group_rows(accepted)]
    return "\n".join(lines), accepted, rejected


def token_metrics(reference, hypothesis):
    pattern = r"[0-9A-Za-z가-힣]+(?:[.,:/×x-][0-9A-Za-z가-힣]+)*"
    reference_tokens = Counter(re.findall(pattern, reference.casefold()))
    hypothesis_tokens = Counter(re.findall(pattern, hypothesis.casefold()))
    overlap = sum((reference_tokens & hypothesis_tokens).values())
    recall = overlap / max(1, sum(reference_tokens.values()))
    precision = overlap / max(1, sum(hypothesis_tokens.values()))
    similarity = SequenceMatcher(
        None, re.sub(r"\s+", "", reference.casefold()),
        re.sub(r"\s+", "", hypothesis.casefold()), autojunk=False
    ).ratio()
    return {
        "reference_tokens": sum(reference_tokens.values()),
        "ocr_tokens": sum(hypothesis_tokens.values()),
        "matched_tokens": overlap,
        "token_recall": round(recall, 4),
        "token_precision": round(precision, 4),
        "character_sequence_similarity": round(similarity, 4),
    }


def load_dom(image_path):
    if image_path.endswith("_product.png"):
        path = source_prefix(image_path) + "_product_dom.txt"
    else:
        path = source_prefix(image_path) + "_dom.txt"
    try:
        with open(path, "r", encoding="utf-8") as source:
            return source.read(), path
    except OSError:
        return None, path


def ocr_image(image_path):
    started = time.time()
    table_result = extract_spec_table(image_path)
    if table_result is not None:
        text = table_result["text"]
        accepted = [
            item for item in table_result["details"]
            if item["confidence"] >= OCR_CONFIDENCE_THRESHOLD
        ]
        rejected = [
            item for item in table_result["details"]
            if item["confidence"] < OCR_CONFIDENCE_THRESHOLD
        ]
        extraction_mode = "detected_table_cells"
        print(f"   규격표 자동 검출: {table_result['crop_path']}")
    else:
        text, accepted, rejected = run_ocr(image_path)
        extraction_mode = "full_image_fallback"
    prefix = output_prefix(image_path)
    os.makedirs(os.path.dirname(prefix), exist_ok=True)
    with open(prefix + "_ocr.txt", "w", encoding="utf-8") as output:
        output.write(text)
    with open(prefix + "_detail.json", "w", encoding="utf-8") as output:
        json.dump(
            {
                "extraction_mode": extraction_mode,
                "table": table_result,
                "accepted": accepted,
                "low_confidence": rejected,
            },
            output, ensure_ascii=False, indent=2,
        )

    dom_text, dom_path = load_dom(image_path)
    final_text = dom_text if dom_text is not None else text
    final_source = "dom" if dom_text is not None else "ocr"
    with open(prefix + ".txt", "w", encoding="utf-8") as output:
        output.write(final_text)

    validation = {
        "status": "compared" if dom_text is not None else "no_dom_reference",
        "extraction_mode": extraction_mode,
        "table_crop_path": table_result["crop_path"] if table_result else None,
        "final_text_source": final_source,
        "dom_path": dom_path,
        "accepted_boxes": len(accepted),
        "low_confidence_boxes": len(rejected),
        "easyocr_boxes": sum(item["engine"] == "easyocr" for item in accepted),
        "paddleocr_boxes": sum(item["engine"] == "paddleocr" for item in accepted),
        "elapsed_seconds": round(time.time() - started, 2),
    }
    if dom_text is not None:
        validation.update(token_metrics(dom_text, text))
    with open(prefix + "_validation.json", "w", encoding="utf-8") as output:
        json.dump(validation, output, ensure_ascii=False, indent=2)
    print(f"   최종({final_source}): {prefix}.txt")
    return validation


def ocr_all():
    # 파일 경로를 인자로 주면 해당 이미지 한 장만 처리한다.
    # 인자가 없을 때만 IMAGE_DIR 전체를 자동 검색한다.
    if len(sys.argv) > 1:
        requested = os.path.abspath(sys.argv[1])
        if not os.path.isfile(requested):
            print(f"지정한 이미지가 없습니다: {requested}")
            return
        images = [requested]
    else:
        images = find_captured_images()
    if not images:
        print(f"OCR 대상이 없습니다: {IMAGE_DIR}")
        return
    cache = load_cache()
    summary = []
    for image_path in images:
        digest = file_hash(image_path)
        prefix = output_prefix(image_path)
        if OCR_CACHE_ENABLED and cache.get(image_path) == digest and os.path.exists(prefix + "_validation.json"):
            with open(prefix + "_validation.json", "r", encoding="utf-8") as source:
                validation = json.load(source)
            validation["cache_hit"] = True
            print(f"캐시 사용: {image_path}")
        else:
            print(f"\nOCR: {image_path}")
            try:
                validation = ocr_image(image_path)
                validation["cache_hit"] = False
                cache[image_path] = digest
                save_cache(cache)
            except Exception as error:
                print(f"   실패: {error}")
                validation = {"status": "error", "error": str(error), "cache_hit": False}
        summary.append({"image": image_path, **validation})
    os.makedirs(TEXT_DIR, exist_ok=True)
    with open(os.path.join(TEXT_DIR, "ocr_summary.json"), "w", encoding="utf-8") as output:
        json.dump(summary, output, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    ocr_all()
