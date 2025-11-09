from src.ingestion.report_ingestion_service import ingestion_service

# 单个PDF摄入
result = ingestion_service.ingest_pdf(
    pdf_path="E:/workspace/fin-report-reviewer/data/pdfs/海康威视-2025半年报.pdf",
    company_name="海康威视",
    company_code="002415.SZ",
    report_period="2025-06-30"
)