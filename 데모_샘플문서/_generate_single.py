# -*- coding: utf-8 -*-
"""단일 문서 테스트용 — 문서 1건만 업로드해도 이슈가 나오는 사양서.

여러 문서를 준비하지 않고도 파이프라인(파싱 → 추출 → 검증)을 확인하는 용도.
교차검증에는 보통 2개 이상 문서가 필요하지만, '한 설비 안에서 값들이 서로 맞는지'
(계산 검증)와 '필수 항목이 빠졌는지'(누락 검증)는 문서 1건으로도 잡아낸다.

심어둔 이슈:
  1. P-301 : 정격전류 32 A  vs  30kW/380V 3상 계산값 약 44 A   → 계산 불일치 (calc_mismatch, 중간)
  2. M-301 : 차단기 20 A  vs  정격전류 28 A (여유율 0.7배)      → 차단기 용량 부족 (calc_mismatch, 높음)
  3. M-301 : 효율(Efficiency) 미기재                            → 필수 항목 누락 (missing, 낮음)
  4. B-301 : 유량(Flow) 미기재                                  → 필수 항목 누락 (missing, 낮음)
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

styles = getSampleStyleSheet()
title = ParagraphStyle("t", parent=styles["Title"], fontName=FONT, fontSize=15)
h = ParagraphStyle("h", parent=styles["Heading3"], fontName=FONT, spaceBefore=10)
small = ParagraphStyle("s", parent=styles["BodyText"], fontName=FONT, fontSize=8,
                       textColor=colors.grey, leading=12)


def tbl(rows):
    t = Table([["항목", "값", "비고"]] + rows, colWidths=[40 * mm, 40 * mm, 70 * mm], hAlign="LEFT")
    t.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), FONT),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eef1f5")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#c9ced6")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t


doc = SimpleDocTemplate(str(OUT / "05_단일문서_테스트_사양서.pdf"), pagesize=A4,
                        topMargin=20 * mm, bottomMargin=18 * mm, leftMargin=20 * mm, rightMargin=20 * mm)

story = [
    Paragraph("설비 사양서 (단일 문서 테스트용)", title),
    Spacer(1, 4),
    Paragraph("프로젝트 : 테스트 프로젝트 &nbsp;|&nbsp; 문서번호 : TEST-SPEC-001 &nbsp;|&nbsp; Rev. 0", small),
    Spacer(1, 10),

    Paragraph("1. 냉각수 순환펌프 P-301", h),
    tbl([
        ["설비 유형", "원심펌프", "-"],
        ["제조사", "동방펌프", "-"],
        ["모델명", "DBP-160", "-"],
        ["정격출력", "30 kW", "-"],
        ["정격전압", "380 V", "3상 60Hz"],
        ["정격전류", "32 A", "명판 기준"],
        ["회전수", "1,760 rpm", "-"],
        ["유량", "150 m³/h", "설계점"],
        ["양정", "50 m", "설계점"],
    ]),
    Spacer(1, 8),

    Paragraph("2. 교반기 전동기 M-301", h),
    tbl([
        ["설비 유형", "3상 유도전동기", "-"],
        ["제조사", "성진모터", "-"],
        ["모델명", "SM-160L", "-"],
        ["정격출력", "15 kW", "-"],
        ["정격전압", "380 V", "-"],
        ["정격전류", "28 A", "-"],
        ["회전수", "1,750 rpm", "-"],
        ["차단기", "20 A", "MCCB"],
        # '효율(Efficiency)' 행 없음 — 의도적 누락 (전동기 필수 항목)
    ]),
    Spacer(1, 8),

    Paragraph("3. 가압 송풍기 B-301", h),
    tbl([
        ["설비 유형", "터보 송풍기", "-"],
        ["제조사", "한성블로워", "-"],
        ["모델명", "HB-40", "-"],
        ["정격출력", "7.5 kW", "-"],
        ["정격전압", "380 V", "-"],
        ["회전수", "3,540 rpm", "-"],
        ["정압", "3.5 kPa", "-"],
        # '유량(풍량, Flow)' 행 없음 — 의도적 누락 (송풍기 필수 항목)
    ]),
    Spacer(1, 12),
    Paragraph("※ 본 문서는 시스템 테스트용 가상 데이터입니다. 실제 설계 기준이 아닙니다.", small),
]

doc.build(story)
print("생성:", (OUT / "05_단일문서_테스트_사양서.pdf").name)
