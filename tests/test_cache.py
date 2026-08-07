from app.cache import normalize

def test_normalized_lowercase():
    assert normalize("VANS Boots") == "vans boots"

def test_normalize_strips_punctuations():
    assert normalize("Infuse! Boots?!@") == "infuse boots"

def test_normalize_collapse_whitespace():
    assert normalize("vans    infuse         boots") == "vans infuse boots"

def test_normalize_handles_empty_string():
    assert normalize("") == ""