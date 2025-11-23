from src.ingestion.report_ingestion_service import ingestion_service

# 单个PDF摄入
# result_pdf = ingestion_service.ingest_pdf(
#     pdf_path="E:/workspace/fin-report-reviewer/data/pdfs/海康威视-2025半年报.pdf",
#     company_name="海康威视",
#     company_code="002415.SZ",
#     report_period="2025-06-30"
# )

# 单个markdown摄入
# result_markdown = ingestion_service.ingest_markdown(
#     markdown_path="E:/workspace/fin-report-reviewer/data/markdowns/MinerU_360-2025半年报.md",
#     company_name="海康威视",
#     company_code="002415.SZ",
#     report_period="20250630"
# )

result_markdown = ingestion_service.ingest_markdown(
    markdown_path="E:/workspace/fin-report-reviewer/data/markdowns/MinerU_360-2025半年报__20251115024319.md",
    company_name="三六零",
    company_code="601360",
    report_period="20250630"
)


print(result_markdown)
