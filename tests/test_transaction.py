from bankcleanr.transaction import Transaction, mask_transaction, mask_account_and_sort_codes


def test_mask_account_and_sort_codes():
    text = "Transfer to 12-34-56 12345678"
    assert mask_account_and_sort_codes(text) == "Transfer to ****3456 ****5678"


def test_mask_transaction_does_not_modify_original():
    tx = Transaction(date="2024-01-01", description="Pay 12-34-56 12345678", amount="-1.00")
    masked = mask_transaction(tx)
    assert masked.description == "Pay ****3456 ****5678"
    # original untouched
    assert tx.description == "Pay 12-34-56 12345678"
