from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import uuid
import os
import re
import openai  # optional if you want OpenAI summaries

# ----- Models -----
class NoteIn(BaseModel):
    content: str

class NoteOut(BaseModel):
    id: str
    content: str

# ----- App -----
app = FastAPI(title="Notes API")

# Allow frontend dev origin
origins = ["http://localhost:3000", "http://127.0.0.1:3000", "http://127.0.0.1:3002", "http://localhost:3002"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory store
notes: List[NoteOut] = []

# ----- Helpers -----
def simple_summarizer(text: str, max_sentences: int = 2) -> str:
    if not text.strip():
        return "No notes to summarize."
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    words = re.findall(r'\w+', text.lower())
    stopwords = set(["the","is","in","and","to","a","of","for","on","it","this","that","with","as","are","was","be","by","an","or"])
    freq = {}
    for w in words:
        if w in stopwords: continue
        freq[w] = freq.get(w,0)+1
    if not freq: return "Summary not available."
    sent_scores = []
    for s in sentences:
        s_words = re.findall(r'\w+', s.lower())
        score = sum(freq.get(w,0) for w in s_words)
        if len(s_words) > 0: score = score / len(s_words)
        sent_scores.append((score, s))
    sent_scores.sort(reverse=True,key=lambda x:x[0])
    top = [s for (_,s) in sent_scores[:max_sentences]]
    return " ".join(top).strip()

def openai_summarizer(text: str, max_tokens: int = 200) -> str:
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("OPENAI_API_KEY not set")
    openai.api_key = key
    prompt = f"Summarize the following notes in 2-3 sentences:\n\n{text}\n\nSummary:"
    resp = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role":"user","content":prompt}],
        max_tokens=max_tokens,
        temperature=0.3
    )
    return resp.choices[0].message["content"].strip()

# ----- Endpoints -----
@app.post("/notes", response_model=NoteOut)
def add_note(note_in: NoteIn):
    new_id = str(uuid.uuid4())
    note = NoteOut(id=new_id, content=note_in.content)
    notes.append(note)
    return note

@app.get("/notes", response_model=List[NoteOut])
def get_notes(page: int=1, limit: int=100):
    start = (page-1)*limit
    end = start+limit
    return notes[start:end]

@app.delete("/notes/{note_id}")
def delete_note(note_id: str):
    global notes
    for n in notes:
        if n.id == note_id:
            notes = [x for x in notes if x.id != note_id]
            return {"message": "deleted"}
    raise HTTPException(status_code=404, detail="Note not found")

@app.get("/summary")
def get_summary(use_openai: bool=False):
    if not notes:
        return {"summary": "No notes available."}
    combined = "\n".join(n.content for n in notes)
    if use_openai:
        try:
            return {"summary": openai_summarizer(combined)}
        except:
            return {"summary": simple_summarizer(combined) + " (OpenAI failed)"}
    return {"summary": simple_summarizer(combined)}
