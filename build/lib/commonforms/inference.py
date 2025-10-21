from __future__ import annotations
from ultralytics import YOLO
from pathlib import Path
from huggingface_hub import hf_hub_download

from commonforms.utils import BoundingBox, Page, Widget
from commonforms.form_creator import PyPdfFormCreator
from commonforms.exceptions import EncryptedPdfError

import formalpdf
import pypdfium2


# our mapping from (model_name, fast) to (repo_id, filename) for the huggingface hub
models = {
    ("FFDNET-S", True): ("jbarrow/FFDNet-S-cpu", "FFDNet-S.onnx"),
    ("FFDNET-S", False): ("jbarrow/FFDNet-S", "FFDNet-S.pt"),
    ("FFDNET-L", True): ("jbarrow/FFDNet-L-cpu", "FFDNet-L.onnx"),
    ("FFDNET-L", False): ("jbarrow/FFDNet-L", "FFDNet-L.pt"),
}


class FFDNetDetector:
    def __init__(
        self, model_or_path: str, device: int | str = "cpu", fast: bool = False
    ) -> None:
        self.device = device
        self.fast = fast

        model_path = self.get_model_path(model_or_path, device, fast)
        self.model = YOLO(model_path, task="detect")

        self.id_to_cls = {0: "TextBox", 1: "ChoiceButton", 2: "Signature"}

    def get_model_path(
        self, model_or_path: str, device: int | str = "cpu", fast: bool = False
    ) -> str:
        """
        Construct the path to the model weights based on:
         (a) the requested model (in the package or external path)
         (b) --fast (if enabled, use ONNX, otherwise use pt)
        """
        model_upper = model_or_path.upper()
        if model_upper in ["FFDNET-S", "FFDNET-L"]:
            # download the model, will just use the cached version if it already exists
            repo_id, filename = models[(model_upper, fast)] 
            model_path = hf_hub_download(repo_id=repo_id, filename=filename) 
        else:
            model_path = model_or_path

        return model_path

    def extract_widgets(
        self,
        pages: list[Page],
        confidence: float = 0.3,
        image_size: int = 1600,
        *,
        nms_iou: float = 0.6,
        postprocess_iou: float = 0.5,
        min_box_area: float = 0.00025,
    ) -> dict[int, list[Widget]]:
        if self.fast:
            # overrides the image size to 1216, since that's all ONNX supports
            results = [
                self.model.predict(
                    p.image, iou=nms_iou, conf=confidence, augment=False, imgsz=1216
                )
                for p in pages
            ]
        else:
            results = self.model.predict(
                [p.image for p in pages],
                iou=nms_iou,
                conf=confidence,
                augment=True,
                imgsz=image_size,
                device=self.device,
            )

        widgets = {}
        for page_ix, result in enumerate(results):
            if isinstance(result, list):
                result = result[0]
            # no predictions, skip page
            if result is None or result.boxes is None:
                continue

            page_widgets: list[Widget] = []
            # Filter tiny boxes and build widget list
            for box in result.boxes.cpu().numpy():
                x, y, w, h = box.xywhn[0]
                area = float(w) * float(h)
                if area < min_box_area:
                    continue

                cls_id = int(box.cls.item())
                widget_type = self.id_to_cls[cls_id]

                page_widgets.append(
                    Widget(
                        widget_type=widget_type,
                        bounding_box=BoundingBox.from_yolo(cx=x, cy=y, w=w, h=h),
                        page=page_ix,
                    )
                )

            # Additional lightweight dedup in case upstream NMS leaves overlaps
            page_widgets = dedupe_widgets(page_widgets, iou_threshold=postprocess_iou)

            # Sort into reading order to improve tab navigation
            widgets[page_ix] = sort_widgets(page_widgets)

        return widgets


