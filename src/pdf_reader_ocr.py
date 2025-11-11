import asyncio
import os
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io

# 项目根目录
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OCR_TXT_DIR = os.path.join(BASE_DIR, "data", "ocr_output_txt")
OUTPUT_DIR = os.path.join(BASE_DIR, "data", "final_output_txt")

# 设置 Tesseract-OCR 的安装路径（请根据你的实际安装位置修改）
#pytesseract.pytesseract.tesseract_cmd = r"C:\Users\Emma\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"


def find_pdf_files_recursive(folder_path):
    """递归查找文件夹中的所有 PDF 文件"""
    pdf_files = []
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.lower().endswith('.pdf'):
                full_path = os.path.join(root, file)
                pdf_files.append(full_path)
    return pdf_files


def ocr_extract_pdf(pdf_path):
    """对 PDF 的每一页进行 OCR 并返回完整文本"""
    print(f"ocr processing：{pdf_path}")
    doc = fitz.open(pdf_path)
    full_text = ""

    for page_idx in range(len(doc)):
        page = doc.load_page(page_idx)

        # 提升分辨率，提高 OCR 准确率
        pix = page.get_pixmap(matrix=fitz.Matrix(2.5, 2.5))
        img_bytes = pix.tobytes("ppm")
        image = Image.open(io.BytesIO(img_bytes))

        # OCR（支持中文）
        text = pytesseract.image_to_string(image, lang="chi_sim+eng")

        full_text += f"\n--- Page {page_idx + 1} ---\n{text}"

    doc.close()
    return full_text


async def ocr_pdf_to_txt(pdf_path, output_dir):
    """OCR 单个 PDF 并保存为 txt 文件"""
    # OCR 可能耗时，将其放入线程池
    text = await asyncio.to_thread(ocr_extract_pdf, pdf_path)

    # 输出路径
    base_name = os.path.basename(pdf_path)
    file_stem = os.path.splitext(base_name)[0]
    output_txt_path = os.path.join(output_dir, f"{file_stem}.txt")

    # 保存 TXT
    with open(output_txt_path, "w", encoding="utf-8") as f:
        f.write(text)

    print(f"saved as：{output_txt_path}\n")
    return output_txt_path


async def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    pdf_files = find_pdf_files_recursive(OCR_TXT_DIR)

    if not pdf_files:
        print("no pdf")
        return

    print(f"found {len(pdf_files)} PDFs\n")

    # 逐个 OCR 处理
    for pdf in pdf_files:
        try:
            await ocr_pdf_to_txt(pdf, OUTPUT_DIR)
        except Exception as e:
            print(f"failed：{pdf}  error:{e}")


if __name__ == "__main__":
    asyncio.run(main())
