import os
from fastapi import APIRouter, UploadFile, File
from ..ingest import UPLOADS_DIR, ingest_pdf_paths

router = APIRouter(prefix="/api/ingest", tags=["ingest"])

@router.post("", summary="Upload PDFs and ingest into the vector store")
async def ingest(files: list[UploadFile] = File(...)):
    saved_paths = []
    for f in files:
        dest = os.path.join(UPLOADS_DIR, f.filename)
        with open(dest, "wb") as out:
            out.write(await f.read())
        saved_paths.append(dest)

    added = ingest_pdf_paths(saved_paths)
    return {"added_documents": added, "files": [os.path.basename(p) for p in saved_paths]}
