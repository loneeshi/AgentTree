import asyncio
from agentscope.rag import PDFReader, Document
import json
import os

#相对路径
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW_PDF_DIR = os.path.join(BASE_DIR, "data", "raw_pdf")
OUTPUT_DIR = os.path.join(BASE_DIR, "data", "final_output_txt")


def find_pdf_files_recursive(folder_path):
    #递归查找文件夹中的所有PDF文件[3](@ref)
    pdf_files = []
    
    # 使用os.walk递归遍历目录[7](@ref)
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.lower().endswith('.pdf'):
                full_path = os.path.join(root, file)
                pdf_files.append(full_path)
    
    return pdf_files

async def example_pdf_reader(pdf_path: str, output_dir: str, print_docs: bool = True):
    reader = PDFReader(chunk_size=800, split_by="paragraph")

    # 读取 PDF
    documents = await reader(pdf_path)

    """
    if print_docs:
        print(f"{os.path.basename(pdf_path)} 被分块为 {len(documents)} 个 Document 对象：")
        for idx, doc in enumerate(documents):
            text_content = doc.metadata["content"]["text"]
            preview = text_content[:100] + "..." if len(text_content) > 100 else text_content

            print(f"Document {idx}:")
            print("\tScore:", doc.score)
            print("\tContent preview:", preview)
            print("\tMetadata:", json.dumps(doc.metadata, indent=2, ensure_ascii=False), "\n")
    """            

    # 输出 txt 文件
    # txt 文件名 = pdf 同名
    base_name = os.path.basename(pdf_path)
    file_stem = os.path.splitext(base_name)[0]
    output_txt_path = os.path.join(output_dir, f"{file_stem}.txt")

    with open(output_txt_path, "w", encoding="utf-8") as f:
        for i, doc in enumerate(documents):
            f.write(f"--- Document Chunk {i} ---\n")
            f.write(doc.metadata["content"]["text"] + "\n\n")

    print(f"saved as ：{output_txt_path}\n")

    return documents


async def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    pdf_files = find_pdf_files_recursive(RAW_PDF_DIR)

    if not pdf_files:
        print("no pdf")
        return

    print(f"{len(pdf_files)} pdfs found\n")

    # 逐个解析 PDF
    for pdf in pdf_files:
        print(f"processing：{pdf}")
        await example_pdf_reader(pdf, OUTPUT_DIR, print_docs=True)


if __name__ == "__main__":
    asyncio.run(main())

