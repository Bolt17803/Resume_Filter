# Add this endpoint at the end of your FastAPI app

from tokenize import Octnumber
from fastapi import Request
from fastapi.responses import JSONResponse
import concurrent.futures
from fastapi import FastAPI, File, UploadFile, Form, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
import logging 
from utils.processing import extract_text_from_pdf, get_skills_and_exp_score, save_pdfs_from_zip, get_query_answer, get_jd_skill_exp
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
from fastapi import BackgroundTasks
import time
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

# Clean up uploads folder on startup
def cleanup_uploads_folder():
    """Remove all files and directories in the uploads folder on startup"""
    try:
        if os.path.exists(UPLOAD_FOLDER):
            for item in os.listdir(UPLOAD_FOLDER):
                item_path = os.path.join(UPLOAD_FOLDER, item)
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                else:
                    os.remove(item_path)
            logger.info("Uploads folder cleaned up on startup")
    except Exception as e:
        logger.error(f"Error cleaning up uploads folder: {str(e)}")

# Clean up on startup
cleanup_uploads_folder()

#--------------------------------------------LOAD LLM ENV VARIABLES--------------------------------------------------
os.environ['LANGSMITH_TRACING'] = "true"
os.environ['LANGSMITH_API_KEY'] = "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"
os.environ['LANGSMITH_PROJECT'] = "default"

os.environ['GOOGLE_API_KEY'] = "AIzaSyAK98AyVqJ61lEQJSVxFHvjXWKeCdzB2mc"
model = init_chat_model("gemini-2.5-flash", model_provider="google_genai")

#---------------------------------------------FILE SYSTEM MONITORING--------------------------------------------------
observers = {}

async def start_folder_monitoring(session_id: str, background_tasks: BackgroundTasks):
    """
    Start a simple polling-based monitor for new files in the session's CANDIDATE PDFS folder.
    Runs as a background task in the FastAPI event loop.
    For each new PDF, process and update the results/results.json file in the session directory.
    """
    import json

    session_folder = os.path.join(UPLOAD_FOLDER, session_id)
    candidate_pdfs_path = os.path.join(session_folder, "CANDIDATE PDFS")
    pdf_text_path = os.path.join(session_folder, "PDF TEXT")
    skills_path = os.path.join(session_folder, "skills.txt")
    experience_path = os.path.join(session_folder, "experience.txt")
    results_dir = os.path.join(session_folder, "results")
    results_json_path = os.path.join(results_dir, "results.json")

    # Store the set of already seen files
    seen_files = set(os.listdir(candidate_pdfs_path))

    async def monitor():
        logger.info(f"Started polling monitor for {session_id}")
        while True:
            try:
                current_files = set(os.listdir(candidate_pdfs_path))
                new_files = current_files - seen_files
                if new_files:
                    for f in new_files:
                        filename = f
                        logger.info(f"New file detected in session {session_id}: {f}")
                        pdf_file_path = os.path.join(candidate_pdfs_path, filename)
                        # Read PDF bytes
                        async with aiofiles.open(pdf_file_path, "rb") as pdf_f:
                            pdf_bytes = await pdf_f.read()
                        # Extract text from PDF
                        extracted_text = extract_text_from_pdf(pdf_bytes)
                        # Save extracted text to PDF TEXT folder
                        os.makedirs(pdf_text_path, exist_ok=True)
                        text_filename = f"{os.path.splitext(filename)[0]}.txt"
                        text_file_path = os.path.join(pdf_text_path, text_filename)
                        async with aiofiles.open(text_file_path, "w", encoding="utf-8") as txt_f:
                            await txt_f.write(extracted_text)
                        # Read skills and experience
                        async with aiofiles.open(skills_path, "r", encoding="utf-8") as f_sk:
                            skills_text = await f_sk.read()
                        async with aiofiles.open(experience_path, "r", encoding="utf-8") as f_exp:
                            experience_text = await f_exp.read()
                        # Now process the saved text file
                        skill_score, exp_score = await process_pdf(text_filename, pdf_text_path, skills_text, experience_text)

                        # Update results/results.json
                        os.makedirs(results_dir, exist_ok=True)
                        # Load existing results or create new
                        if os.path.exists(results_json_path):
                            async with aiofiles.open(results_json_path, "r", encoding="utf-8") as res_f:
                                try:
                                    results_data = json.loads(await res_f.read())
                                except Exception:
                                    results_data = {}
                        else:
                            results_data = {}

                        # Ensure lists exist
                        if "skill_match_score" not in results_data or not isinstance(results_data.get("skill_match_score"), list):
                            results_data["skill_match_score"] = []
                        if "exp_match_score" not in results_data or not isinstance(results_data.get("exp_match_score"), list):
                            results_data["exp_match_score"] = []
                        if "filenames" not in results_data or not isinstance(results_data.get("filenames"), list):
                            results_data["filenames"] = []

                        # Append new scores and filename
                        results_data["skill_match_score"].append(str(skill_score))
                        results_data["exp_match_score"].append(str(exp_score))
                        results_data["filenames"].append(f"{filename[:-4]}.txt")
                        results_data["session_id"] = session_id
                        results_data["message"] = "Resume Scanned Successfully!"

                        # Write back to results.json
                        async with aiofiles.open(results_json_path, "w", encoding="utf-8") as res_f:
                            await res_f.write(json.dumps(results_data, indent=2))

                    seen_files.update(new_files)
                await asyncio.sleep(2)  # Poll every 2 seconds
            except Exception as e:
                logger.error(f"Error in folder monitoring for session {session_id}: {str(e)}")
                break

    # Schedule the monitor coroutine as a background task
    task = asyncio.create_task(monitor())
    observers[session_id] = task
    background_tasks.add_task(lambda: task)  # Ensure task is kept alive
    logger.info(f"Scheduled monitoring task for session {session_id}")    

