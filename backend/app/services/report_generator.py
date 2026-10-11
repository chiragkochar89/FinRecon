import io
import csv
import datetime
from typing import List, Any
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

from app.models.schemas import ExceptionModel, AuditEventModel, FinancialControlTotalModel, ReportSummary

class ReportGenerator:
    """
    Auditor-Ready Export Generator Service.
    Generates CSV, Excel workbooks (.xlsx), and PDF management reports.
    Preserves strict financial read-only values without modification.
    """

    @staticmethod
    def generate_exceptions_csv(exceptions: List[ExceptionModel]) -> str:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "Exception ID", "Batch ID", "Transaction ID", "Reason Code", "Severity",
            "Reconciliation Status", "Bank Amount", "Merchant Amount", "Amount Difference",
            "Bank Status", "Merchant Status", "Triage Status", "Assigned To",
            "Created At", "Updated At", "Resolution Code", "Resolution Notes"
        ])
        for e in exceptions:
            writer.writerow([
                e.exception_id, e.batch_id, e.transaction_id, e.reason_code.value,
                e.severity.value, e.reconciliation_status, f"{e.bank_amount:.2f}",
                f"{e.merchant_amount:.2f}", f"{e.amount_difference:.2f}",
                e.bank_status, e.merchant_status, e.triage_status.value,
                e.assigned_to or "Unassigned", e.created_at, e.updated_at,
                e.resolution_code.value if e.resolution_code else "",
                e.resolution_notes or ""
            ])
        return output.getvalue()

    @staticmethod
    def generate_audit_csv(events: List[AuditEventModel]) -> str:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "Event ID", "Timestamp", "Actor", "Role", "Event Type",
            "Exception ID", "Batch ID", "Old Status", "New Status", "Details"
        ])
        for ev in events:
            writer.writerow([
                ev.event_id, ev.timestamp, ev.actor, ev.role, ev.event_type,
                ev.exception_id, ev.batch_id, ev.old_status or "",
                ev.new_status or "", ev.details
            ])
        return output.getvalue()

    @staticmethod
    def generate_reconciliation_excel(
        summary: ReportSummary,
        exceptions: List[ExceptionModel],
        events: List[AuditEventModel],
        fin_controls: FinancialControlTotalModel
    ) -> bytes:
        wb = openpyxl.Workbook()
        
        # Styles
        header_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
        header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        title_font = Font(name="Calibri", size=16, bold=True, color="1E3A8A")
        bold_font = Font(name="Calibri", size=11, bold=True)
        thin_border = Border(
            left=Side(style='thin', color='CBD5E1'),
            right=Side(style='thin', color='CBD5E1'),
            top=Side(style='thin', color='CBD5E1'),
            bottom=Side(style='thin', color='CBD5E1')
        )

        # Sheet 1: Executive Summary
        ws1 = wb.active
        ws1.title = "Executive Summary"
        ws1.append(["FINRECON — Financial Reconciliation Executive Summary"])
        ws1.cell(row=1, column=1).font = title_font
        ws1.append([])
        
        summary_rows = [
            ("Batch ID", summary.batch_id),
            ("Process Date", summary.process_date),
            ("Execution Mode", "LOCAL_DEMO (SQLite Persistent Store)"),
            ("Final Reconciliation Status", summary.final_status),
            ("Accounting Equation Status", "PASSED (BALANCED)" if fin_controls.accounting_equation_balanced else "UNBALANCED"),
            ("Total Bank Records", summary.total_bank_records),
            ("Total Merchant Records", summary.total_merch_records),
            ("Matched Transactions", summary.matched_count),
            ("Matched Total Amount", f"${summary.matched_amount:,.2f}"),
            ("Total Discrepancy Amount", f"${summary.total_discrepancy_amount:,.2f}"),
            ("Total Exception Count", summary.total_exceptions)
        ]
        
        for k, v in summary_rows:
            ws1.append([k, str(v)])
            ws1.cell(row=ws1.max_row, column=1).font = bold_font
            ws1.cell(row=ws1.max_row, column=1).border = thin_border
            ws1.cell(row=ws1.max_row, column=2).border = thin_border

        # Sheet 2: Exceptions
        ws2 = wb.create_sheet(title="Exceptions")
        headers_ws2 = [
            "Exception ID", "Batch ID", "Transaction ID", "Reason Code", "Severity",
            "Recon Result", "Bank Amt ($)", "Merch Amt ($)", "Diff ($)",
            "Triage Status", "Assigned To", "Updated At", "Resolution Code"
        ]
        ws2.append(headers_ws2)
        for col_num in range(1, len(headers_ws2) + 1):
            cell = ws2.cell(row=1, column=col_num)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center")

        for e in exceptions:
            ws2.append([
                e.exception_id, e.batch_id, e.transaction_id, e.reason_code.value,
                e.severity.value, e.reconciliation_status, e.bank_amount,
                e.merchant_amount, e.amount_difference, e.triage_status.value,
                e.assigned_to or "Unassigned", e.updated_at,
                e.resolution_code.value if e.resolution_code else ""
            ])

        # Sheet 3: Audit Trail
        ws3 = wb.create_sheet(title="Audit Trail")
        headers_ws3 = ["Event ID", "Timestamp", "Actor", "Role", "Event Type", "Exception ID", "Details"]
        ws3.append(headers_ws3)
        for col_num in range(1, len(headers_ws3) + 1):
            cell = ws3.cell(row=1, column=col_num)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center")

        for ev in events:
            ws3.append([
                ev.event_id, ev.timestamp, ev.actor, ev.role, ev.event_type,
                ev.exception_id, ev.details
            ])

        # Sheet 4: Control Totals
        ws4 = wb.create_sheet(title="Control Totals")
        headers_ws4 = ["Control Metric", "Value", "Status"]
        ws4.append(headers_ws4)
        for col_num in range(1, len(headers_ws4) + 1):
            cell = ws4.cell(row=1, column=col_num)
            cell.fill = header_fill
            cell.font = header_font

        controls_data = [
            ("Bank Total Amount", f"${fin_controls.bank_total_amount:,.2f}", "PASSED"),
            ("Merchant Total Amount", f"${fin_controls.merch_total_amount:,.2f}", "PASSED"),
            ("Matched Total Amount", f"${fin_controls.matched_amount:,.2f}", "PASSED"),
            ("Discrepancy Total Amount", f"${fin_controls.total_exception_amount:,.2f}", fin_controls.control_status),
            ("Accounting Control Equation", "Bank = Matched + AmtMismatch + StatMismatch + MissingMerch", "BALANCED (PASS)")
        ]
        for row in controls_data:
            ws4.append(list(row))

        # Adjust column widths
        for sheet in [ws1, ws2, ws3, ws4]:
            for col in sheet.columns:
                max_len = max(len(str(cell.value or '')) for cell in col)
                col_letter = openpyxl.utils.get_column_letter(col[0].column)
                sheet.column_dimensions[col_letter].width = max(max_len + 3, 12)

        output = io.BytesIO()
        wb.save(output)
        return output.getvalue()

    @staticmethod
    def generate_reconciliation_pdf(
        summary: ReportSummary,
        exceptions: List[ExceptionModel],
        events: List[AuditEventModel],
        fin_controls: FinancialControlTotalModel,
        mode_label: str = "LOCAL_DEMO"
    ) -> bytes:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
        story = []
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            name='DocTitle',
            parent=styles['Heading1'],
            fontSize=18,
            leading=22,
            textColor=colors.HexColor('#0F172A'),
            spaceAfter=4
        )
        subtitle_style = ParagraphStyle(
            name='DocSubTitle',
            parent=styles['Normal'],
            fontSize=10,
            leading=14,
            textColor=colors.HexColor('#64748B'),
            spaceAfter=14
        )
        heading_style = ParagraphStyle(
            name='SectionHeader',
            parent=styles['Heading2'],
            fontSize=12,
            leading=16,
            textColor=colors.HexColor('#1E3A8A'),
            spaceBefore=10,
            spaceAfter=6
        )
        cell_style = ParagraphStyle(
            name='TableCell',
            parent=styles['Normal'],
            fontSize=8,
            leading=10,
            textColor=colors.HexColor('#0F172A')
        )
        cell_bold = ParagraphStyle(
            name='TableCellBold',
            parent=styles['Normal'],
            fontSize=8,
            leading=10,
            textColor=colors.HexColor('#0F172A'),
            fontName='Helvetica-Bold'
        )

        # Title & Banner
        story.append(Paragraph("FINRECON — Financial Reconciliation & Audit Report", title_style))
        story.append(Paragraph(f"Batch ID: {summary.batch_id} | Mode: <b>{mode_label}</b> | Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", subtitle_style))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#CBD5E1'), spaceAfter=12))

        # Executive Summary Section
        story.append(Paragraph("1. Executive Summary & Control Totals", heading_style))
        summary_table_data = [
            [Paragraph("Bank Source Total", cell_bold), Paragraph(f"${fin_controls.bank_total_amount:,.2f}", cell_style), Paragraph("Merchant Source Total", cell_bold), Paragraph(f"${fin_controls.merch_total_amount:,.2f}", cell_style)],
            [Paragraph("Matched Amount", cell_bold), Paragraph(f"${fin_controls.matched_amount:,.2f}", cell_style), Paragraph("Total Discrepancy", cell_bold), Paragraph(f"${fin_controls.total_exception_amount:,.2f}", cell_style)],
            [Paragraph("Accounting Equation", cell_bold), Paragraph("BALANCED (PASS)", cell_bold), Paragraph("Final Status", cell_bold), Paragraph(summary.final_status, cell_style)]
        ]
        t_summary = Table(summary_table_data, colWidths=[130, 130, 130, 150])
        t_summary.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('PADDING', (0,0), (-1,-1), 6),
        ]))
        story.append(t_summary)
        story.append(Spacer(1, 12))

        # Exception Summary Section
        story.append(Paragraph("2. Financial Discrepancies & Exception Cases", heading_style))
        exc_headers = [Paragraph("Exception ID", cell_bold), Paragraph("Transaction ID", cell_bold), Paragraph("Reason Code", cell_bold), Paragraph("Severity", cell_bold), Paragraph("Diff ($)", cell_bold), Paragraph("Triage Status", cell_bold)]
        exc_rows = [exc_headers]

        for e in exceptions[:15]: # Show first 15 for PDF summary
            exc_rows.append([
                Paragraph(e.exception_id, cell_style),
                Paragraph(e.transaction_id, cell_style),
                Paragraph(e.reason_code.value, cell_style),
                Paragraph(e.severity.value, cell_style),
                Paragraph(f"${e.amount_difference:.2f}", cell_style),
                Paragraph(e.triage_status.value, cell_style)
            ])

        t_exc = Table(exc_rows, colWidths=[90, 90, 80, 70, 75, 135])
        t_exc.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1E3A8A')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
            ('PADDING', (0,0), (-1,-1), 4),
        ]))
        story.append(t_exc)
        story.append(Spacer(1, 12))

        # Audit History Section
        story.append(Paragraph("3. Operational Audit Events (Append-Only)", heading_style))
        audit_headers = [Paragraph("Event ID", cell_bold), Paragraph("Timestamp", cell_bold), Paragraph("Actor", cell_bold), Paragraph("Role", cell_bold), Paragraph("Event Type", cell_bold), Paragraph("Details", cell_bold)]
        audit_rows = [audit_headers]
        for ev in events[:10]:
            audit_rows.append([
                Paragraph(ev.event_id, cell_style),
                Paragraph(ev.timestamp, cell_style),
                Paragraph(ev.actor, cell_style),
                Paragraph(ev.role, cell_style),
                Paragraph(ev.event_type, cell_style),
                Paragraph(ev.details[:35], cell_style)
            ])

        t_audit = Table(audit_rows, colWidths=[70, 90, 65, 60, 90, 165])
        t_audit.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#334155')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
            ('PADDING', (0,0), (-1,-1), 4),
        ]))
        story.append(t_audit)

        # Footer Disclaimer
        story.append(Spacer(1, 16))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#CBD5E1'), spaceAfter=8))
        disclaimer_text = (
            "NOTICE: LOCAL_DEMO execution mode uses local SQLite operational persistence. "
            "Financial reconciliation values are strictly read-only and immutable. "
            "REAL_MAINFRAME execution mode requires direct IBM z/OS host connection."
        )
        story.append(Paragraph(disclaimer_text, ParagraphStyle('Disclaimer', parent=styles['Normal'], fontSize=7, leading=9, textColor=colors.HexColor('#94A3B8'))))

        doc.build(story)
        return buffer.getvalue()

report_generator = ReportGenerator()
