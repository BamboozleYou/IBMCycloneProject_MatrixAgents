"""
extract_reference.py

Extracts structured text from all .pptx, .docx and .pdf files found under
reference/, and pulls one frame every 10 seconds from every .mp4 found there.

Outputs:
  reference/extracted/<stem>.pptx.txt   – slide-by-slide text
  reference/extracted/<stem>.docx.txt   – paragraph text
  reference/extracted/<stem>.pdf.txt    – page-by-page text
  reference/extracted/<stem>_frame_<N>s.jpg  – video frames
"""

from __future__ import annotations

import sys
from pathlib import Path

# ── paths ────────────────────────────────────────────────────────────────────
REFERENCE_DIR = Path(__file__).parent.parent / "reference"
EXTRACTED_DIR = REFERENCE_DIR / "extracted"
EXTRACTED_DIR.mkdir(parents=True, exist_ok=True)


# ── helpers ──────────────────────────────────────────────────────────────────

def extract_pptx(path: Path) -> None:
    from pptx import Presentation  # type: ignore

    prs = Presentation(path)
    lines: list[str] = []
    for slide_idx, slide in enumerate(prs.slides, start=1):
        lines.append(f"=== Slide {slide_idx} ===")
        for shape in slide.shapes:
            if shape.has_text_frame:
                for para in shape.text_frame.paragraphs:
                    text = para.text.strip()
                    if text:
                        lines.append(text)
        lines.append("")

    out = EXTRACTED_DIR / (path.stem + ".pptx.txt")
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"  [pptx] {out.name}  ({len(prs.slides)} slides)")


def extract_docx(path: Path) -> None:
    from docx import Document  # type: ignore

    doc = Document(path)
    lines: list[str] = []
    for para in doc.paragraphs:
        text = para.text.strip()
        if text:
            lines.append(text)

    out = EXTRACTED_DIR / (path.stem + ".docx.txt")
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"  [docx] {out.name}  ({len(lines)} paragraphs)")


def extract_pdf(path: Path) -> None:
    import pymupdf  # type: ignore

    doc = pymupdf.open(path)
    page_count = doc.page_count
    lines: list[str] = []
    for page_idx, page in enumerate(doc, start=1):
        lines.append(f"=== Page {page_idx} ===")
        text = page.get_text("text").strip()
        if text:
            lines.append(text)
        lines.append("")
    doc.close()

    out = EXTRACTED_DIR / (path.stem + ".pdf.txt")
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"  [pdf]  {out.name}  ({page_count} pages)")


def extract_mp4_frames(path: Path, interval_seconds: int = 10) -> None:
    import cv2  # type: ignore

    cap = cv2.VideoCapture(str(path))
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0:
        print(f"  [mp4]  WARNING: could not read FPS for {path.name}, skipping.")
        cap.release()
        return

    frame_interval = max(1, int(fps * interval_seconds))
    frame_number = 0
    saved = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if frame_number % frame_interval == 0:
            timestamp_s = int(frame_number / fps)
            out = EXTRACTED_DIR / f"{path.stem}_frame_{timestamp_s:04d}s.jpg"
            cv2.imwrite(str(out), frame)
            saved += 1
        frame_number += 1

    cap.release()
    print(f"  [mp4]  {path.name}  → {saved} frames saved")


# ── main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    print(f"Scanning {REFERENCE_DIR} …\n")

    for path in sorted(REFERENCE_DIR.iterdir()):
        if path.suffix.lower() == ".pptx":
            extract_pptx(path)
        elif path.suffix.lower() == ".docx":
            extract_docx(path)
        elif path.suffix.lower() == ".pdf":
            extract_pdf(path)
        elif path.suffix.lower() == ".mp4":
            extract_mp4_frames(path)

    print(f"\nDone. Outputs in {EXTRACTED_DIR}")


if __name__ == "__main__":
    main()
