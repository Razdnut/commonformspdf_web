from commonforms.inference import prepare_form
from argparse import ArgumentParser
from pathlib import Path


def main():
    parser = ArgumentParser(
        prog="commonforms", description="Automatically Prepare a Fillable PDF Form"
    )
    parser.add_argument(
        "input",
        type=Path,
        help="Path to the input file (only .pdf files are supported for now.)",
    )
    parser.add_argument("output", type=Path, help="Path to save the output PDF file.")
    parser.add_argument(
        "--model",
        type=str,
        default="FFDNet-L",
        help="Model (FFDNet-L/FFDNet-S) or path to a different .pt model",
    )
    parser.add_argument(
        "--keep-existing-fields",
        action="store_true",
        help="If true, keep existing form fields on the PDF",
    )
    parser.add_argument(
        "--use-signature-fields",
        action="store_true",
        help="If true, use signature fields instead of text fields for detected signatures",
    )
    parser.add_argument(
        "--device", default="cpu", help="Which device to use for inference."
    )
    parser.add_argument(
        "--image-size",
        type=int,
        default=1600,
        dest="image_size",
        help="Image size for inference (default: 1600)",
    )
    parser.add_argument(
        "--confidence",
        type=float,
        default=0.3,
        help="Confidence threshold for detection (default: 0.3)",
    )
    parser.add_argument(
        "--fast",
        action="store_true",
        help="If running on a CPU, you can use --fast to get a 50% speedup with a small accuracy penalty",
    )
    parser.add_argument(
        "--multiline",
        action="store_true",
        help="If you want the detected textboxes to allow multiline inputs.",
    )
    parser.add_argument(
        "--nms-iou",
        type=float,
        default=0.6,
        dest="nms_iou",
        help="IoU threshold for model NMS (default: 0.6)",
    )
    parser.add_argument(
        "--postprocess-iou",
        type=float,
        default=0.5,
        dest="postprocess_iou",
        help="IoU threshold for extra dedup after model NMS (default: 0.5)",
    )
    parser.add_argument(
        "--min-box-area",
        type=float,
        default=0.00025,
        dest="min_box_area",
        help="Minimum normalized area to keep a detection (default: 0.00025)",
    )

    args = parser.parse_args()

    prepare_form(
        args.input,
        args.output,
        model_or_path=args.model,
        keep_existing_fields=args.keep_existing_fields,
        use_signature_fields=args.use_signature_fields,
        device=args.device,
        image_size=args.image_size,
        confidence=args.confidence,
        fast=args.fast,
        multiline=args.multiline,
        nms_iou=args.nms_iou,
        postprocess_iou=args.postprocess_iou,
        min_box_area=args.min_box_area,
    )


if __name__ == "__main__":
    main()
