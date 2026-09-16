# -*- coding: utf-8 -*-
"""추가 테스트 문서 생성기: 공정 데이터시트, 계장 데이터시트, 변경이력."""
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

OUT = Path(__file__).resolve().parent
FONT = "HYSMyeongJo-Medium"
pdfmetrics.registerFont(UnicodeCIDFont(FONT))


def make_process_csv():
    text = (
        "△△ 폐수처리시설 개선사업 - 공정 설계 데이터 / PR-CALC-003 Rev.B\n"
        "TAG,Service,Flow(m3/h),Head(m),DesignTemp(C),Source\n"
        "P-101,Transfer Pump Duty,125,45,35,Process Design Basis\n"
        "P-102,Transfer Pump Standby,120,45,35,Process Design Basis\n"
        "M-101,Agitator Motor,,,35,Mechanical Specification\n"
    )
    (OUT / "06_공정_설계데이터.csv").write_text(text, encoding="utf-8-sig")


def make_instrument_pdf():
    styles = getSampleStyleSheet()
    title = ParagraphStyle("title", parent=styles["Title"], fontName=FONT, fontSize=15)
    head = ParagraphStyle("head", parent=styles["Heading3"], fontName=FONT, spaceBefore=10)
    small = ParagraphStyle("small", parent=styles["BodyText"], fontName=FONT, fontSize=8, textColor=colors.grey)
    doc = SimpleDocTemplate(str(OUT / "07_계장_모터데이터시트.pdf"), pagesize=A4,
                            topMargin=18 * mm, bottomMargin=18 * mm, leftMargin=20 * mm, rightMargin=20 * mm)

    def table(rows):
        t = Table([["항목", "값", "출처/비고"]] + rows, colWidths=[45 * mm, 45 * mm, 60 * mm])
        t.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, -1), FONT), ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eef1f5")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#c9ced6")),
            ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        return t

    story = [
        Paragraph("계장·전기 인터페이스 데이터시트", title),
        Paragraph("프로젝트: △△ 폐수처리시설 개선사업 | 문서번호: IE-DS-021 | Rev. A", small),
        Paragraph("전기·계장팀 발행 / Demo Data 기반 테스트 문서", small), Spacer(1, 10),
        Paragraph("1. P-101 이송펌프 인터페이스", head),
        table([
            ["설비 TAG", "P-101", "운전 펌프"],
            ["모터 정격출력", "15 kW", "Motor data"],
            ["정격전류", "29.1 A", "부하계산서 기준"],
            ["케이블", "4C x 25 SQMM", "XLPE"],
            ["차단기", "40 A", "MCC-01 feeder"],
        ]), Spacer(1, 8),
        Paragraph("2. M-101 교반기 인터페이스", head),
        table([
            ["설비 TAG", "M-101", "약품 혼화조"],
            ["모터 정격출력", "7.5 kW", "Motor data"],
            ["정격전류", "15.2 A", "부하계산서 기준"],
            ["케이블", "4C x 6 SQMM", "XLPE"],
            ["차단기", "25 A", "MCC-02 feeder"],
        ]), Spacer(1, 12),
        Paragraph("※ 본 문서는 실제 승인 설계가 아닌 CrossCheck 테스트용 예시입니다. 최종 선정은 담당 엔지니어가 확인해야 합니다.", small),
    ]
    doc.build(story)


def make_revision_txt():
    text = """문서 변경이력 및 검토 메모 - REVISION NOTE RN-006
Project: WWTP Improvement / Date: 2026-08-21

[P-101]
- 공정 설계 기준 유량이 120 m3/h에서 125 m3/h로 변경됨.
- 기계 사양서와 전기 부하계산서의 정격출력 15 kW는 유지.
- 전기 도면의 RATED OUTPUT 18.5 kW 표기는 변경 검토 필요.

[M-101]
- 모델명은 SM-132M을 기준으로 검토.
- 설비 목록의 SM-132S 표기는 공급사 회신 후 확정 예정.

[검토 상태]
- 본 문서는 변경 영향 추적 테스트용 참고 문서이며 승인 문서가 아님.
"""
    (OUT / "08_설계_변경이력_검토메모.txt").write_text(text, encoding="utf-8")


if __name__ == "__main__":
    make_process_csv()
    make_instrument_pdf()
    make_revision_txt()
    print("추가 테스트 문서 생성 완료")