def sort_widgets(widgets: list[Widget]) -> list[Widget]:
    """
    Sort widgets in approximate reading order (left-to-right/top-to-bottom)
    which makes the LLMs less likely to mess up.
    """
    # Sort first by y coordinate, then x coordinate for reading order
    sorted_widgets = sorted(
        widgets,
        key=lambda w: (
            round(
                w.bounding_box.y0, 3
            ),  # Round to handle minor vertical alignment differences
            w.bounding_box.x0,
        ),
    )

    # Find rows of widgets by grouping those with similar y coordinates
    y_threshold = 0.01  # Threshold for considering widgets on same line
    lines = []
    current_line = []

    for widget in sorted_widgets:
        if (
            not current_line
            or abs(widget.bounding_box.y0 - current_line[0].bounding_box.y0)
            < y_threshold
        ):
            current_line.append(widget)
        else:
            # Sort widgets in line by x coordinate
            current_line.sort(key=lambda w: w.bounding_box.x0)
            lines.append(current_line)
            current_line = [widget]

    if current_line:
        current_line.sort(key=lambda w: w.bounding_box.x0)
        lines.append(current_line)

    # Flatten the lines back into single list
    return [widget for line in lines for widget in line]


def _iou(a: BoundingBox, b: BoundingBox) -> float:
    # intersection
    ix0 = max(a.x0, b.x0)
    iy0 = max(a.y0, b.y0)
    ix1 = min(a.x1, b.x1)
    iy1 = min(a.y1, b.y1)
    iw = max(0.0, ix1 - ix0)
    ih = max(0.0, iy1 - iy0)
    inter = iw * ih
    if inter <= 0:
        return 0.0
    # union
    aw = max(0.0, a.x1 - a.x0)
    ah = max(0.0, a.y1 - a.y0)
    bw = max(0.0, b.x1 - b.x0)
    bh = max(0.0, b.y1 - b.y0)
    union = aw * ah + bw * bh - inter
    if union <= 0:
        return 0.0
    return inter / union


def dedupe_widgets(widgets: list[Widget], iou_threshold: float = 0.5) -> list[Widget]:
    # Class-wise greedy NMS on Widgets based on IoU only (no scores available)
    kept: list[Widget] = []
    for w in widgets:
        duplicate = False
        for k in kept:
            if w.widget_type == k.widget_type and _iou(w.bounding_box, k.bounding_box) >= iou_threshold:
                duplicate = True
                break
        if not duplicate:
            kept.append(w)
    return kept


def render_pdf(pdf_path: str) -> list[Page]:
    pages = []
    doc = formalpdf.open(pdf_path)
    try:
        for page in doc:
            image = page.render()
            pages.append(Page(image=image, width=image.width, height=image.height))
        return pages
    finally:
        doc.document.close()


def prepare_form(
    input_path: str | Path,
    output_path: str | Path,
    *,
    model_or_path: str = "FFDNet-L",
    keep_existing_fields: bool = False,
    use_signature_fields: bool = False,
    device: int | str = "cpu",
    image_size: int = 1600,
    confidence: float = 0.3,
    fast: bool = False,
    multiline: bool = False,
    # Advanced tuning
    nms_iou: float = 0.6,
    postprocess_iou: float = 0.5,
    min_box_area: float = 0.00025,
):
    detector = FFDNetDetector(model_or_path, device=device, fast=fast)

    try:
        pages = render_pdf(input_path)
    except pypdfium2._helpers.misc.PdfiumError:
        raise EncryptedPdfError

    results = detector.extract_widgets(
        pages,
        confidence=confidence,
        image_size=image_size,
        nms_iou=nms_iou,
        postprocess_iou=postprocess_iou,
        min_box_area=min_box_area,
    )

    writer = PyPdfFormCreator(input_path)
    if not keep_existing_fields:
        writer.clear_existing_fields()

    text_field_count = 0
    for page_ix, widgets in results.items():
        for i, widget in enumerate(widgets):
            name = f"{widget.widget_type.lower()}_{widget.page}_{i}"

            if widget.widget_type == "TextBox":
                writer.add_text_box(name, page_ix, widget.bounding_box, multiline=multiline)
                text_field_count += 1
            elif widget.widget_type == "ChoiceButton":
                writer.add_checkbox(name, page_ix, widget.bounding_box)
            elif widget.widget_type == "Signature":
                if use_signature_fields:
                    writer.add_signature(name, page_ix, widget.bounding_box)
                else:
                    writer.add_text_box(name, page_ix, widget.bounding_box)
                    text_field_count += 1

    # Attach a document-level metadata entry with the count of text boxes
    try:
        writer.add_text_fields_count_metadata(text_field_count)
    except Exception:
        # In case an older writer implementation doesn't support metadata, ignore
        pass

    writer.save(output_path)
    writer.close()
