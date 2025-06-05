import fitz # PyMuPDF library 
from fastapi import UploadFile 
from fastapi.exceptions import HTTPException 

async def pdfParser(file: UploadFile):
    try:
        # Reset file pointer to beginning
        await file.seek(0)
        
        # Read the file content once
        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="The file appears to be empty")
            
        try:
            # Create a bytes stream for PyMuPDF
            doc = fitz.open(stream=content, filetype="pdf")
            if doc.page_count == 0:
                raise HTTPException(status_code=400, detail="The PDF file has no pages")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Could not open PDF file: {str(e)}")
        finalText = ""
        for page_number, page in enumerate(doc, start=1):
            try:
                page_text = page.get_text("text")
                if not page_text.strip():
                    continue
                finalText += f"\n=== Page {page_number} ===\n\n{page_text}\n\n"
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Could not read page {page_number}: {str(e)}")
        if not finalText.strip():
            raise HTTPException(status_code=400, detail="Could not extract any text from the PDF")
        return {"format": "pdf", "content": finalText.strip()}
    except HTTPException as e:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"An unexpected error occurred: {str(e)}")
