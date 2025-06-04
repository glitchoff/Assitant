import fitz  # PyMuPDF library 
from fastapi import UploadFile 
from fastapi.exceptions import HTTPException 

# Function to convert PDF to readable text
async def pdfParser(file: UploadFile):
    try:
        content = await file.read() # Read the file content
        
        # Check if we actually got any content
        if not content:
            raise HTTPException(status_code=400, detail="The file appears to be empty")
        # Try to open the PDF
        try:
            doc = fitz.open(stream=content, filetype="pdf")
            
            # Check if the PDF has any pages
            if doc.page_count == 0:
                raise HTTPException(status_code=400, detail="The PDF file has no pages")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Could not open PDF file: {str(e)}")

        # Create a string to store our final text
        finalText = ""
        
        # Process each page in the PDF
        for page_number, page in enumerate(doc, start=1):
            try:
                # Extract text from the page
                page_text = page.get_text("text")
                
                # Skip empty pages
                if not page_text.strip():
                    continue
                    
                # Add a header for each page and the text
                finalText += f"\n=== Page {page_number} ===\n\n{page_text}\n\n"
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Could not read page {page_number}: {str(e)}")

        # If we didn't get any text at all
        if not finalText.strip():
            raise HTTPException(status_code=400, detail="Could not extract any text from the PDF")

        # Return the processed text
        return {"format": "pdf", "content": finalText.strip()}

    except HTTPException as e:
        # Re-raise the HTTPException with its original message
        raise
    except Exception as e:
        # For any other unexpected error, provide a clear message
        raise HTTPException(status_code=400, detail=f"An unexpected error occurred: {str(e)}")
