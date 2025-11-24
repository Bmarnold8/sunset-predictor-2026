# src/sunset_classification.py

"""
Educational sunset-condition classifiers.

Each evaluate_* function returns:
  - headline (string)
  - detail_lines (list of strings)
  - explanation (string)

All headlines include an emoji label:
  🟢 Ideal
  🟡 Neutral / non-enhancing (or mixed)
  🔴 Not ideal
"""

from typing import List, Tuple


def _label(rating: str) -> str:
    """
    rating: "ideal" | "neutral" | "not_ideal"
    """
    rating = rating.lower().strip()
    if rating == "ideal":
        return "🟢 Ideal"
    if rating == "not_ideal":
        return "🔴 Not ideal"
    return "🟡 Neutral / non-enhancing"


# -----------------------------
# FAR WEST (468–936 km)
# -----------------------------
def evaluate_far_west(low: float, mid: float, high: float) -> Tuple[str, List[str], str]:
    ideal = (high < 10) and (mid < 10) and (low < 10)

    if ideal:
        headline = f"The far west is expected to be clear – {_label('ideal')}"
        expl = (
            "Clear far western skies create sunsets that seem to last forever. "
            "Any far-west clouds along the azimuth could shorten or mute the sunset."
        )
    else:
        headline = f"The far west is expected to be cloudy – {_label('not_ideal')}"
        expl = (
            "Clouds far to the west can restrict incoming light near sunset. "
            "This may shorten the visible sunset or reduce color intensity, especially late in the event."
        )

    lines = [
        "Cloud cover between 468km and 936km west along the azimuth:",
        f"  Average low cloud cover:  {low:5.1f}%",
        f"  Average mid cloud cover:  {mid:5.1f}%",
        f"  Average high cloud cover: {high:5.1f}%"
    ]
    return headline, lines, expl


# -----------------------------
# OVERHEAD HEIGHT (local)
# -----------------------------
def evaluate_overhead_height(low: float, mid: float, high: float) -> Tuple[str, List[str], str]:
    # Ideal if low is small and mid/high present (>=10%) — this is your rule.
    ideal = (low < 10) and ((mid >= 10) or (high >= 10))

    if ideal:
        headline = f"Overhead clouds are expected to be high – {_label('ideal')}"
        expl = (
            "During sunset, sunlight passes through more atmosphere, scattering blue light. "
            "Higher clouds can reflect deeper red/orange hues back toward you. "
            "Low clouds nearby can shorten or block the sunset."
        )
    else:
        # If low clouds exceed threshold, it's not ideal.
        if low >= 10:
            headline = f"Overhead clouds are expected to be low – {_label('not_ideal')}"
            expl = (
                "Low clouds near your location can block the sun’s final light and reduce color. "
                "This often shortens the sunset or turns it gray."
            )
        else:
            headline = f"Overhead skies are expected to be clear – {_label('neutral')}"
            expl = (
                "Clear overhead skies do not block the sunset, but they also provide fewer mid/high clouds "
                "to reflect color across the sky above you."
            )

    lines = [
        "Overhead cloud cover at your location:",
        f"  Low cloud cover:  {low:5.1f}%",
        f"  Mid cloud cover:  {mid:5.1f}%",
        f"  High cloud cover: {high:5.1f}%",
        "Cloud base altitude guidance (future HRRR feature): 4200m–22000m",
    ]
    return headline, lines, expl


