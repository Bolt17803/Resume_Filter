import PyPDF2
from langchain_core.prompts import ChatPromptTemplate
from utils.prompts import system_skill_exp_extractor_prompt, query_prompt, jd_skill_exp_extractor_prompt
import zipfile
import os
from PyPDF2 import PdfReader
import io
import asyncio

def save_pdfs_from_zip(session_path, zip_file):
    session_path = os.path.join("../", session_path)
    os.makedirs(session_path, exist_ok=True)
    with zipfile.ZipFile(session_path, 'r') as zip_ref:
        for file_name in zip_ref.namelist():
            # Check if the file ends with .pdf (case-insensitive)
            if file_name.lower().endswith('.pdf'):
                # Extract only this file
                zip_ref.extract(file_name, session_path)
                print(f"Extracted: {file_name}")

def extract_text_from_pdf(pdf_bytes):
    pdf_stream = io.BytesIO(pdf_bytes)
    reader = PyPDF2.PdfReader(pdf_stream)
    text = ""
    try:
        for page in reader.pages:
            text += page.extract_text()
    except Exception as e:
        print(f"\033[91m Error extracting the text from PDF: {e} \033[0m")
    return text.strip()

async def get_skills_and_exp_score(model, skills_text, experience_text, resume_text):
    sys_prompt = system_skill_exp_extractor_prompt()
    prompt_template = ChatPromptTemplate.from_messages(
        [("system", sys_prompt),("user","{resume_file}")]
    )

    prompt = prompt_template.invoke({"skills_file": skills_text, "experience_file": experience_text, "resume_file": resume_text})

    response = await model.ainvoke(prompt)
    if len(response.content)>8:
        response = await model.ainvoke(prompt)
    print(f"\033[92m Response from model: {response} \033[0m")
    ret = response.content.split(',')
    return ret[0], ret[1]

async def get_query_answer(model, resume_text, job_skill_file, job_experience_file, question):
    sys_prompt = query_prompt()

    prompt_template = ChatPromptTemplate.from_messages(
        [("system", sys_prompt), ("user", "{question}")]
    )

    prompt = prompt_template.invoke({"resume_file": resume_text, "job_skill_file": job_skill_file, "job_experience_file": job_experience_file, "question": question})

    response = await model.ainvoke(prompt)

    return response.content

async def get_jd_skill_exp(model, job_description_text):
    sys_prompt = jd_skill_exp_extractor_prompt()

    prompt_template = ChatPromptTemplate.from_messages(
        [("system", sys_prompt), ("user", "{job_description_text}")]
    )

    prompt = prompt_template.invoke({"job_description_text": job_description_text})

    response = await model.ainvoke(prompt)

    return response.content