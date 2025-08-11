"""Qimen Dunjia chart generation and prompt assembly.

This module contains a stub implementation of the Qimen Dunjia algorithm.  It
generates a minimal chart based on the sexagenary cycle and fills the nine
palaces with placeholder symbols.  In production you should replace
`generate_chart()` with a call to a proper charting library (e.g. the
`kinqimen` package).  The prompt assembly function combines the generated
chart with the user’s question to give the large language model (LLM) a
structured context.
"""

from __future__ import annotations

import random
from datetime import datetime, date, time, timedelta
from typing import Dict, Any, List

from dateutil import tz


HEAVENLY_STEMS = list("甲乙丙丁戊己庚辛壬癸")
EARTHLY_BRANCHES = list("子丑寅卯辰巳午未申酉戌亥")
EIGHT_GATES = ["休", "生", "伤", "杜", "景", "死", "惊", "开"]
NINE_STARS = ["蓬", "任", "冲", "辅", "英", "芮", "柱", "心", "禽"]
GODS = ["值符", "腾蛇", "太阴", "六合", "白虎", "玄武", "九地", "九天"]


def _sexagenary_index(dt: datetime) -> int:
    """Compute the index (0–59) of the sexagenary cycle for a given datetime.

    The sexagenary cycle repeats every 60 units.  We take 1984‑01‑01 00:00
    (Gregorian) as the base point of the cycle (a 甲子 year) and compute
    the difference in days.  This yields a rough approximation of the
    Heavenly‑Stem/Earthly‑Branch combination for the current day.  This
    implementation is **not exact**, because it ignores solar terms and the
    Chinese lunar calendar, but it provides a deterministic placeholder.
    """
    base = datetime(1984, 1, 1, tzinfo=tz.gettz("UTC"))
    delta_days = (dt - base).days
    return delta_days % 60


def _stem_branch(index: int) -> str:
    """Return the combined Heavenly Stem and Earthly Branch for the given index."""
    return HEAVENLY_STEMS[index % 10] + EARTHLY_BRANCHES[index % 12]


def generate_chart(dt: datetime) -> Dict[str, Any]:
    """Generate a simplified Qimen chart for the given datetime.

    The returned dictionary contains:

    * `sexagenary_cycle`: the Heavenly‑Stem/Earthly‑Branch combination for
      the date (approximate).
    * `palaces`: a list of nine palace objects.  Each palace includes a
      `gate`, `star` and `god`, selected deterministically based on the
      cycle index.

    This function deliberately avoids the full Qimen algorithm.  In
    production you must compute the Yin/Yang dun, the 24 solar terms and
    rotate the plates according to the rules【232079094909397†L287-L299】.
    """
    index = _sexagenary_index(dt)
    stem_branch = _stem_branch(index)
    # Determine starting offsets for gates, stars and gods
    gate_offset = index % len(EIGHT_GATES)
    star_offset = index % len(NINE_STARS)
    god_offset = index % len(GODS)
    palaces: List[Dict[str, str]] = []
    for i in range(9):
        gate = EIGHT_GATES[(gate_offset + i) % len(EIGHT_GATES)]
        star = NINE_STARS[(star_offset + i) % len(NINE_STARS)]
        god = GODS[(god_offset + i) % len(GODS)]
        palaces.append({
            "position": i + 1,
            "gate": gate,
            "star": star,
            "god": god
        })
    return {
        "sexagenary_cycle": stem_branch,
        "palaces": palaces
    }


def chart_to_prompt(chart: Dict[str, Any], question: str, context: str | None = None) -> str:
    """Assemble a prompt for the LLM from a chart and a user question.

    The prompt includes:

    * A preamble explaining that the answer should integrate Qimen symbolism.
    * The sexagenary cycle and a textual representation of the nine palaces.
    * Optional additional context (e.g. domain knowledge for specific tools).
    * The user’s question.

    A deterministic format makes it easier to adjust the prompt in future
    without affecting the rest of the system.
    """
    lines: List[str] = []
    lines.append("You are a Qimen Dunjia divination assistant.  Use the provided chart to guide your answer.")
    lines.append(f"Sexagenary cycle (approx.): {chart['sexagenary_cycle']}")
    lines.append("Nine palaces:")
    for palace in chart["palaces"]:
        lines.append(f"  Palace {palace['position']}: Gate={palace['gate']}, Star={palace['star']}, God={palace['god']}")
    if context:
        lines.append("Context:")
        lines.append(context)
    lines.append("Question:")
    lines.append(question.strip())
    return "\n".join(lines)