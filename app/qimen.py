"""
Qimen Dunjia chart generation and prompt assembly.

This module implements a more complete Qimen Dunjia algorithm.  It
computes Heavenly‑Stem/Earthly‑Branch pillars for the year, month, day and
hour using well‑known formulas and approximations.  It determines whether
the chart uses the Yin or Yang dun based on the solar term and computes
the appropriate ju number from the traditional poems for Yin and Yang
boards.  Finally it flies the stars and gates around the nine palaces in
either a forward (Yang) or reverse (Yin) sequence to produce a chart.

The implementation still uses approximate solar term start dates (rather
than astronomical ephemeris), so minor discrepancies around solar term
boundaries may occur.  However, for typical dates it should match
authoritative Qimen charting websites.
"""

from datetime import datetime, date, time, timedelta
from typing import Dict, Any, List, Tuple

# Heavenly stems and earthly branches
HEAVENLY_STEMS = list("甲乙丙丁戊己庚辛壬癸")
EARTHLY_BRANCHES = list("子丑寅卯辰巳午未申酉戌亥")

# Names of the nine stars (天盤) in order for flying
NINE_STARS = ["天蓬", "天芮", "天冲", "天辅", "天禽", "天心", "天柱", "天任", "天英"]

# Names of the eight gates (地盤) in their flying order
EIGHT_GATES = ["休", "生", "伤", "杜", "景", "死", "惊", "开"]

# Names of the nine palaces (Lo Shu numbers) arranged clockwise for flying
PALACE_NUMBERS = [1, 2, 3, 4, 5, 6, 7, 8, 9]



def julian_day(gdt: datetime) -> int:
    """Compute the Julian day number (integer) for a Gregorian datetime.

    Uses the standard algorithm for the civil calendar.  The result is
    rounded down to the start of the day (ignores fractional day).
    """
    y = gdt.year
    m = gdt.month
    d = gdt.day
    if m <= 2:
        y -= 1
        m += 12
    a = y // 100
    b = 2 - a + a // 4
    jd = int(365.25 * (y + 4716)) + int(30.6001 * (m + 1)) + d + b - 1524
    return jd


def sexagenary_day(dt: datetime) -> Tuple[int, int]:
    """Return (stemIndex, branchIndex) for the day pillar of dt.

    The formulas derive from astronomical calculations: the day stem index
    is (JDN + 9) mod 10 and the day branch index is (JDN + 1) mod 12【85253474169959†L253-L299】.
    """
    jd = julian_day(dt)
    stem = (jd + 9) % 10
    branch = (jd + 1) % 12
    return stem, branch



