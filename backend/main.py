# Add this endpoint at the end of your FastAPI app

from fastapi import Request
from fastapi.responses import JSONResponse
import concurrent.futures
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
import logging 
from utils.processing import extract_text_from_pdf, get_skills_and_exp_score, save_pdfs_from_zip, get_query_answer
from langchain.chat_models import init_chat_model
import time
import io
import zipfile
import asyncio
import aiofiles
import json
from whoosh.index import create_in, open_dir, exists_in
from whoosh.fields import Schema, TEXT, ID
from whoosh.qparser import QueryParser
from whoosh.query import *

#------------------------LOGGING------------------------
logger = logging.getLogger("fastapi_app")
logger.setLevel(logging.INFO)
YELLOW = "\033[93m"
RESET = "\033[0m"

class ColorFormatter(logging.Formatter):
    def format(self, record):
        log_message = super().format(record)
        if record.levelno == logging.INFO:
            return f"{YELLOW}{log_message}{RESET}"
        return log_message
handler = logging.StreamHandler()
formatter = ColorFormatter("%(asctime)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

#-----------------------------INITIALIZATION OF FASTAPI BACKEND-------------------------

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

logger.info("App started successfully")

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

#--------------------------------------------LOAD LLM ENV VARIABLES--------------------------------------------------
os.environ['LANGSMITH_TRACING'] = "true"
os.environ['LANGSMITH_API_KEY'] = "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"
os.environ['LANGSMITH_PROJECT'] = "default"

os.environ['GOOGLE_API_KEY'] = "AIzaSyAK98AyVqJ61lEQJSVxFHvjXWKeCdzB2mc"
model = init_chat_model("gemini-2.5-flash", model_provider="google_genai")

#---------------------------------------------END POINTS-----------------------------------------------------------------------
async def process_pdf(pdf, pdf_path, skills_text, experience_text):
    pdf_txt_path = os.path.join(pdf_path, pdf)
    async with aiofiles.open(pdf_txt_path, "r", encoding="utf-8") as f:
        text = await f.read()
    skill_score, exp_score = await get_skills_and_exp_score(model, skills_text, experience_text, text)
    return skill_score, exp_score

@app.post("/upload/")  # Endpoint for file upload with session and text
async def upload_file(
    file: UploadFile = File(...),
    skills_input: str = Form(...),
    experience_input: str = Form(...),
    session_id: str = Form(...)
):
    if not file.filename.endswith((".zip", ".pdf")):
        return {"error": "Only ZIP or PDF files allowed"}
    start_time = time.time()
    # Create a session-specific folder
    session_folder = os.path.join(UPLOAD_FOLDER, session_id)
    os.makedirs(session_folder, exist_ok=True)

    # Save the skills and experience input as text files in the session folder
    skills_path = os.path.join(session_folder, "skills.txt")
    with open(skills_path, "w", encoding="utf-8") as f:
        f.write(skills_input)
    experience_path = os.path.join(session_folder, "experience.txt")
    with open(experience_path, "w", encoding="utf-8") as f:
        f.write(experience_input)

    pdf_path = os.path.join(session_folder, "PDFS")
    os.makedirs(pdf_path, exist_ok=True)
    # extract the text from uploaded file
    if file.filename.endswith((".pdf")):
        upload="pdf"
        pdf_bytes = await file.read()
        try:  # Extract text from PDF
            text = extract_text_from_pdf(pdf_bytes)
            txt_filename = os.path.splitext(file.filename)[0] + ".txt"
            txt_file_path = os.path.join(pdf_path, txt_filename)
            with open(txt_file_path, "w", encoding="utf-8") as txt_file:
                txt_file.write(text)
            logger.info(f"Extracted text from {file.filename} to {txt_filename} in session {session_id}")
        except Exception as e:
            logger.error(f"Error processing {file.filename} in session {session_id}: {str(e)}")
            return {"error": str(e)}
    else:
        upload = "zip"
        file_names=[]
        try:
            # Read ZIP file into memory
            zip_bytes = await file.read()
            zip_stream = io.BytesIO(zip_bytes)

            with zipfile.ZipFile(zip_stream, 'r') as zip_ref:
                for pdf_name in zip_ref.namelist():
                    if pdf_name.lower().endswith(".pdf"):
                        
                        with zip_ref.open(pdf_name) as pdf_file:
                            pdf_bytes = pdf_file.read()

                        # Extract text directly from PDF bytes
                        text = extract_text_from_pdf(pdf_bytes)

                        # Save extracted text as .txt in session folder
                        txt_filename = os.path.splitext(os.path.basename(pdf_name))[0] + ".txt"
                        file_names.append(txt_filename)
                        txt_file_path = os.path.join(pdf_path, txt_filename)
                        with open(txt_file_path, "w", encoding="utf-8") as txt_file:
                            txt_file.write(text)

                        logger.info(f"Extracted text from {pdf_name} to {txt_filename} in session {session_id}")

        except Exception as e:
            logger.error(f"Error processing ZIP {file.filename} in session {session_id}: {str(e)}")
            return {"error": str(e)}
        print(file_names)

    with open(skills_path, "r", encoding="utf-8") as f:
        skills_text = f.read()
    with open(experience_path, "r", encoding="utf-8") as f:
        experience_text = f.read()

    if upload == "pdf":
        with open(txt_file_path, "r", encoding="utf-8") as f:
            text = f.read()
        skill_match_score, exp_match_score = await get_skills_and_exp_score(model, skills_text, experience_text, text)
    else:
        tasks = [process_pdf(pdf, pdf_path, skills_text, experience_text) for pdf in file_names]
        results = await asyncio.gather(*tasks)
        skill_match_score, exp_match_score = zip(*results)
    
    end_time = time.time()

    # Store the result in a results.json file inside a results directory under the session
    
    # Add filenames if multiple resumes (zip upload)
    if upload == "zip":
        result_data = {
            "skill_match_score": skill_match_score,
            "exp_match_score": exp_match_score,
            "session_id": session_id,
            "message": "Resume Scanned Successfully!",
            "processing_time": end_time - start_time
        }
        original_filenames = [os.path.splitext(f)[0] + ".txt" for f in file_names]
        result_data["filenames"] = original_filenames
    else:
        result_data = {
            "skill_match_score": [skill_match_score],
            "exp_match_score": [exp_match_score],
            "session_id": session_id,
            "message": "Resume Scanned Successfully!",
            "processing_time": end_time - start_time
        }
        result_data["filenames"] = [txt_filename]
    results_dir = os.path.join(session_folder, "results")
    os.makedirs(results_dir, exist_ok=True)
    results_path = os.path.join(results_dir, "results.json")
    import json
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(result_data, f, indent=2)

    return result_data

@app.get("/session_result/{session_id}")
async def get_session_result(session_id: str):
    session_folder = os.path.join(UPLOAD_FOLDER, session_id)
    results_path = os.path.join(session_folder, "results", "results.json")
    if not os.path.exists(results_path):
        return JSONResponse(status_code=404, content={"error": "Result not found for this session."})
    import json
    with open(results_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data

@app.post("/search/")
async def create_session(
    query_exp: str = Form(...),
    session_id: str = Form(...),
    score: int = Form(...),
):
    session_folder = os.path.join(UPLOAD_FOLDER, session_id)
    os.makedirs(session_folder, exist_ok=True)

    results_folder = os.path.join(session_folder, "results", "results.json")

    with open(results_folder, "r") as f:
        results = json.load(f)

    skill_scores = list(map(float, results["skill_match_score"]))
    exp_scores = list(map(float, results["exp_match_score"]))
    filenames = results["filenames"]
    matching_indices = [
            i for i, (skill, exp) in enumerate(zip(skill_scores, exp_scores))
            if (0.7 * skill + 0.3 * exp) > score
        ]

    filtered_filenames = [filenames[i] for i in matching_indices]
    print(filtered_filenames)
    schema = Schema(
        id = ID(stored=True, unique=True),
        filename=TEXT(stored=True),
        content=TEXT(stored=True)
    )

    index_dir = os.path.join(session_folder, "indexes")
    os.makedirs(index_dir, exist_ok=True)
    index_path = os.path.join(index_dir, f"score_{score}")

    pdf_path = os.path.join(session_folder, "PDFS")
    if os.path.exists(index_path):
        ix = open_dir(index_path)

    else:
        os.makedirs(index_path, exist_ok=True)

        ix = create_in(index_path, schema)
        writer = ix.writer()
        for file_name in filtered_filenames:
            print("reading:", file_name)
            async with aiofiles.open(os.path.join(pdf_path, file_name), "r", encoding="utf-8") as f:
                content = await f.read()
                writer.add_document(
                    id=file_name,
                    filename=file_name,
                    content=content
                )
        writer.commit()
    with ix.searcher() as searcher:
        # Parse a query for the 'content' field
        parser = QueryParser("content", ix.schema)
        
        # Example 1: Simple AND query (implicit)
        query = parser.parse(query_exp)
        results = searcher.search(query, limit= None)
        hits = len(results)
        hit_filenames = []
        for hit in results:
            hit_filenames.append(hit['filename'])
    return {"hits": hits, "filenames": hit_filenames}


@app.post("/query")
async def query_resume(request: Request):
    data = await request.json()
    file_name = data.get("file_name")
    session_id = data.get("sessionId")
    question = data.get("question")

    file_path = os.path.join(UPLOAD_FOLDER, session_id, "PDFS", file_name)
    
    with open(file_path, "r", encoding="utf-8") as f:
        resume_text = f.read()
    
    answer = await get_query_answer(model, resume_text, question)

    return {"answer": answer}