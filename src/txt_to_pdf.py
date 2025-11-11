import os
import chardet
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont

# 自动路径
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OCR_TXT_DIR = os.path.join(BASE_DIR, "data", "ocr_output_txt")


def detect_encoding(file_path):
    with open(file_path, 'rb') as f:
        raw_data = f.read(4096)
    return chardet.detect(raw_data)['encoding']


def register_chinese_font():
    pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))


def txt_to_pdf(txt_path, pdf_path, font_name="STSong-Light"):
    encoding = detect_encoding(txt_path)
    print(f"[encoding] {txt_path} → {encoding}")

    c = canvas.Canvas(pdf_path, pagesize=A4)
    width, height = A4

    x = 40
    y = height - 40
    max_width = width - 80
    line_height = 20

    with open(txt_path, "r", encoding=encoding, errors="ignore") as f:
        for line in f:
            stripped = line.rstrip("\n").replace("\u3000", " ")
            if stripped == "":
                y -= line_height
                continue

            if pdfmetrics.stringWidth(stripped, font_name, 12) < max_width:
                c.drawString(x, y, stripped)
                y -= line_height
            else:
                # 自动换行
                while stripped:
                    for i in range(len(stripped)):
                        if pdfmetrics.stringWidth(stripped[:i+1], font_name, 12) > max_width:
                            c.drawString(x, y, stripped[:i])
                            stripped = stripped[i:]
                            y -= line_height
                            break
                    else:
                        c.drawString(x, y, stripped)
                        stripped = ""
                        y -= line_height

    c.save()


def convert_all_txt_in_folder(folder_path):
    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.lower().endswith(".txt"):
                txt_file = os.path.join(root, file)
                pdf_file = os.path.splitext(txt_file)[0] + ".pdf"

                print("processing", txt_file)
                txt_to_pdf(txt_file, pdf_file)
                print("output:", pdf_file)


def main():
    register_chinese_font()
    convert_all_txt_in_folder(OCR_TXT_DIR)


if __name__ == "__main__":
    main()
