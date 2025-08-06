from bankcleanr.pii import mask_pii


def test_mask_sort_code():
    assert mask_pii("sort code 12-34-56") == "sort code XX-XX-XX"


def test_mask_iban():
    masked = mask_pii("IBAN GB29NWBK60161331926819")
    assert masked == "IBAN GB29XXXXXXXXXXXXXX6819"


def test_mask_pan():
    masked = mask_pii("card 1234567890123456")
    assert masked == "card XXXXXXXXXXXX3456"


def test_mask_name_exact():
    masked = mask_pii("Paid to John Doe", ["John Doe"])
    assert masked == "Paid to XX MASKED NAME XX"


def test_mask_name_fuzzy():
    masked = mask_pii("Paid to Jhon Doe", ["John Doe"])
    assert masked == "Paid to XX MASKED NAME XX"
