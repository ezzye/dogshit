from bankcleanr.signature import normalise_signature


def test_diacritics_are_removed():
    assert normalise_signature("Café Métro") == "cafe metro"


def test_prefixes_and_suffixes():
    assert normalise_signature("dd Example ltd") == "example"
    assert normalise_signature("sto Sample co") == "sample"


def test_trailing_digits_trimmed():
    assert normalise_signature("merchant 123456 78910") == "merchant"
    assert normalise_signature("merchant 1234") == "merchant 1234"
    assert normalise_signature("123456 merchant") == "123456 merchant"
