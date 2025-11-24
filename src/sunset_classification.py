# src/sunset_classification.py

from __future__ import annotations


# ----------------------------
# Tunable thresholds (v1)
# ----------------------------

# "Clear" threshold used in Far West & Cloud Horizon
CLEAR_MAX = 10.0  # percent

# "Ideal high-cloud deck" window (used overhead + west)
IDEAL_MIN = 30.0  # percent
IDEAL_MAX = 90.0  # percent

# "Some mid/high present" threshold for overhead-height logic
PRESENT_MIN = 10.0  # percent


# ----------------------------
# ANSI color helpers (terminal)
# ----------------------------

RESET = "\033[0m"
BOLD = "\033[1m"
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"


def _ideal(text: str) -> str:
    return f"{BOLD}{GREEN}{text}{RESET}"


def _not_ideal(text: str) -> str:
    return f"{BOLD}{RED}{text}{RESET}"


def _neutral(text: str) -> str:
    return f"{BOLD}{YELLOW}{text}{RESET}"


# ----------------------------
# Simple helper utilities
# ----------------------------

def _in_range(x: float, lo: float, hi: float) -> bool:
    return lo <= x <= hi


def _fmt_pct(x: float) -> str:
    return f"{x:5.1f}%"


# ----------------------------
# Condition evaluators
# Each returns:
#   headline (str)
#   detail_lines (list[str])
#   explanation (str)
# ----------------------------

def evaluate_far_west(avg_low: float, avg_mid: float, avg_high: float):
    """
    Far West (468–936 km along azimuth)

    Ideal: high <10 AND mid <10 AND low <10
    Not ideal: otherwise
    """
    clear_all = (avg_high < CLEAR_MAX) and (avg_mid < CLEAR_MAX) and (avg_low < CLEAR_MAX)

    if clear_all:
        headline = f"The far west is expected to be clear – {_ideal('Ideal condition')}"
        explanation = (
            "Clear far western skies allow sunlight to travel a long distance toward your location. "
            "This supports prolonged sunset color and a slower fade after the sun drops below the horizon."
        )
    else:
        headline = f"The far west is expected to be cloudy – {_not_ideal('Not ideal')}"
        explanation = (
            "Clouds far to the west can restrict incoming light near sunset. "
            "This may shorten the visible sunset or reduce color intensity, especially late in the event."
        )

    detail_lines = [
        "Cloud cover between 468km and 936km west along the azimuth:",
        f"  Average low cloud cover:  {_fmt_pct(avg_low)}",
        f"  Average mid cloud cover:  {_fmt_pct(avg_mid)}",
        f"  Average high cloud cover: {_fmt_pct(avg_high)}",
    ]

    return headline, detail_lines, explanation


def evaluate_overhead_height(low_at: float, mid_at: float, high_at: float):
    """
    Overhead 'height' proxy (using cover only for v1)

    Ideal: low <10 AND (mid >=10 OR high >=10)
    Not ideal: low >=10
    Neutral/clear: low <10 AND mid <10 AND high <10
    """
    low_blocking = (low_at >= CLEAR_MAX)
    mid_or_high_present = (mid_at >= PRESENT_MIN) or (high_at >= PRESENT_MIN)
    clear_overhead = (low_at < CLEAR_MAX) and (mid_at < PRESENT_MIN) and (high_at < PRESENT_MIN)

    if low_blocking:
        headline = f"Overhead clouds are expected to be low – {_not_ideal('Not ideal')}"
        explanation = (
            "Substantial low-cloud coverage overhead can obstruct sunlight and reduce "
            "the amount of light reaching higher cloud layers. This often shortens or mutes the sunset."
        )
    elif clear_overhead:
        headline = f"Overhead skies are expected to be clear – {_neutral('Neutral / non-enhancing')}"
        explanation = (
            "Clear overhead skies do not block the sunset, but they also provide fewer mid/high clouds "
            "to reflect color across the sky above you."
        )
    elif mid_or_high_present:
        headline = f"Overhead clouds are expected to be high – {_ideal('Ideal condition')}"
        explanation = (
            "Mid and high clouds overhead can reflect long-wavelength sunset light (reds/oranges) "
            "back toward your location. This supports broader color across the sky."
        )
    else:
        headline = f"Overhead cloud height conditions are mixed – {_not_ideal('Not ideal')}"
        explanation = (
            "Overhead cloud structure is outside the ideal pattern for strong color reflection."
        )

    detail_lines = [
        "Overhead cloud cover at your location:",
        f"  Low cloud cover:  {_fmt_pct(low_at)}",
        f"  Mid cloud cover:  {_fmt_pct(mid_at)}",
        f"  High cloud cover: {_fmt_pct(high_at)}",
        "Cloud base altitude guidance (future HRRR feature): 4200m–22000m",
    ]

    return headline, detail_lines, explanation


