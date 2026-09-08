# -*- coding: utf-8 -*-
"""공모전 라이브 데모용 샘플 설계문서 생성 — △△ 폐수처리시설 이송펌프 패키지.

의도적으로 주입한 문서 간 불일치 (전부 현업에서 실제로 발생하는 유형):
  1. P-101 정격출력  : 사양서 15 kW / 부하계산서 15 kW / 전기도면 18.5 kW   → 도면 오기재
  2. P-101 정격전압  : 사양서·계산서·목록 380 V / 전기도면 440 V           → 도면 오기재
  3. P-101 케이블규격 : 계산서·도면 25 mm² / 설비목록 35 mm²                → 설비목록 미갱신
  4. M-101 모델명    : 사양서 SM-132M / 설비목록 SM-132S                    → 한 글자 차이(프레임 상이)
  5. P-102 양정      : 사양서에만 기재, 계산서·도면·목록 없음               → 예비설비 사양 누락

표기·언어도 문서마다 다름: 정격출력 / RATED OUTPUT / Power(kW) / 정격출력(kW)
"""

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

OUT = Path(r"d:\download\VS 파일\공모전 !!!\데모_샘플문서")
FONT = "HYSMyeongJo-Medium"
pdfmetrics.registerFont(UnicodeCIDFont(FONT))


def spec_pdf() -> None:
    styles = getSampleStyleSheet()
    title = ParagraphStyle("t", parent=styles["Title"], fontName=FONT, fontSize=15)
    h = ParagraphStyle("h", parent=styles["Heading3"], fontName=FONT, spaceBefore=10)
    small = ParagraphStyle("s", parent=styles["BodyText"], fontName=FONT, fontSize=8,
                           textColor=colors.grey, leading=12)

    doc = SimpleDocTemplate(str(OUT / "01_기계장비_사양서.pdf"), pagesize=A4,
                            topMargin=20 * mm, bottomMargin=18 * mm,
                            leftMargin=20 * mm, rightMargin=20 * mm)

    def spec_table(rows):
        t = Table([["항목", "값", "비고"]] + rows, colWidths=[42 * mm, 42 * mm, 66 * mm], hAlign="LEFT")
        t.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, -1), FONT),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eef1f5")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#c9ced6")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        return t

    story = [
        Paragraph("기계장비 사양서 (Mechanical Equipment Specification)", title),
        Spacer(1, 4),
        Paragraph("프로젝트 : △△ 폐수처리시설 개선사업 &nbsp; | &nbsp; 문서번호 : ME-SPEC-014 &nbsp; | &nbsp; Rev. B", small),
        Paragraph("작성 : 기계설계팀 &nbsp; | &nbsp; 검토 : 이OO &nbsp; | &nbsp; 발행일 : 2026-07-11", small),
        Spacer(1, 10),
        Paragraph("1. 이송펌프 P-101 (운전)", h),
        spec_table([
            ["설비 유형", "원심펌프", "End-suction"],
            ["제조사", "대한펌프", "-"],
            ["모델명", "DHP-125", "-"],
            ["정격출력", "15 kW", "전동기 정격"],
            ["정격전압", "380 V", "3상 60Hz"],
            ["회전수", "1,760 rpm", "-"],
            ["유량", "120 m³/h", "설계점"],
            ["양정", "45 m", "설계점"],
        ]),
        Spacer(1, 8),
        Paragraph("2. 이송펌프 P-102 (예비)", h),
        spec_table([
            ["설비 유형", "원심펌프", "P-101 과 동일 형식"],
            ["제조사", "대한펌프", "-"],
            ["모델명", "DHP-125", "-"],
            ["정격출력", "15 kW", "-"],
            ["정격전압", "380 V", "-"],
            ["유량", "120 m³/h", "-"],
            # '양정' 행 없음 — 의도적 누락
        ]),
        Spacer(1, 8),
        Paragraph("3. 교반기 전동기 M-101", h),
        spec_table([
            ["설비 유형", "3상 유도전동기", "약품 혼화조 교반기"],
            ["제조사", "성진모터", "-"],
            ["모델명", "SM-132M", "프레임 132M"],
            ["정격출력", "7.5 kW", "-"],
            ["정격전압", "380 V", "-"],
            ["회전수", "1,750 rpm", "-"],
            ["효율", "89.1 %", "IE3"],
        ]),
        Spacer(1, 12),
        Paragraph("※ 본 사양서의 값은 기계설계 기준이며, 케이블·차단기 규격은 전기팀 부하계산서(EL-CALC-007)에 따른다.", small),
    ]
    doc.build(story)


def load_calc_csv() -> None:
    text = (
        "△△ 폐수처리시설 개선사업 - 전동기 부하 계산서 (Motor Load Schedule) / EL-CALC-007 Rev.A\n"
        "Tag,Description,Power(kW),Voltage(V),Efficiency(%),PowerFactor,FLC(A),Cable(mm2),Breaker(A)\n"
        "P-101,Transfer Pump (Duty),15,380,89.5,0.86,29.1,25,40\n"
        "P-102,Transfer Pump (Standby),15,380,89.5,0.86,29.1,25,40\n"
        "M-101,Agitator Motor,7.5,380,89.1,0.83,15.2,6,25\n"
    )
    (OUT / "02_전기_부하계산서.csv").write_text(text, encoding="utf-8-sig")


def sld_notes_txt() -> None:
    text = """ELECTRICAL SINGLE LINE DIAGRAM - FEEDER NOTES (title block & schedule extract)
Project: WWTP Improvement   Drawing: E-201   Rev: C   Date: 2026-08-19

TAG          : P-101
SERVICE      : TRANSFER PUMP (DUTY)
RATED OUTPUT : 18.5 kW
VOLTAGE      : 440 V , 3PH , 60Hz
CABLE        : 4C x 25 SQMM , XLPE
BREAKER      : 40 A

TAG          : P-102
SERVICE      : TRANSFER PUMP (STANDBY)
RATED OUTPUT : 15 kW
VOLTAGE      : 380 V , 3PH , 60Hz
CABLE        : 4C x 25 SQMM
BREAKER      : 40 A

TAG          : M-101
SERVICE      : AGITATOR MOTOR
RATED OUTPUT : 7.5 kW
VOLTAGE      : 380 V
CABLE        : 4C x 6 SQMM
BREAKER      : 25 A

NOTE: Final cable sizing to be confirmed against load calculation EL-CALC-007.
"""
    (OUT / "03_전기_단선결선도_주석.txt").write_text(text, encoding="utf-8")


def equipment_list_csv() -> None:
    text = (
        "△△ 폐수처리시설 개선사업 - 설비 목록 (Equipment List) / DOC-EL-001 Rev.D\n"
        "TAG,설비명,설비유형,제조사,모델명,정격출력(kW),전압(V),유량(m3/h),케이블(mm2),비고\n"
        "P-101,이송펌프,원심펌프,대한펌프,DHP-125,15,380,120,35,운전\n"
        "P-102,이송펌프,원심펌프,대한펌프,DHP-125,15,380,120,25,예비\n"
        "M-101,교반기 전동기,유도전동기,성진모터,SM-132S,7.5,380,,6,약품 혼화조\n"
    )
    (OUT / "04_설비_목록.csv").write_text(text, encoding="utf-8-sig")


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    spec_pdf()
    load_calc_csv()
    sld_notes_txt()
    equipment_list_csv()
    print("생성 완료:")
    for p in sorted(OUT.iterdir()):
        print(f"  {p.name}  ({p.stat().st_size:,} bytes)")