#---------------------------------------------END POINTS-----------------------------------------------------------------------

async def process_pdf(pdf, pdf_path, skills_text, experience_text):
    pdf_txt_path = os.path.join(pdf_path, pdf)
    async with aiofiles.open(pdf_txt_path, "r", encoding="utf-8") as f:
        text = await f.read()
    skill_score, exp_score = await get_skills_and_exp_score(model, skills_text, experience_text, text)
    return skill_score, exp_score

@app.post("/upload/")
async def upload_file(
    file: UploadFile = File(...),
    skills_input: str = Form(...),
    experience_input: str = Form(...),
    session_id: str = Form(...),
    background_tasks: BackgroundTasks = None  # Add BackgroundTasks dependency
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

    # New folders for candidate PDFs and extracted text
    candidate_pdfs_path = os.path.join(session_folder, "CANDIDATE PDFS")
    pdf_text_path = os.path.join(session_folder, "PDF TEXT")
    os.makedirs(candidate_pdfs_path, exist_ok=True)
    os.makedirs(pdf_text_path, exist_ok=True)

    if file.filename.endswith(".pdf"):
        upload = "pdf"
        pdf_bytes = await file.read()
        try:
            # Save the uploaded PDF in CANDIDATE PDFS
            pdf_save_path = os.path.join(candidate_pdfs_path, file.filename)
            with open(pdf_save_path, "wb") as pdf_file:
                pdf_file.write(pdf_bytes)

            # Extract text from PDF and save in PDF TEXT
            text = extract_text_from_pdf(pdf_bytes)
            txt_filename = os.path.splitext(file.filename)[0] + ".txt"
            txt_file_path = os.path.join(pdf_text_path, txt_filename)
            with open(txt_file_path, "w", encoding="utf-8") as txt_file:
                txt_file.write(text)
            logger.info(f"Saved PDF {file.filename} and extracted text to {txt_filename} in session {session_id}")
        except Exception as e:
            logger.error(f"Error processing {file.filename} in session {session_id}: {str(e)}")
            return {"error": str(e)}
    else:
        upload = "zip"
        file_names = []
        try:
            # Read ZIP file into memory
            zip_bytes = await file.read()
            zip_stream = io.BytesIO(zip_bytes)

            with zipfile.ZipFile(zip_stream, 'r') as zip_ref:
                for pdf_name in zip_ref.namelist():
                    if pdf_name.lower().endswith(".pdf"):
                        # Save the PDF file in CANDIDATE PDFS
                        with zip_ref.open(pdf_name) as pdf_file:
                            pdf_bytes = pdf_file.read()
                            pdf_save_path = os.path.join(candidate_pdfs_path, os.path.basename(pdf_name))
                            with open(pdf_save_path, "wb") as out_pdf:
                                out_pdf.write(pdf_bytes)

                        # Extract text directly from PDF bytes
                        text = extract_text_from_pdf(pdf_bytes)

                        # Save extracted text as .txt in PDF TEXT
                        txt_filename = os.path.splitext(os.path.basename(pdf_name))[0] + ".txt"
                        file_names.append(txt_filename)
                        txt_file_path = os.path.join(pdf_text_path, txt_filename)
                        with open(txt_file_path, "w", encoding="utf-8") as txt_file:
                            txt_file.write(text)

                        logger.info(f"Saved PDF {pdf_name} and extracted text to {txt_filename} in session {session_id}")

        except Exception as e:
            logger.error(f"Error processing ZIP {file.filename} in session {session_id}: {str(e)}")
            return {"error": str(e)}

    with open(skills_path, "r", encoding="utf-8") as f:
        skills_text = f.read()
    with open(experience_path, "r", encoding="utf-8") as f:
        experience_text = f.read()

    if upload == "pdf":
        with open(txt_file_path, "r", encoding="utf-8") as f:
            text = f.read()
        skill_match_score, exp_match_score = await get_skills_and_exp_score(model, skills_text, experience_text, text)
    else:
        tasks = [process_pdf(pdf, pdf_text_path, skills_text, experience_text) for pdf in file_names]
        results = await asyncio.gather(*tasks)
        skill_match_score, exp_match_score = zip(*results)

    end_time = time.time()

    # Store the result in a results.json file inside a results directory under the session
    if upload == "zip":
        result_data = {
            "skill_match_score": list(skill_match_score),
            "exp_match_score": list(exp_match_score),
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
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(result_data, f, indent=2)

    # Start monitoring the CANDIDATE PDFS folder as a background task
    await start_folder_monitoring(session_id, background_tasks)

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
    score: int = Form(...)
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
        id=ID(stored=True, unique=True),
        filename=TEXT(stored=True),
        content=TEXT(stored=True)
    )

    index_dir = os.path.join(session_folder, "indexes")
    os.makedirs(index_dir, exist_ok=True)
    index_path = os.path.join(index_dir, f"score_{score}")

    pdf_path = os.path.join(session_folder, "PDF TEXT")  # Corrected to PDF TEXT
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
        parser = QueryParser("content", ix.schema)
        query = parser.parse(query_exp)
        results = searcher.search(query, limit=None)
        hits = len(results)
        hit_filenames = [hit['filename'] for hit in results]
    return {"hits": hits, "filenames": hit_filenames}

@app.post("/query")
async def query_resume(request: Request):
    data = await request.json()
    file_name = data.get("file_name")
    session_id = data.get("sessionId")
    question = data.get("question")

    file_path = os.path.join(UPLOAD_FOLDER, session_id, "PDF TEXT", file_name)
    
    with open(file_path, "r", encoding="utf-8") as f:
        resume_text = f.read()
    
    job_skill_file = os.path.join(UPLOAD_FOLDER, session_id, "skills.txt")  
    job_experience_file = os.path.join(UPLOAD_FOLDER, session_id, "experience.txt")
    answer = await get_query_answer(model, resume_text, job_skill_file, job_experience_file, question)

    return {"answer": answer}

@app.post("/upload_files/")
async def upload_files(
    file: UploadFile = File(...),
    job_description_file: UploadFile = File(None),
    session_id: str = Form(...),
    background_tasks: BackgroundTasks = None
):
    if not file.filename.endswith((".zip", ".pdf")):
        return {"error": "Only ZIP or PDF files allowed"}
    start_time = time.time()
    # Create a session-specific folder
    session_folder = os.path.join(UPLOAD_FOLDER, session_id)
    os.makedirs(session_folder, exist_ok=True)

    jd_pdf_bytes = await job_description_file.read()
    jd_text = extract_text_from_pdf(jd_pdf_bytes)
    jd_text_path = os.path.join(session_folder, "job_description.txt")
    with open(jd_text_path, "w", encoding="utf-8") as f:
        f.write(jd_text)
    
    # Extract skills and experience from job description
    jd_response = await get_jd_skill_exp(model, jd_text)
    logger.info(f"Raw LLM response: {jd_response}")
    
    try:
        # Try to parse the JSON response directly
        jd_json = json.loads(jd_response)
        skills_input = jd_json.get("skills", "No skills extracted")
        experience_input = jd_json.get("experience", "No experience extracted")
    except json.JSONDecodeError:
        # Try to extract JSON from the response if it's wrapped in other text
        try:
            import re
            # Look for JSON pattern in the response
            json_match = re.search(r'\{.*\}', jd_response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                jd_json = json.loads(json_str)
                skills_input = jd_json.get("skills", "No skills extracted")
                experience_input = jd_json.get("experience", "No experience extracted")
            else:
                raise ValueError("No JSON found in response")
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse JSON from LLM response: {e}")
            logger.error(f"LLM response was: {jd_response}")
            # Fallback: use the raw response or default values
            skills_input = "Failed to extract skills from job description"
            experience_input = "Failed to extract experience from job description"


    # Save the skills and experience input as text files in the session folder
    skills_path = os.path.join(session_folder, "skills.txt")
    with open(skills_path, "w", encoding="utf-8") as f:
        f.write(skills_input)
    experience_path = os.path.join(session_folder, "experience.txt")
    with open(experience_path, "w", encoding="utf-8") as f:
        f.write(experience_input)

    # New folders for candidate PDFs and extracted text
    candidate_pdfs_path = os.path.join(session_folder, "CANDIDATE PDFS")
    pdf_text_path = os.path.join(session_folder, "PDF TEXT")
    os.makedirs(candidate_pdfs_path, exist_ok=True)
    os.makedirs(pdf_text_path, exist_ok=True)

    if file.filename.endswith(".pdf"):
        upload = "pdf"
        pdf_bytes = await file.read()
        try:
            # Save the uploaded PDF in CANDIDATE PDFS
            pdf_save_path = os.path.join(candidate_pdfs_path, file.filename)
            with open(pdf_save_path, "wb") as pdf_file:
                pdf_file.write(pdf_bytes)

            # Extract text from PDF and save in PDF TEXT
            text = extract_text_from_pdf(pdf_bytes)
            txt_filename = os.path.splitext(file.filename)[0] + ".txt"
            txt_file_path = os.path.join(pdf_text_path, txt_filename)
            with open(txt_file_path, "w", encoding="utf-8") as txt_file:
                txt_file.write(text)
            logger.info(f"Saved PDF {file.filename} and extracted text to {txt_filename} in session {session_id}")
        except Exception as e:
            logger.error(f"Error processing {file.filename} in session {session_id}: {str(e)}")
            return {"error": str(e)}
    else:
        upload = "zip"
        file_names = []
        try:
            # Read ZIP file into memory
            zip_bytes = await file.read()
            zip_stream = io.BytesIO(zip_bytes)

            with zipfile.ZipFile(zip_stream, 'r') as zip_ref:
                for pdf_name in zip_ref.namelist():
                    if pdf_name.lower().endswith(".pdf"):
                        # Save the PDF file in CANDIDATE PDFS
                        with zip_ref.open(pdf_name) as pdf_file:
                            pdf_bytes = pdf_file.read()
                            pdf_save_path = os.path.join(candidate_pdfs_path, os.path.basename(pdf_name))
                            with open(pdf_save_path, "wb") as out_pdf:
                                out_pdf.write(pdf_bytes)

                        # Extract text directly from PDF bytes
                        text = extract_text_from_pdf(pdf_bytes)

                        # Save extracted text as .txt in PDF TEXT
                        txt_filename = os.path.splitext(os.path.basename(pdf_name))[0] + ".txt"
                        file_names.append(txt_filename)
                        txt_file_path = os.path.join(pdf_text_path, txt_filename)
                        with open(txt_file_path, "w", encoding="utf-8") as txt_file:
                            txt_file.write(text)

                        logger.info(f"Saved PDF {pdf_name} and extracted text to {txt_filename} in session {session_id}")

        except Exception as e:
            logger.error(f"Error processing ZIP {file.filename} in session {session_id}: {str(e)}")
            return {"error": str(e)}

    with open(skills_path, "r", encoding="utf-8") as f:
        skills_text = f.read()
    with open(experience_path, "r", encoding="utf-8") as f:
        experience_text = f.read()

    if upload == "pdf":
        with open(txt_file_path, "r", encoding="utf-8") as f:
            text = f.read()
        skill_match_score, exp_match_score = await get_skills_and_exp_score(model, skills_text, experience_text, text)
    else:
        tasks = [process_pdf(pdf, pdf_text_path, skills_text, experience_text) for pdf in file_names]
        results = await asyncio.gather(*tasks)
        skill_match_score, exp_match_score = zip(*results)

    end_time = time.time()

    # Store the result in a results.json file inside a results directory under the session
    if upload == "zip":
        result_data = {
            "skill_match_score": list(skill_match_score),
            "exp_match_score": list(exp_match_score),
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
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(result_data, f, indent=2)

    # Start monitoring the CANDIDATE PDFS folder as a background task
    await start_folder_monitoring(session_id, background_tasks)

    return result_data

@app.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """Delete a session and all its associated files"""
    try:
        session_folder = os.path.join(UPLOAD_FOLDER, session_id)
        
        if not os.path.exists(session_folder):
            return JSONResponse(status_code=404, content={"error": "Session not found"})
        
        # Stop monitoring for this session
        if session_id in observers:
            observers[session_id].stop()
            observers[session_id].join()
            del observers[session_id]
            logger.info(f"Stopped monitoring for session {session_id}")
        
        # Remove the entire session folder and all its contents
        shutil.rmtree(session_folder)
        logger.info(f"Session {session_id} and all its files deleted successfully")
        
        return {"message": f"Session {session_id} deleted successfully"}
    
    except Exception as e:
        logger.error(f"Error deleting session {session_id}: {str(e)}")
        return JSONResponse(status_code=500, content={"error": f"Failed to delete session: {str(e)}"})