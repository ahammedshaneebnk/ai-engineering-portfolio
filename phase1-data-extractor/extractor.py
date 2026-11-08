import logging
from dotenv import load_dotenv
from litellm import completion
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


# messy input text
messy_text = """
    Invoice from Emirates Office Supplies LLC.
    Dated: 11-Nov-2026. 
    Items provided: 5x Ergonomic Chairs, 2x Standing Desks.
    Total balance to pay: 4,500.50 AED.
"""

print(f"--- Messy Input Text ---{messy_text}")

MODEL = "claude-haiku-5-5"

# API call
response = completion(
    model=MODEL,
    messages=[
        {"role":"user",
         "content":f"Extract structured data from this invoice:-\n{messy_text}"}
    ],
    response_format=ExtractedInvoice
)

# response text into pydantic
extracted_data = ExtractedInvoice.model_validate_json(response.choices[0].message.content)

print(f"--- Output ---\n{extracted_data}")

# example usage with output -> extracted_data.vendor, extracted_data.total_amount, etc.