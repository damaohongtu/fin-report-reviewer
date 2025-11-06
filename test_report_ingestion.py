from src.ingestion.report_ingestion_service import ingestion_service

# 单个PDF摄入
result = ingestion_service.ingest_pdf(
    pdf_path="E:/workspace/fin-report-reviewer/data/pdfs/360-2025一季度报.pdf",
    company_name="三六零",
    company_code="600601.SH",
    report_period="2025-03-31"
)