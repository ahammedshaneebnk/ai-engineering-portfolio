import asyncio
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

    return extracted_data


async def main():
    # concurrent tasks list
    tasks = [extract_from_invoice(invoice) for invoice in invoices]

    # execute tasks simultaneously
    results = await asyncio.gather(*tasks) # gather expects each arg separately, * will satisfy it by unpacking the list

    for res in results:
        print(f"Vendor: {res.vendor_name}\tInvoice Date: {res.invoice_date}")


if __name__ == "__main__":
    print("--- Output ---")
    asyncio.run(main())