def evaluate_overhead_coverage(low_at: float, mid_at: float, high_at: float):
    """
    Overhead coverage %

    Ideal moderate: low <10 AND (mid in 30–90 OR high in 30–90)
    Not ideal low-blocking: low >=10
    Not ideal clear: low <10 AND mid <30 AND high <30
    Not ideal off-window/heavy: low <10 AND not ideal moderate and not clear
    """
    low_blocking = (low_at >= CLEAR_MAX)
    ideal_moderate = (low_at < CLEAR_MAX) and (
        _in_range(mid_at, IDEAL_MIN, IDEAL_MAX) or _in_range(high_at, IDEAL_MIN, IDEAL_MAX)
    )
    clear_overhead = (low_at < CLEAR_MAX) and (mid_at < IDEAL_MIN) and (high_at < IDEAL_MIN)

    if low_blocking:
        headline = f"Overhead cloud coverage is substantial – {_not_ideal('Not ideal')}"
        explanation = (
            "Low clouds above the threshold are substantial enough to obstruct light. "
            "This can block your view of the brightest horizon glow and shorten the sunset."
        )
    elif ideal_moderate:
        headline = f"Overhead coverage is moderate – {_ideal('Ideal condition')}"
        explanation = (
            "Moderate mid/high cloud coverage overhead can catch sunlight and reflect color across the sky. "
            "This is one of the most reliable patterns for vivid overhead reds and oranges."
        )
    elif clear_overhead:
        headline = f"Overhead skies are mostly clear – {_neutral('Neutral / non-enhancing')}"
        explanation = (
            "Clear overhead conditions do not prevent a good sunset, but they provide limited "
            "mid/high cloud surfaces to reflect color above you."
        )
    else:
        headline = f"Overhead coverage is outside the ideal range – {_not_ideal('Not ideal')}"
        explanation = (
            "Overhead cloud coverage is either too thin in mid/high layers or too dense in a way "
            "that reduces ideal color reflection."
        )

    detail_lines = [
        "Overhead coverage at your location:",
        f"  Average low cloud cover:  {_fmt_pct(low_at)}",
        f"  Average mid cloud cover:  {_fmt_pct(mid_at)}",
        f"  Average high cloud cover: {_fmt_pct(high_at)}",
        f"Ideal overhead pattern: low < {CLEAR_MAX:.0f}%, and mid/high in {IDEAL_MIN:.0f}–{IDEAL_MAX:.0f}%",
    ]

    return headline, detail_lines, explanation


def evaluate_western_band(avg_low: float, avg_mid: float, avg_high: float):
    """
    Western band (252–350 km)

    Ideal: low <10 AND mid <10 AND high in 30–90
    Not ideal low/mid blocking: low >=10 OR mid >=10
    Clear / non-factor: low <10 AND mid <10 AND high <30
    Not ideal overcast high: low <10 AND mid <10 AND high >90
    """
    low_or_mid_blocking = (avg_low >= CLEAR_MAX) or (avg_mid >= CLEAR_MAX)
    ideal_high_deck = (avg_low < CLEAR_MAX) and (avg_mid < CLEAR_MAX) and _in_range(avg_high, IDEAL_MIN, IDEAL_MAX)
    clear_west = (avg_low < CLEAR_MAX) and (avg_mid < CLEAR_MAX) and (avg_high < IDEAL_MIN)
    overcast_high = (avg_low < CLEAR_MAX) and (avg_mid < CLEAR_MAX) and (avg_high > IDEAL_MAX)

    if low_or_mid_blocking:
        headline = f"Western low/mid clouds may obstruct sunlight – {_not_ideal('Not ideal')}"
        explanation = (
            "Low or mid-level clouds in the western direction can interrupt the light path "
            "toward your location, often muting or shortening the sunset."
        )
    elif ideal_high_deck:
        headline = f"Western high-cloud coverage is moderate – {_ideal('Ideal condition')}"
        explanation = (
            "A moderate deck of high clouds in this western band is a strong enhancer of red/orange glow. "
            "These clouds reflect sunset light toward you without significantly blocking the horizon."
        )
    elif clear_west:
        headline = f"Western skies are mostly clear – {_neutral('Neutral / non-enhancing')}"
        explanation = (
            "Clear western skies do not block the sunset, but limited high clouds may reduce "
            "the intensity of reflected color near the horizon."
        )
    elif overcast_high:
        headline = f"Western high-cloud coverage is dense – {_not_ideal('Not ideal')}"
        explanation = (
            "Very dense high clouds can reduce contrast and dim the sunset’s color, "
            "even if low/mid layers are clear."
        )
    else:
        headline = f"Western cloud conditions are mixed – {_not_ideal('Not ideal')}"
        explanation = (
            "Western clouds do not match the ideal high-cloud pattern for strong glow."
        )

    detail_lines = [
        "Cloud cover between 252km and 350km west along the azimuth:",
        f"  Average low cloud cover:  {_fmt_pct(avg_low)}",
        f"  Average mid cloud cover:  {_fmt_pct(avg_mid)}",
        f"  Average high cloud cover: {_fmt_pct(avg_high)}",
        f"Ideal western pattern: high in {IDEAL_MIN:.0f}–{IDEAL_MAX:.0f}% with low/mid < {CLEAR_MAX:.0f}%",
    ]

    return headline, detail_lines, explanation


def evaluate_cloud_horizon(avg_low: float, avg_mid: float, avg_high: float):
    """
    Cloud Horizon band (350–468 km)

    Ideal: all layers <10
    Not ideal: otherwise
    """
    clear_all = (avg_high < CLEAR_MAX) and (avg_mid < CLEAR_MAX) and (avg_low < CLEAR_MAX)

    if clear_all:
        headline = f"The cloud horizon is expected to be clear – {_ideal('Ideal condition')}"
        explanation = (
            "A clear horizon band allows sunlight to reach you unobstructed. "
            "This supports longer and cleaner horizon color near sunset."
        )
    else:
        headline = f"Distant clouds may obscure the horizon – {_not_ideal('Not ideal')}"
        explanation = (
            "Clouds near the horizon band can block or weaken the last stage of sunset light. "
            "This may shorten the sunset or reduce horizon-level glow."
        )

    detail_lines = [
        "Cloud cover between 350km and 468km west along the azimuth:",
        f"  Average low cloud cover:  {_fmt_pct(avg_low)}",
        f"  Average mid cloud cover:  {_fmt_pct(avg_mid)}",
        f"  Average high cloud cover: {_fmt_pct(avg_high)}",
    ]

    return headline, detail_lines, explanation
