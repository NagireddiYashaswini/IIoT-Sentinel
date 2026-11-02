"""
Convert PPTX presentation to PDF using native PowerPoint COM automation.
"""

import os
import sys
import win32com.client

PPTX_PATH = os.path.abspath("IIoT_Sentinel_4.0_Presentation.pptx")
PDF_PATH = os.path.abspath("IIoT_Sentinel_4.0_Presentation.pdf")

def convert_pptx_to_pdf(input_file, output_file):
    print(f"Converting PPTX to PDF...")
    print(f"Input: {input_file}")
    print(f"Output: {output_file}")
    
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Input file not found: {input_file}")

    powerpoint = win32com.client.Dispatch("PowerPoint.Application")
    # ppSaveAsPDF = 32
    deck = None
    try:
        deck = powerpoint.Presentations.Open(input_file, WithWindow=False)
        deck.SaveAs(output_file, 32)
        print(f"Conversion successful! PDF created: {output_file} ({os.path.getsize(output_file):,} bytes)")
    finally:
        if deck:
            deck.Close()
        powerpoint.Quit()

if __name__ == "__main__":
    convert_pptx_to_pdf(PPTX_PATH, PDF_PATH)

