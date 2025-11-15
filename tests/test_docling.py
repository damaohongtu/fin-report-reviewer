from docling_core.transforms.chunker import HierarchicalChunker

from docling.document_converter import DocumentConverter

converter = DocumentConverter()
chunker = HierarchicalChunker()

# Convert the input file to Docling Document
source = "E:/workspace/fin-report-reviewer/data/markdowns/MinerU_海康威视-2025半年报__20251115014014.md"
doc = converter.convert(source).document

# Perform hierarchical chunking
texts = [chunk.text for chunk in chunker.chunk(doc)]

print(len(texts))
for text in texts:
    print(len(text))
    print(text)
    print("-"*50)