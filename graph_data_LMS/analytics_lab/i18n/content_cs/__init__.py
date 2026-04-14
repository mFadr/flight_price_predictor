"""Czech overlays for the learning content.

Each module holds plain dictionaries keyed by content id (lesson, question, exercise, case,
capstone ...). ``apply_all`` lays them over the shared English objects via
``analytics_lab.i18n.overlay``; the English text is restored when the language switches back.
"""

from __future__ import annotations

import importlib

MODULES = ("descriptive", "diagnostic", "predictive", "prescriptive", "visualization")


def _optional(name: str):
    try:
        return importlib.import_module(f"analytics_lab.i18n.content_cs.{name}")
    except ModuleNotFoundError as exc:
        if exc.name != f"analytics_lab.i18n.content_cs.{name}":
            raise
        return None


def topics() -> dict[str, str]:
    """English -> Czech question topics from every questions_<module> file."""
    out: dict[str, str] = {}
    for module in MODULES:
        mod = _optional(f"questions_{module}")
        if mod:
            out.update(getattr(mod, "TOPICS", {}))
    return out


def apply_all() -> None:
    from analytics_lab import models
    from analytics_lab.assessment.bank import EXERCISES_BY_ID, QUESTIONS_BY_ID
    from analytics_lab.curriculum import LESSONS_BY_ID
    from analytics_lab.i18n import overlay, overlay_dict

    general = _optional("general")
    if general:
        overlay_dict(models.MODULES, general.MODULES)
        overlay_dict(models.MODULE_QUESTIONS, general.MODULE_QUESTIONS)
        from analytics_lab.curriculum.competencies import BY_ID as COMPETENCIES

        for cid, patch in general.COMPETENCIES.items():
            overlay(COMPETENCIES[cid], patch)

    for module in MODULES:
        for kind, registry in (("lessons", LESSONS_BY_ID), ("questions", QUESTIONS_BY_ID), ("exercises", EXERCISES_BY_ID)):
            mod = _optional(f"{kind}_{module}")
            if mod:
                for item_id, patch in getattr(mod, kind.upper()).items():
                    overlay(registry[item_id], patch)

    if general:
        # Shared rubric lines, unless an exercise overlay already replaced its rubric.
        for ex in EXERCISES_BY_ID.values():
            if ex.rubric and all(isinstance(c, tuple) and c[0] in general.RUBRIC for c in ex.rubric):
                overlay(ex, {"rubric": [(general.RUBRIC[c], pts) for c, pts in ex.rubric]})

    capstones = _optional("capstones")
    if capstones:
        from analytics_lab.assessment.capstones import CAPSTONES_BY_ID

        for cid, patch in capstones.CAPSTONES.items():
            overlay(CAPSTONES_BY_ID[cid], patch)
        for eid, patch in capstones.EXERCISES.items():
            overlay(EXERCISES_BY_ID[eid], patch)

    cases = _optional("cases")
    if cases:
        from analytics_lab.assessment.cases import CASES_BY_ID, STANDARD_RUBRIC

        for criterion, patch in zip(STANDARD_RUBRIC, cases.STANDARD_RUBRIC):
            overlay(criterion, patch)
        for cid, patch in cases.CASES.items():
            overlay(CASES_BY_ID[cid], patch)

    reference = _optional("reference")
    if reference:
        from analytics_lab.curriculum.reference import CHEATSHEETS, GLOSSARY

        overlay_dict(GLOSSARY, reference.GLOSSARY)
        overlay_dict(CHEATSHEETS, reference.cheatsheets())

    datasets = _optional("datasets")
    if datasets:
        from analytics_lab.data.catalog import DATASETS

        for schema, patch in datasets.DATASETS.items():
            overlay(DATASETS[schema], patch)