# -----------------------------
# OVERHEAD COVERAGE % (local)
# -----------------------------
def evaluate_overhead_coverage(low: float, mid: float, high: float) -> Tuple[str, List[str], str]:
    ideal = (low < 10) and (
        (30 <= mid <= 90) or (30 <= high <= 90)
    )

    clear_neutral = (low < 10) and (mid < 30) and (high < 30)

    if ideal:
        headline = f"Overhead coverage % is expected to be moderate – {_label('ideal')}"
        expl = (
            "Moderate mid/high overhead coverage can ‘catch’ the sunset light and spread color above you. "
            "If mid clouds get very thick (roughly >60%), they may block light from higher layers."
        )
    elif low >= 10:
        headline = f"Overhead low-cloud coverage is substantial – {_label('not_ideal')}"
        expl = (
            "Substantial low-cloud coverage overhead often blocks the sun’s final light, reducing color "
            "and shortening the sunset."
        )
    elif clear_neutral:
        headline = f"Overhead skies are mostly clear – {_label('neutral')}"
        expl = (
            "Clear overhead conditions do not prevent a good sunset, but they provide limited mid/high "
            "cloud surfaces to reflect color above you."
        )
    else:
        headline = f"Overhead coverage is mixed – {_label('neutral')}"
        expl = (
            "Some overhead cloud layers may help reflect color, but the pattern isn't strongly ideal or harmful."
        )

    lines = [
        "Overhead coverage at your location:",
        f"  Average low cloud cover:  {low:5.1f}%",
        f"  Average mid cloud cover:  {mid:5.1f}%",
        f"  Average high cloud cover: {high:5.1f}%",
        "Ideal overhead pattern: low < 10%, and mid/high in 30–90%",
    ]
    return headline, lines, expl


# -----------------------------
# WESTERN BAND (252–350 km)
# -----------------------------
def evaluate_western_band(low: float, mid: float, high: float) -> Tuple[str, List[str], str]:
    ideal = (low < 10) and (mid < 10) and (30 <= high <= 90)
    clear_neutral = (low < 10) and (mid < 10) and (high < 30)

    if ideal:
        headline = f"Western coverage % is expected to be moderate – {_label('ideal')}"
        expl = (
            "Moderate high clouds to the west can reflect sunset color near the horizon. "
            "Too many low/mid clouds westward can block the light entirely."
        )
    elif (low >= 10) or (mid >= 10):
        headline = f"Western low/mid clouds are substantial – {_label('not_ideal')}"
        expl = (
            "Low or mid clouds to the west often block incoming sunset light, muting or shortening the sunset."
        )
    elif clear_neutral:
        headline = f"Western skies are mostly clear – {_label('neutral')}"
        expl = (
            "Clear western skies do not block the sunset, but limited high clouds may reduce the intensity "
            "of reflected color near the horizon."
        )
    else:
        headline = f"Western cloud pattern is mixed – {_label('neutral')}"
        expl = (
            "Some western high clouds may help, but the overall pattern isn't strongly ideal or harmful."
        )

    lines = [
        "Cloud cover between 252km and 350km west along the azimuth:",
        f"  Average low cloud cover:  {low:5.1f}%",
        f"  Average mid cloud cover:  {mid:5.1f}%",
        f"  Average high cloud cover: {high:5.1f}%",
        "Ideal western pattern: high in 30–90% with low/mid < 10%",
    ]
    return headline, lines, expl


# -----------------------------
# CLOUD HORIZON BAND (350–468 km)
# -----------------------------
def evaluate_cloud_horizon(low: float, mid: float, high: float) -> Tuple[str, List[str], str]:
    ideal = (low < 10) and (mid < 10) and (high < 10)

    if ideal:
        headline = f"The cloud horizon is expected to be clear – {_label('ideal')}"
        expl = (
            "A clear horizon band preserves the final stage of sunset light, enabling longer and more vivid color."
        )
    else:
        headline = f"Distant clouds may obscure the horizon – {_label('not_ideal')}"
        expl = (
            "Clouds near the horizon band can block or weaken the last stage of sunset light. "
            "This may shorten the sunset or reduce horizon-level glow."
        )

    lines = [
        "Cloud cover between 350km and 468km west along the azimuth:",
        f"  Average low cloud cover:  {low:5.1f}%",
        f"  Average mid cloud cover:  {mid:5.1f}%",
        f"  Average high cloud cover: {high:5.1f}%",
    ]
    return headline, lines, expl
