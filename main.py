from fastapi import FastAPI
from pydantic import BaseModel
from agent import run_agent
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(title= "Crypto Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins = ["*"],
    allow_credentials = True,
    allow_methods = ["*"],
    allow_headers = ["*"],
)
class Question(BaseModel):
    question:str

@app.post("/ask")
def ask_agent(body:Question):
    answer = run_agent(body.question)
    return {"answer":answer}

@app.get("/")
def home():
    return {"message":"Crpto Agent is running"}



