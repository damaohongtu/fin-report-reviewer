from src.ingestion.markdown_chunker import MarkdownChunker


def test_markdown_chunker_preserves_tables_and_headings():
    markdown = """# 第一节 重要提示

段落一内容，描述公司治理情况。

<table>
<tr><td>项目</td><td>金额</td></tr>
<tr><td>营业收入</td><td>100</td></tr>
</table>

继续描述，保持上下文。
"""
    chunker = MarkdownChunker(max_chunk_chars=200)
    chunks = chunker.chunk_text(markdown, file_path="dummy.md")

    assert chunks, "应该至少生成一个 chunk"
    assert chunks[0]["chunk_text"].startswith("# 第一节 重要提示")

    table_chunks = [c for c in chunks if "<table>" in c["chunk_text"]]
    assert table_chunks, "表格 chunk 应当存在且未被破坏"
    assert "</table>" in table_chunks[0]["chunk_text"]


def test_markdown_chunker_split_long_paragraph_by_sentence():
    long_paragraph = (
        "# 第二节 管理层讨论\n\n"
        "这是第一句。" + "这是一句比较长的测试语句。" * 20 + "这是结尾。"
    )
    chunker = MarkdownChunker(max_chunk_chars=150)
    chunks = chunker.chunk_text(long_paragraph, file_path="dummy.md")

    assert len(chunks) >= 2, "长段落应被按句子切分为多个 chunk"
    for chunk in chunks:
        assert chunk["chunk_text"].startswith("# 第二节 管理层讨论")
        # 检查 chunk 内文本长度满足限制
        assert len(chunk["chunk_text"]) <= 200