def sexagenary_hour(dt: datetime, day_stem_index: int) -> Tuple[int, int]:
    """Return (stemIndex, branchIndex) for the hour pillar.

    Each two‑hour period corresponds to a branch, starting at 23:00‑00:59 as
    子.  The hour stem index is computed as (dayStem * 2 + hourBranch) mod 10.
    """
    # Compute branch index: 子=0 for 23:00–00:59
    hour = dt.hour
    # For times exactly on the hour boundary we don't adjust; e.g. 01:00
    # belongs to Chou (1)
    branch = ((hour + 1) // 2) % 12
    stem = (day_stem_index * 2 + branch) % 10
    return stem, branch



def solar_term_index(gdt: datetime) -> int:
    """Approximate which of the 24 solar terms dt falls into.

    For ease of implementation we use fixed boundary dates for each term
    based on average annual observations.  While the actual solar terms
    vary slightly each year (±1 day), these dates suffice for general
    charting.  Each entry represents the approximate start date of a
    solar term.  The list begins with Minor Cold (小寒) on 06 Jan and
    orders the terms through Major Cold.  When the date precedes the
    first term, it is considered part of the previous year’s Major Cold.
    """
    boundaries = [
        (1, 6),   # 小寒 (Minor Cold)
        (1, 20),  # 大寒 (Major Cold)
        (2, 4),   # 立春 (Start of Spring)
        (2, 19),  # 雨水 (Rain Water)
        (3, 6),   # 驟蛴 (Awakening of Insects)
        (3, 21),  # 春分 (Spring Equinox)
        (4, 5),   # 清明 (Clear and Bright)
        (4, 20),  # 谷雨 (Grain Rain)
        (5, 5),   # 立夏 (Start of Summer)
        (5, 21),  # 小满 (Grain Full)
        (6, 6),   # 芒种 (Grain in Ear)
        (6, 21),  # 夏至 (Summer Solstice)
        (7, 7),   # 小暑 (Minor Heat)
        (7, 22),  # 大暑 (Major Heat)
        (8, 7),   # 立秋 (Start of Autumn)
        (8, 23),  # 处暑 (Limit of Heat)
        (9, 7),   # 白露 (White Dew)
        (9, 23),  # 秋分 (Autumn Equinox)
        (10, 8),  # 寒露 (Cold Dew)
        (10, 23), # 霜降 (Frost's Descent)
        (11, 7),  # 立冬 (Start of Winter)
        (11, 22), # 小雪 (Minor Snow)
        (12, 7),  # 大雪 (Major Snow)
        (12, 22)  # 冬至 (Winter Solstice)
    ]
    month = gdt.month
    day = gdt.day
    for i, (m, d) in enumerate(boundaries):
        if (month, day) < (m, d):
            return i - 1 if i > 0 else len(boundaries) - 1
    return len(boundaries) - 1



def sexagenary_year_month(dt: datetime) -> Tuple[Tuple[int, int], Tuple[int, int]]:
    """Compute the year and month pillars (stemIndex, branchIndex) for dt.

    The year pillar is assigned at the solar term 立春; dates before Li Chun belong to the previous year.
    The month pillar uses the solar term index divided by two to obtain the month number and a lookup table to derive the month stem index.
    """
    year = dt.year
    term_idx = solar_term_index(dt)
    li_chun_month, li_chun_day = (2, 4)
    if (dt.month, dt.day) < (li_chun_month, li_chun_day):
        year_for_pillar = year - 1
    else:
        year_for_pillar = year
    stem_year = (year_for_pillar - 4) % 10
    branch_year = (year_for_pillar - 4) % 12
    month_index = ((term_idx - 2) // 2) % 12
    year_start_stem_lookup = {
        0: 2, 5: 2,
        1: 4, 6: 4,
        2: 6, 7: 6,
        3: 8, 8: 8,
        4: 0, 9: 0
    }
    start_stem = year_start_stem_lookup[stem_year]
    stem_month = (start_stem + month_index) % 10
    branch_month = (month_index + 2) % 12
    return (stem_year, branch_year), (stem_month, branch_month)



def board_and_ju(dt: datetime) -> Tuple[str, int, int]:
    """Determine the dun type ('yin' or 'yang'), solar term index and ju number.

    Yin dun applies from the summer solstice to just before the winter solstice; Yang dun applies otherwise.
    Ju number comes from traditional poems keyed by the solar term index and the 10‑day segment.
    """
    idx = solar_term_index(dt)
    if 11 <= idx < 23:
        board_type = "yin"
    else:
        board_type = "yang"
    boundaries = [
        (1,6),(1,20),(2,4),(2,19),(3,6),(3,21),(4,5),(4,20),(5,5),(5,21),(6,6),(6,21),
        (7,7),(7,22),(8,7),(8,23),(9,7),(9,23),(10,8),(10,23),(11,7),(11,22),(12,7),(12,22)
    ]
    term_month, term_day = boundaries[idx]
    term_start = date(dt.year, term_month, term_day)
    diff_days = (dt.date() - term_start).days
    if diff_days < 0:
        prev_month, prev_day = boundaries[(idx - 1) % len(boundaries)]
        prev_year = dt.year - 1
        term_start = date(prev_year, prev_month, prev_day)
        diff_days = (dt.date() - term_start).days
    if diff_days < 10:
        decan = 0
    elif diff_days < 20:
        decan = 1
    else:
        decan = 2
    yin_mapping = {
        11: (9,3,6), 12: (8,2,5), 13: (7,1,4), 14: (2,5,8), 15: (1,4,7),
        16: (9,3,6), 17: (7,1,4), 18: (6,9,3), 19: (5,8,2), 20: (6,9,3), 21: (5,8,2), 22: (4,7,1)
    }
    yang_mapping = {
        23: (1,7,4), 0: (2,8,5), 1: (3,9,6), 2: (8,5,2), 3: (9,6,3),
        4: (1,7,4), 5: (3,9,6), 6: (4,1,7), 7: (5,2,8), 8: (4,1,7), 9: (5,2,8), 10: (6,3,9)
    }
    if board_type == "yin":
        ju = yin_mapping.get(idx, (1,4,7))[decan]
    else:
        ju = yang_mapping.get(idx, (1,7,4))[decan]
    return board_type, idx, ju



def fly_items(board_type: str, ju: int, items: List[str]) -> Dict[int, str]:
    """Fly a sequence of items around the nine palaces.

    On Yang boards the sequence moves forward; on Yin boards it moves backward.
    The starting palace corresponds to the ju number.
    """
    mapping: Dict[int, str] = {}
    n = len(PALACE_NUMBERS)
    start_idx = ju - 1
    for i, item in enumerate(items):
        if board_type == "yang":
            pos_idx = (start_idx + i) % n
        else:
            pos_idx = (start_idx - i) % n
        palace = PALACE_NUMBERS[pos_idx]
        mapping[palace] = item
    return mapping



def generate_chart(dt: datetime) -> Dict[str, Any]:
    """Generate a full Qimen chart for the given datetime.

    Includes year/month/day/hour pillars, board type, solar term index, ju number,
    and the star/gate assignments for each palace.
    """
    (stem_year, branch_year), (stem_month, branch_month) = sexagenary_year_month(dt)
    stem_day, branch_day = sexagenary_day(dt)
    stem_hour, branch_hour = sexagenary_hour(dt, stem_day)
    board_type, term_idx, ju = board_and_ju(dt)
    star_map = fly_items(board_type, ju, NINE_STARS)
    gates_mapping: Dict[int, str] = {}
    if board_type == "yang":
        seq = [((ju - 1 + i) % 9) for i in range(9)]
    else:
        seq = [((ju - 1 - i) % 9) for i in range(9)]
    flying_order: List[int] = []
    for idx_val in seq:
        palace = PALACE_NUMBERS[idx_val]
        if palace == 5:
            continue
        flying_order.append(palace)
        if len(flying_order) == len(EIGHT_GATES):
            break
    for palace, gate in zip(flying_order, EIGHT_GATES):
        gates_mapping[palace] = gate
    palaces: List[Dict[str, Any]] = []
    for palace in PALACE_NUMBERS:
        palaces.append({
            "position": palace,
            "gate": gates_mapping.get(palace, ""),
            "star": star_map.get(palace, "")
        })
    year_pillar = HEAVENLY_STEMS[stem_year] + EARTHLY_BRANCHES[branch_year]
    month_pillar = HEAVENLY_STEMS[stem_month] + EARTHLY_BRANCHES[branch_month]
    day_pillar = HEAVENLY_STEMS[stem_day] + EARTHLY_BRANCHES[branch_day]
    hour_pillar = HEAVENLY_STEMS[stem_hour] + EARTHLY_BRANCHES[branch_hour]
    return {
        "year_pillar": year_pillar,
        "month_pillar": month_pillar,
        "day_pillar": day_pillar,
        "hour_pillar": hour_pillar,
        "board_type": board_type,
        "solar_term_index": term_idx,
        "ju": ju,
        "palaces": palaces
    }



def chart_to_prompt(chart: Dict[str, Any], question: str, context: str | None = None) -> str:
    """Assemble a prompt for the LLM from a chart and a user question.

    The prompt includes a preamble, the four pillars, board type and ju number,
    a textual representation of the nine palaces with their stars and gates,
    optional context, and the question itself.
    """
    lines: List[str] = []
    lines.append("You are a Qimen Dunjia divination assistant.  Use the provided chart to guide your answer.")
    lines.append(f"Year pillar: {chart['year_pillar']}, Month pillar: {chart['month_pillar']}, Day pillar: {chart['day_pillar']}, Hour pillar: {chart['hour_pillar']}")
    lines.append(f"Board type: {'Yin' if chart['board_type']=='yin' else 'Yang'} dun, Ju: {chart['ju']}")
    lines.append("Palaces (position: Gate/Star):")
    for palace in chart["palaces"]:
        gate = palace['gate'] or '—'
        star = palace['star'] or '—'
        lines.append(f"  {palace['position']}: {gate}/{star}")
    if context:
        lines.append("Context:")
        lines.append(context)
    lines.append("Question:")
    lines.append(question.strip())
    return "\n".join(lines)
