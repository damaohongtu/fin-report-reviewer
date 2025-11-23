import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from src.ingestion.markdown_chunker import MarkdownChunker, save_chunks_to_file  # noqa: E402


def parse_args():
    parser = argparse.ArgumentParser(description="Markdown 财报分块工具")
    parser.add_argument("--input", required=True, help="待分块的 Markdown 文件路径")
    parser.add_argument("--output", required=True, help="分块结果输出 JSON 路径")
    parser.add_argument("--max-chunk", type=int, default=600, help="单个 chunk 最大字符数")
    parser.add_argument("--min-chunk", type=int, default=200, help="单个 chunk 最小字符数（用于调优）")
    return parser.parse_args()


def main():
    args = parse_args()
    markdown_path = Path(args.input)
    if not markdown_path.exists():
        raise FileNotFoundError(f"未找到 Markdown 文件: {markdown_path}")

    chunker = MarkdownChunker(max_chunk_chars=args.max_chunk, min_chunk_chars=args.min_chunk)
    chunks = chunker.chunk_file(str(markdown_path))
    save_chunks_to_file(chunks, args.output)

    print(json.dumps({"chunks": len(chunks), "output": args.output}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()


