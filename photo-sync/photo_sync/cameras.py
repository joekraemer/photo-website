"""Turn EXIF Make + Model into the name people know a camera by.

    camera_name("SONY", "ILCE-6400")            -> "Sony α6400"
    camera_name("NIKON CORPORATION", "NIKON Z 6_2") -> "Nikon Z6 II"
    camera_name("Canon", "Canon EOS R5")        -> "Canon EOS R5"

Sony and Nikon Z model codes follow a pattern, so they are decoded by rule.
A short table covers the codes that don't. Anything else falls back to
"<brand> <model>" with the brand said once.
"""

from __future__ import annotations

import re

_ROMAN = {1: "", 2: "II", 3: "III", 4: "IV", 5: "V", 6: "VI", 7: "VII", 8: "VIII", 9: "IX"}

# EXIF Make (upper-cased) -> brand as written in marketing.
_BRANDS = {
    "SONY": "Sony",
    "CANON": "Canon",
    "NIKON": "Nikon",
    "NIKON CORPORATION": "Nikon",
    "FUJIFILM": "Fujifilm",
    "FUJI PHOTO FILM CO., LTD.": "Fujifilm",
    "OLYMPUS IMAGING CORP.": "Olympus",
    "OLYMPUS CORPORATION": "Olympus",
    "OM DIGITAL SOLUTIONS": "OM System",
    "PANASONIC": "Panasonic",
    "LEICA CAMERA AG": "Leica",
    "RICOH IMAGING COMPANY, LTD.": "Ricoh",
    "PENTAX": "Pentax",
    "APPLE": "Apple",
    "GOOGLE": "Google",
    "SAMSUNG": "Samsung",
    "DJI": "DJI",
    "GOPRO": "GoPro",
    "HASSELBLAD": "Hasselblad",
}

# Codes no rule below decodes. Keys are (brand, model with the brand removed),
# upper-cased.
_TABLE = {
    ("SONY", "ZV-E10M2"): "ZV-E10 II",
    ("SONY", "ILME-FX3"): "FX3",
    ("SONY", "ILME-FX30"): "FX30",
    ("SONY", "ILME-FX6V"): "FX6",
    ("SONY", "ILCA-99M2"): "α99 II",
    ("SONY", "ILCA-77M2"): "α77 II",
    ("NIKON", "COOLPIX P1000"): "Coolpix P1000",
    ("NIKON", "COOLPIX P950"): "Coolpix P950",
}

# ILCE-6400 -> α6400, ILCE-7M3 -> α7 III, ILCE-7RM4A -> α7R IVA, ILCE-7CR -> α7CR
_SONY_ILCE = re.compile(r"^ILCE-(\d+)([A-Z]*?)(?:M(\d))?(A)?$")
# DSC-RX100M7 -> RX100 VII, DSC-RX10M4 -> RX10 IV, DSC-RX1RM2 -> RX1R II
_SONY_DSC = re.compile(r"^DSC-(RX\d+R?)(?:M(\d))?(A)?$")
# Z 6_2 -> Z6 II, Z 50 -> Z50, Z f -> Zf
_NIKON_Z = re.compile(r"^Z ?(\d+|f|fc)(?:_(\d))?$", re.IGNORECASE)


def _clean(text) -> str:
    return re.sub(r"\s+", " ", str(text or "").strip("\x00 ").strip())


def brand_name(make) -> str:
    make = _clean(make)
    if not make:
        return ""
    upper = make.upper()
    if upper in _BRANDS:
        return _BRANDS[upper]
    first = upper.split()[0].rstrip(",.")
    if first in _BRANDS:
        return _BRANDS[first]
    return make if not make.isupper() else make.title()


def _strip_brand(model: str, brand: str, make: str) -> str:
    for word in {brand, make, make.split()[0] if make else ""}:
        if word and model.upper().startswith(word.upper() + " "):
            return model[len(word) + 1:].strip()
    return model


def _roman(n: str | None) -> str:
    return _ROMAN.get(int(n), n) if n else ""


def _decode(brand: str, model: str) -> str | None:
    key = model.upper()
    if (brand.upper(), key) in _TABLE:
        return _TABLE[(brand.upper(), key)]
    if brand == "Sony":
        if m := _SONY_ILCE.match(key):
            number, letters, gen, a = m.groups()
            gen = _roman(gen)
            return f"α{number}{letters}" + (f" {gen}" if gen else "") + (a or "")
        if m := _SONY_DSC.match(key):
            body, gen, a = m.groups()
            gen = _roman(gen)
            return body + (f" {gen}" if gen else "") + (a or "")
    if brand == "Nikon" and (m := _NIKON_Z.match(model)):
        number, gen = m.groups()
        gen = _roman(gen)
        return f"Z{number}" + (f" {gen}" if gen else "")
    return None


def camera_name(make, model) -> str | None:
    """Friendly camera name, or None when EXIF names no camera at all."""
    make, model = _clean(make), _clean(model)
    if not model:
        return None
    brand = brand_name(make)
    if not brand and re.match(r"^(ILCE|ILCA|ILME|DSC)-", model, re.IGNORECASE):
        brand = "Sony"  # Make stripped but the model code is unmistakable
    rest = _strip_brand(model, brand, make)
    pretty = _decode(brand, rest) or rest
    return f"{brand} {pretty}" if brand else pretty
