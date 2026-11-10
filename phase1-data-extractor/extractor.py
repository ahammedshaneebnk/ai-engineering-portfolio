import asyncio
import sqlite3
import logging
from dotenv import load_dotenv
from litellm import acompletion
from pydantic import BaseModel, Field


logging.basicConfig(
    level=logging.INFO,
    filename="extractor.log",
    filemode="w"
)

load_dotenv()


# output data structure using pydantic
class ExtractedInvoice(BaseModel):
    vendor_name: str = Field(description="The name of the company issuing the invoice")
    invoice_date: str = Field(description="The date the invoice was issued")
    total_amount: float = Field(description="The total numerical amount due")
    currency: str = Field(description="The currency code, e.g., AED, USD, INR, EUR")
    line_items: list[str] = Field(description="List of products or services purchased")


# multiple invoices
invoices = [
    "Invoice from Emirates Office Supplies. Dated: 12-Oct-2026. Items: 5x Chairs. Total: 4,500 AED.",
    "Invoice from Dubai Logistics FZCO. Dated: 14-Oct-2026. Items: Freight shipping. Total: 12,300 USD.",
    "Invoice from Al Maya Groceries. Dated: 15-Oct-2026. Items: Office pantry supplies. Total: 850 AED."
]

MODEL = "claude-haiku-5-5"

INVOICE_DB = "invoices.db"
TABLE_NAME = "extracted_invoices"

def init_db():
    conn = sqlite3.connect(INVOICE_DB)
    cursor = conn.cursor()
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vendor_name TEXT,
            invoice_date TEXT,
            total_amount REAL,
            currency TEXT,
            line_items TEXT
        )
    """)
    conn.commit()
    conn.close()


def save_to_db(data: ExtractedInvoice):
    conn = sqlite3.connect(INVOICE_DB)
    cursor = conn.cursor()
    conn.execute(f"""
        INSERT INTO {TABLE_NAME} (vendor_name, invoice_date, total_amount, currency, line_items)
        VALUES (?, ?, ?, ?, ?)
    """, (
        data.vendor_name,
        data.invoice_date,
        data.total_amount,
        data.currency,
        ", ".join(data.line_items) # list into comma separated string for storing into db
    ))
    conn.commit()
    conn.close()

def verify_db():
    conn = sqlite3.connect(INVOICE_DB)
    cursor = conn.cursor()
    cursor.execute(f"""SELECT * FROM {TABLE_NAME}""")
    rows = cursor.fetchall()

    for row in rows:
        record_id, vendor_name, invoice_date, total_amount, currency, line_items = row
        print(f"Record ID: {record_id}")
        print(f"Vendor: {vendor_name}")
        print(f"Invoice Date: {invoice_date}")
        print(f"Total Amount: {total_amount}")
        print(f"Currency: {currency}")
        print(f"Line Items: {line_items}")
        print("--"*20)

    conn.close()


async def extract_from_invoice(invoice:str):
    # API call
    response = await acompletion(
        model=MODEL,
        messages=[
            {"role":"user",
            "content":f"Extract structured data from this invoice:-\n{invoice}"}
        ],
        response_format=ExtractedInvoice
    )

    # response text into pydantic
    extracted_data = ExtractedInvoice.model_validate_json(response.choices[0].message.content)

    save_to_db(extracted_data)

    return extracted_data


async def main():
    init_db()

    # concurrent tasks list
    tasks = [extract_from_invoice(invoice) for invoice in invoices]

    # execute tasks simultaneously
    results = await asyncio.gather(*tasks) # gather expects each arg separately, * will satisfy it by unpacking the list

    verify_db()

if __name__ == "__main__":
    print("--- Output ---")
    asyncio.run(main())