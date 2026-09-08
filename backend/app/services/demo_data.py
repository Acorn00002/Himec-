"""Builds the curated demo dataset (section 14/15 of the product spec).

Values are hand-crafted so the demo is 100% reliable during a live presentation:
mismatches are deliberately injected and the resulting Issues (severity + impact +
reasoning) are seeded directly rather than derived by a generic inference engine.
The per-parameter ✓ / ⚠ status shown in the CrossCheck table, however, IS computed
live by services.crosscheck_basic from these same raw values, so the table and the
seeded issues stay consistent with each other.
"""

from __future__ import annotations

import datetime as dt
from collections import defaultdict

from sqlalchemy.orm import Session

from app.db import models

DOCS = [
    ("Motor_Spec.pdf", "pdf", "spec"),
    ("Electrical_Drawing.pdf", "pdf", "drawing"),
    ("Load_Calculation.xlsx", "xlsx", "calculation"),
    ("Equipment_List.xlsx", "xlsx", "equipment_list"),
    ("P&ID.pdf", "pdf", "pid"),
]


def _num(value: str) -> float | None:
    try:
        return float(value)
    except ValueError:
        return None


def seed_demo_project(db: Session) -> models.Project:
    project = models.Project(name="Demo Project — Motor & Pump Package", is_demo=True)
    db.add(project)
    db.flush()

    doc = {}
    for filename, doc_type, category in DOCS:
        d = models.Document(
            project_id=project.id,
            filename=filename,
            doc_type=doc_type,
            category=category,
            status="analyzed",
            uploaded_at=dt.datetime.utcnow(),
        )
        db.add(d)
        db.flush()
        doc[filename] = d

    equipment = {}
    for tag, etype in [
        ("M-101", "Motor"),
        ("M-102", "Motor"),
        ("P-101", "Pump"),
        ("P-102", "Pump"),
        ("AHU-101", "AHU"),
    ]:
        e = models.Equipment(project_id=project.id, tag=tag, equipment_type=etype)
        db.add(e)
        db.flush()
        equipment[tag] = e

    created_params: list[tuple[str, models.ParameterValue]] = []

    def add(tag, filename, name, value, unit=None, location=None, snippet=None):
        pv = models.ParameterValue(
            equipment_id=equipment[tag].id,
            document_id=doc[filename].id,
            name=name,
            value=str(value),
            numeric_value=_num(str(value)),
            unit=unit,
            location=location,
            raw_snippet=snippet or f"{name}: {value}{(' ' + unit) if unit else ''}",
        )
        db.add(pv)
        created_params.append((tag, pv))

    # ---- M-101 : 정격출력 불일치 (제품 브리프의 대표 예시) ----
    add("M-101", "Motor_Spec.pdf", "Manufacturer", "Siemens", location="p.12")
    add("M-101", "Motor_Spec.pdf", "Model", "1LE1001", location="p.12")
    add("M-101", "Motor_Spec.pdf", "Power", 15, "kW", "p.12")
    add("M-101", "Motor_Spec.pdf", "Voltage", 380, "V", "p.12")
    add("M-101", "Motor_Spec.pdf", "RPM", 1750, None, "p.12")
    add("M-101", "Motor_Spec.pdf", "Efficiency", 92, "%", "p.12")
    add("M-101", "Motor_Spec.pdf", "Power Factor", 0.89, None, "p.12")

    add("M-101", "Electrical_Drawing.pdf", "Power", 15, "kW", "Dwg E-101")
    add("M-101", "Electrical_Drawing.pdf", "Voltage", 380, "V", "Dwg E-101")
    add("M-101", "Electrical_Drawing.pdf", "Cable Size", 6, "mm2", "Dwg E-101")
    add("M-101", "Electrical_Drawing.pdf", "Breaker Size", 40, "A", "Dwg E-101")

    add("M-101", "Load_Calculation.xlsx", "Power", 18.5, "kW", "Sheet1!B4")
    add("M-101", "Load_Calculation.xlsx", "Current", 35.1, "A", "Sheet1!B5")

    add("M-101", "Equipment_List.xlsx", "Manufacturer", "Siemens", location="Row 3")
    add("M-101", "Equipment_List.xlsx", "Model", "1LE1001", location="Row 3")
    add("M-101", "Equipment_List.xlsx", "Power", 15, "kW", "Row 3")

    # ---- M-102 : Power mismatch (도면만 다른 값 — 사양서·목록은 일치) ----
    add("M-102", "Motor_Spec.pdf", "Manufacturer", "ABB", location="p.14")
    add("M-102", "Motor_Spec.pdf", "Model", "M3BP112", location="p.14")
    add("M-102", "Motor_Spec.pdf", "Power", 11, "kW", "p.14")
    add("M-102", "Motor_Spec.pdf", "Voltage", 380, "V", "p.14")
    add("M-102", "Motor_Spec.pdf", "RPM", 1450, None, "p.14")
    add("M-102", "Motor_Spec.pdf", "Efficiency", 91, "%", "p.14")

    add("M-102", "Electrical_Drawing.pdf", "Power", 15, "kW", "Dwg E-102")
    add("M-102", "Electrical_Drawing.pdf", "Voltage", 380, "V", "Dwg E-102")
    add("M-102", "Electrical_Drawing.pdf", "Cable Size", 4, "mm2", "Dwg E-102")
    add("M-102", "Electrical_Drawing.pdf", "Breaker Size", 32, "A", "Dwg E-102")

    add("M-102", "Equipment_List.xlsx", "Manufacturer", "ABB", location="Row 4")
    add("M-102", "Equipment_List.xlsx", "Model", "M3BP112", location="Row 4")
    add("M-102", "Equipment_List.xlsx", "Power", 11, "kW", "Row 4")

    # ---- P-101 : 케이블 규격 / 차단기 용량이 도면과 설비목록에서 상이 ----
    add("P-101", "Equipment_List.xlsx", "Manufacturer", "Grundfos", location="Row 7")
    add("P-101", "Equipment_List.xlsx", "Model", "CR32-4", location="Row 7")
    add("P-101", "Equipment_List.xlsx", "Flow", 120, "m3/h", "Row 7")
    add("P-101", "Equipment_List.xlsx", "Pressure", 4.2, "bar", "Row 7")
    add("P-101", "Equipment_List.xlsx", "Cable Size", 25, "mm2", "Row 7")
    add("P-101", "Equipment_List.xlsx", "Breaker Size", 50, "A", "Row 7")

    add("P-101", "P&ID.pdf", "Manufacturer", "Grundfos", location="Dwg P-201")
    add("P-101", "P&ID.pdf", "Model", "CR32-4", location="Dwg P-201")
    add("P-101", "P&ID.pdf", "Flow", 125, "m3/h", "Dwg P-201")

    add("P-101", "Electrical_Drawing.pdf", "Cable Size", 35, "mm2", "Dwg E-201")
    add("P-101", "Electrical_Drawing.pdf", "Breaker Size", 63, "A", "Dwg E-201")

    add("P-101", "Load_Calculation.xlsx", "Power", 7.5, "kW", "Sheet2!B4")

    # ---- P-102 : 모델명 불일치 + Efficiency 누락 ----
    add("P-102", "Equipment_List.xlsx", "Manufacturer", "Grundfos", location="Row 8")
    add("P-102", "Equipment_List.xlsx", "Model", "CR32-4", location="Row 8")
    add("P-102", "Equipment_List.xlsx", "Flow", 60, "m3/h", "Row 8")
    add("P-102", "Equipment_List.xlsx", "Pressure", 4.2, "bar", "Row 8")
    add("P-102", "Equipment_List.xlsx", "Power", 7.5, "kW", "Row 8")

    add("P-102", "P&ID.pdf", "Manufacturer", "Grundfos", location="Dwg P-202")
    add("P-102", "P&ID.pdf", "Model", "CR64-4", location="Dwg P-202")
    add("P-102", "P&ID.pdf", "Flow", 60, "m3/h", "Dwg P-202")

    add("P-102", "Motor_Spec.pdf", "Power", 7.5, "kW", "p.19")
    add("P-102", "Motor_Spec.pdf", "Voltage", 380, "V", "p.19")
    add("P-102", "Motor_Spec.pdf", "RPM", 2900, None, "p.19")
    # Note: no Efficiency row for P-102 — deliberately missing vs M-101/M-102

    # ---- AHU-101 : 정격출력이 도면에서만 상이 ----
    add("AHU-101", "Equipment_List.xlsx", "Manufacturer", "Daikin", location="Row 12")
    add("AHU-101", "Equipment_List.xlsx", "Model", "AHU-V50", location="Row 12")
    add("AHU-101", "Equipment_List.xlsx", "Power", 15, "kW", "Row 12")
    add("AHU-101", "Equipment_List.xlsx", "Flow", 8500, "m3/h", "Row 12")
    add("AHU-101", "Equipment_List.xlsx", "Weight", 450, "kg", "Row 12")

    add("AHU-101", "Motor_Spec.pdf", "Power", 15, "kW", "p.27")
    add("AHU-101", "Motor_Spec.pdf", "Voltage", 380, "V", "p.27")

    add("AHU-101", "Electrical_Drawing.pdf", "Power", 18.5, "kW", "Dwg E-115")
    add("AHU-101", "Electrical_Drawing.pdf", "Voltage", 380, "V", "Dwg E-115")

    db.flush()

    # ---- Synthesize ExtractedChunk rows from the raw_snippets above, so "view original
    # text" works for the demo project exactly like it does for a real upload (Phase 8
    # normally produces these chunks by parsing the file; here there is no real file,
    # so we build the equivalent chunk text directly from the same snippets). ----
    doc_type_by_id = {doc[filename].id: doc_type for filename, doc_type, _category in DOCS}
    groups: dict[tuple[int, str], list[tuple[str, models.ParameterValue]]] = defaultdict(list)
    for tag, pv in created_params:
        if pv.location:
            groups[(pv.document_id, pv.location)].append((tag, pv))

    for order_index, ((document_id, location), items) in enumerate(groups.items()):
        tags = sorted({t for t, _ in items})
        lines = [f"TAG: {', '.join(tags)}"] + [pv.raw_snippet for _, pv in items]
        content_type = "table" if doc_type_by_id.get(document_id) == "xlsx" else "text"
        db.add(models.ExtractedChunk(
            document_id=document_id,
            location=location,
            content_type=content_type,
            text="\n".join(lines),
            order_index=order_index,
        ))
    db.flush()

    # raw_snippet lookup so demo evidence rows carry the same "원문 스니펫" a real upload
    # would — keyed the way the hand-authored evidence below identifies a data point.
    snippet_by: dict[tuple[int, str | None, str], str | None] = {
        (pv.document_id, pv.location, str(pv.value)): pv.raw_snippet for _tag, pv in created_params
    }

    # ---- Curated Issues (severity / impact / reasoning) ----
    _DISPOSITION_TO_STATUS = {
        "open": "open", "intentional": "reviewed", "action_required": "reviewed", "resolved": "resolved",
    }

    def add_issue(tag, parameter_name, issue_type, severity, title, description, reasoning,
                  evidence, impact_items, status=None,
                  disposition="open", review_comment=None, reviewed_by=None):
        status = status or _DISPOSITION_TO_STATUS[disposition]
        # inject document_id so the frontend can look up original source text, same as
        # for real (non-demo) projects — evidence is authored with just filenames above.
        evidence_with_ids = []
        for e in evidence:
            document_id = doc[e["document"]].id
            evidence_with_ids.append({
                **e,
                "document_id": document_id,
                "raw_snippet": e.get("raw_snippet")
                or snippet_by.get((document_id, e.get("location"), str(e.get("value")))),
            })
        reviewed_at = (
            dt.datetime.utcnow() if (disposition != "open" or review_comment) else None
        )
        db.add(models.Issue(
            project_id=project.id,
            equipment_id=equipment[tag].id if tag else None,
            parameter_name=parameter_name,
            issue_type=issue_type,
            severity=severity,
            title=title,
            description=description,
            reasoning=reasoning,
            evidence=evidence_with_ids,
            impact_items=impact_items,
            status=status,
            disposition=disposition,
            review_comment=review_comment,
            reviewed_by=reviewed_by,
            reviewed_at=reviewed_at,
        ))

    add_issue(
        "M-101", "Power", "value_mismatch", "HIGH",
        "정격출력이 문서마다 다르게 기재되어 있습니다",
        "M-101의 정격출력이 장비 사양서에는 15 kW, 부하 목록에는 18.5 kW, 전기 도면에는 15 kW로 "
        "기재되어 있습니다. 사양서·도면과 부하 목록의 값이 서로 다릅니다.",
        "정격출력은 전동기의 전류를 계산하는 출발점입니다. 15 kW와 18.5 kW는 전류로 환산하면 약 20% 차이가 "
        "나며, 이 값에 따라 케이블 굵기와 차단기 용량이 달라질 수 있습니다. 어느 값이 맞는지는 담당 "
        "엔지니어의 확인이 필요합니다.",
        evidence=[
            {"document": "Motor_Spec.pdf", "location": "p.12", "value": "15", "unit": "kW"},
            {"document": "Electrical_Drawing.pdf", "location": "Dwg E-101", "value": "15", "unit": "kW"},
            {"document": "Load_Calculation.xlsx", "location": "Sheet1!B4", "value": "18.5", "unit": "kW"},
        ],
        impact_items=["전동기 정격전류(A) 재계산", "케이블 굵기 산정", "차단기 용량 선정", "배전반 부하 집계"],
    )

    add_issue(
        "M-102", "Power", "value_mismatch", "HIGH",
        "정격출력이 전기 도면에서만 다르게 기재되어 있습니다",
        "M-102의 정격출력이 장비 사양서와 설비 목록에는 11 kW로 일치하지만, 전기 도면에는 15 kW로 "
        "기재되어 있습니다. 도면만 값이 다릅니다.",
        "두 문서가 11 kW로 일치하고 도면 한 곳만 15 kW이므로 도면의 오기재 가능성이 있습니다. 다만 "
        "도면 값을 기준으로 케이블·차단기가 이미 선정되었다면 실제 부하보다 과다 산정되었을 수 있어 "
        "확인이 필요합니다.",
        evidence=[
            {"document": "Motor_Spec.pdf", "location": "p.14", "value": "11", "unit": "kW"},
            {"document": "Equipment_List.xlsx", "location": "Row 4", "value": "11", "unit": "kW"},
            {"document": "Electrical_Drawing.pdf", "location": "Dwg E-102", "value": "15", "unit": "kW"},
        ],
        impact_items=["전동기 정격전류(A) 재계산", "케이블 굵기 산정", "차단기 용량 선정"],
    )

    add_issue(
        "P-101", "Cable Size", "value_mismatch", "MEDIUM",
        "케이블 굵기가 도면과 설비 목록에서 다릅니다",
        "P-101의 전원 케이블 굵기가 설비 목록에는 25 mm², 전기 도면에는 35 mm²로 기재되어 있습니다.",
        "케이블 굵기가 다르면 허용 전류와 전압 강하 계산 결과가 달라지고, 전선관 규격에도 영향을 줍니다. "
        "두 값 중 어느 것이 최신 설계인지 확인이 필요합니다.",
        evidence=[
            {"document": "Equipment_List.xlsx", "location": "Row 7", "value": "25", "unit": "mm2"},
            {"document": "Electrical_Drawing.pdf", "location": "Dwg E-201", "value": "35", "unit": "mm2"},
        ],
        impact_items=["허용 전류 확인", "전압 강하 계산", "전선관 규격 산정"],
        disposition="action_required",
        reviewed_by="김설계 (전기)",
        review_comment="부하 증가로 케이블을 35 mm²로 상향한 변경이 설비 목록에 반영되지 않은 것으로 확인. "
                       "설비 목록 갱신 요청함 (DCR-2024-018). 갱신 확인 후 조치 완료로 전환 예정.",
    )

    add_issue(
        "P-101", "Breaker Size", "value_mismatch", "MEDIUM",
        "차단기 용량이 도면과 설비 목록에서 다릅니다",
        "P-101의 차단기 용량이 설비 목록에는 50 A, 전기 도면에는 63 A로 기재되어 있습니다.",
        "케이블 굵기 불일치와 함께 나타나는 것으로 보아 같은 설계 변경에서 비롯되었을 가능성이 있습니다. "
        "차단기 용량은 과전류 보호 협조와 배전반 차단 용량 검토에 사용됩니다.",
        evidence=[
            {"document": "Equipment_List.xlsx", "location": "Row 7", "value": "50", "unit": "A"},
            {"document": "Electrical_Drawing.pdf", "location": "Dwg E-201", "value": "63", "unit": "A"},
        ],
        impact_items=["과전류 보호 협조", "배전반 차단 용량 검토"],
    )

    add_issue(
        "P-101", "Flow", "value_mismatch", "LOW",
        "유량 값이 문서 간에 근소하게 다릅니다",
        "P-101의 유량이 설비 목록에는 120 m³/h, P&ID에는 125 m³/h로 기재되어 있습니다. 차이는 약 4%입니다.",
        "차이가 크지 않아 반올림이나 단순 표기 차이일 수 있으나, 값 자체가 다르므로 검토 목록에 포함했습니다. "
        "펌프 선정 및 배관 유속 검토의 기준값입니다.",
        evidence=[
            {"document": "Equipment_List.xlsx", "location": "Row 7", "value": "120", "unit": "m3/h"},
            {"document": "P&ID.pdf", "location": "Dwg P-201", "value": "125", "unit": "m3/h"},
        ],
        impact_items=["펌프 선정 적정성", "배관 유속·구경 검토"],
    )

    add_issue(
        "P-102", "Model", "spec_mismatch", "MEDIUM",
        "같은 설비의 모델명이 문서마다 다릅니다",
        "P-102의 모델명이 설비 목록에는 CR32-4, P&ID에는 CR64-4로 기재되어 있습니다.",
        "CR32와 CR64는 유량·양정 곡선이 다른 별개의 펌프 모델입니다. 어느 쪽이 실제 설치 대상인지에 따라 "
        "성능 검토와 예비품 조달 기준이 달라집니다.",
        evidence=[
            {"document": "Equipment_List.xlsx", "location": "Row 8", "value": "CR32-4", "unit": None},
            {"document": "P&ID.pdf", "location": "Dwg P-202", "value": "CR64-4", "unit": None},
        ],
        impact_items=["펌프 성능 곡선 확인", "예비품·부품 조달 기준", "정비 매뉴얼 기준"],
    )

    add_issue(
        "P-102", "Efficiency", "missing", "LOW",
        "효율 값이 어느 문서에도 없습니다",
        "P-102의 효율이 업로드된 문서 어디에도 기재되어 있지 않습니다. 같은 유형인 M-101, M-102에는 "
        "효율 값이 있습니다.",
        "값이 서로 충돌하는 것은 아니지만, 같은 종류의 다른 설비에는 있는 항목이 빠져 있어 문서 누락으로 "
        "표시했습니다. 소비전력과 부하 계산 정확도 확인에 사용됩니다.",
        evidence=[
            {"document": "Motor_Spec.pdf", "location": "p.19", "value": "(기재 없음)", "unit": None},
            {"document": "Equipment_List.xlsx", "location": "Row 8", "value": "(기재 없음)", "unit": None},
        ],
        impact_items=["소비전력 재확인", "부하 계산 정확도"],
    )

    add_issue(
        "AHU-101", "Power", "value_mismatch", "MEDIUM",
        "정격출력이 전기 도면에서만 다르게 기재되어 있습니다",
        "AHU-101의 정격출력이 설비 목록과 장비 사양서에는 15 kW, 전기 도면에는 18.5 kW로 기재되어 "
        "있습니다.",
        "M-101과 유사한 형태의 불일치입니다. 도면 값(18.5 kW)이 반영되어 케이블·차단기가 선정되었는지, "
        "아니면 사양서 값(15 kW)이 맞는지 확인이 필요합니다.",
        evidence=[
            {"document": "Equipment_List.xlsx", "location": "Row 12", "value": "15", "unit": "kW"},
            {"document": "Motor_Spec.pdf", "location": "p.27", "value": "15", "unit": "kW"},
            {"document": "Electrical_Drawing.pdf", "location": "Dwg E-115", "value": "18.5", "unit": "kW"},
        ],
        impact_items=["팬 정격전류(A) 재계산", "케이블 굵기 산정", "차단기 용량 선정"],
    )

    add_issue(
        "AHU-101", "Weight", "missing", "INFO",
        "중량이 한 문서에서만 확인됩니다",
        "AHU-101의 중량(450 kg)은 설비 목록에만 있고 다른 문서에는 비교할 값이 없습니다.",
        "교차검증할 두 번째 출처가 없어 값이 맞는지 시스템이 판단할 수 없습니다. 참고 정보로만 표시합니다.",
        evidence=[
            {"document": "Equipment_List.xlsx", "location": "Row 12", "value": "450", "unit": "kg"},
        ],
        impact_items=["구조 하중 검토", "양중·설치 계획"],
        disposition="intentional",
        reviewed_by="이검토 (기계)",
        review_comment="중량은 설비 목록이 유일한 공식 출처이며 제조사 카탈로그(450 kg)와 일치 확인. "
                       "단일 출처는 의도된 것으로, 구조·양중 검토는 이 값 기준으로 진행하면 됨. 추가 조치 불필요.",
    )

    db.commit()
    db.refresh(project)
    return project
