#AI_on_Rail

pdf转换documents:
1. 对于大多数pdf，直接调用AgentScope PDFRead,得到结果txt
2. 对于扫描文件，或受水印影响的pdf，直接阅读效果较差。先用ocr读出txt文档。再讲txt文档转化为第一类pdf，再次调用PDFRead功能。
得到chunk_size=800的documents对象。 （chunk_size=800优先考虑词句连贯，较适用于中高级问题。对于初级“大海捞针”式问题，适当减小chunk_size的值，可能效果更佳）
