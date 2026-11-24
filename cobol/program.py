#!/usr/bin/env python3
"""
Re-implementation of the COBOL BOOKFORUM program in Python.
Processes a book transaction from INPUT.DAT, updating ACCOUNTS.DAT, BOOKS.DAT, and TRANSACTIONS.DAT
if validation succeeds.
"""

import os
from pathlib import Path

def main():
    script_dir = Path(__file__).resolve().parent
    input_path = script_dir / "src" / "INPUT.DAT"
    data_dir = script_dir / "data"
    accounts_path = data_dir / "ACCOUNTS.DAT"
    books_path = data_dir / "BOOKS.DAT"
    transactions_path = data_dir / "TRANSACTIONS.DAT"

    # Record sizes
    ACCOUNT_SIZE = 34  # 4 + 20 + 10
    BOOK_SIZE = 28     # 4 + 20 + 4
    TRANS_SIZE = 22    # 4 + 10 + 4 + 4
    INPUT_SIZE = 22    # 4 + 4 + 4 + 10

    # Read input
    with open(input_path, "rb") as f:
        input_data = f.read()
    if not input_data:
        print("Error: Input file is empty")
        return

    # Pad input to record size with spaces if short
    if len(input_data) < INPUT_SIZE:
        input_data = input_data + b" " * (INPUT_SIZE - len(input_data))
    input_rec = input_data[:INPUT_SIZE]

    buyer_id = input_rec[0:4].decode("ascii", errors="replace")
    seller_id = input_rec[4:8].decode("ascii", errors="replace")
    book_id = input_rec[8:12].decode("ascii", errors="replace")
    amount_str = input_rec[12:22].decode("ascii", errors="replace")

    # Parse amount: take integer value, treating non-digits as 0 contribution
    # Strip spaces and take int of digit sequence
    amount_digits = "".join(c for c in amount_str if c.isdigit())
    amount = int(amount_digits) if amount_digits else 0

    # Validate users and book
    buyer_found = False
    seller_found = False
    book_found = False
    valid_owner = False

    # Check accounts
    with open(accounts_path, "rb") as f:
        accounts_data = f.read()
    num_accounts = len(accounts_data) // ACCOUNT_SIZE
    for i in range(num_accounts):
        rec = accounts_data[i*ACCOUNT_SIZE:(i+1)*ACCOUNT_SIZE]
        acc_id = rec[0:4].decode("ascii", errors="replace")
        if acc_id == buyer_id:
            buyer_found = True
        if acc_id == seller_id:
            seller_found = True

    # Check books
    with open(books_path, "rb") as f:
        books_data = f.read()
    num_books = len(books_data) // BOOK_SIZE
    for i in range(num_books):
        rec = books_data[i*BOOK_SIZE:(i+1)*BOOK_SIZE]
        bk_id = rec[0:4].decode("ascii", errors="replace")
        bk_owner = rec[24:28].decode("ascii", errors="replace")
        if bk_id == book_id:
            book_found = True
            if bk_owner == seller_id:
                valid_owner = True

    print(" ")  # Matches the DISPLAY " " in COBOL

    if buyer_found and seller_found and book_found and valid_owner:
        # Process transaction
        # Update accounts
        new_accounts = bytearray(accounts_data)
        for i in range(num_accounts):
            offset = i * ACCOUNT_SIZE
            rec = new_accounts[offset:offset+ACCOUNT_SIZE]
            acc_id = rec[0:4].decode("ascii", errors="replace")
            bal_str = rec[24:34].decode("ascii", errors="replace")
            try:
                balance = int(bal_str)
            except ValueError:
                balance = 0
            if acc_id == buyer_id:
                balance -= amount
                if balance < 0:
                    balance = 0  # or allow negative? COBOL PIC 9 is unsigned, but SUBTRACT may wrap or error
                # Actually PIC 9(10) unsigned, subtract more than balance may cause size error or set to 0 depending
                new_bal = f"{balance:010d}"
                new_accounts[offset+24:offset+34] = new_bal.encode("ascii")
            if acc_id == seller_id:
                balance += amount
                new_bal = f"{balance:010d}"
                new_accounts[offset+24:offset+34] = new_bal.encode("ascii")
        with open(accounts_path, "wb") as f:
            f.write(new_accounts)

        # Update books
        new_books = bytearray(books_data)
        for i in range(num_books):
            offset = i * BOOK_SIZE
            rec = new_books[offset:offset+BOOK_SIZE]
            bk_id = rec[0:4].decode("ascii", errors="replace")
            if bk_id == book_id:
                new_books[offset+24:offset+28] = buyer_id.encode("ascii")
        with open(books_path, "wb") as f:
            f.write(new_books)

        # Append transaction
        # TRANS-BOOK + TRANS-AMOUNT (10 digits) + TRANS-SELLER + TRANS-BUYER
        amount_formatted = f"{amount:010d}"
        trans_rec = (
            book_id.encode("ascii") +
            amount_formatted.encode("ascii") +
            seller_id.encode("ascii") +
            buyer_id.encode("ascii")
        )
        with open(transactions_path, "ab") as f:
            f.write(trans_rec)

        print("Transaction completed successfully")
    else:
        print("Transaction failed due to validation errors")

if __name__ == "__main__":
    main()
