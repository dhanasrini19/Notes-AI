// pages/index.js
import { useState, useEffect } from "react";
import axios from "axios";

const API_BASE = "http://127.0.0.1:8000";

export default function Home() {
  const [note, setNote] = useState("");
  const [notes, setNotes] = useState([]);
  const [summary, setSummary] = useState("");

  // Fetch notes from backend
  const fetchNotes = async () => {
    try {
      const res = await axios.get(`${API_BASE}/notes`);
      setNotes(res.data);
    } catch (err) {
      alert("Failed to load notes");
    }
  };

  useEffect(() => { fetchNotes() }, []);

  // Add a note
  const addNote = async () => {
    if (!note.trim()) return;
    try {
      await axios.post(`${API_BASE}/notes`, { content: note });
      setNote("");
      fetchNotes();
    } catch { alert("Failed to add note"); }
  };

  // Delete a note
  const deleteNote = async (id) => {
    try {
      await axios.delete(`${API_BASE}/notes/${id}`);
      setNotes(notes.filter(n => n.id !== id));
    } catch { alert("Delete failed"); }
  };

  // Get summary
  const getSummary = async () => {
    try {
      const res = await axios.get(`${API_BASE}/summary`);
      setSummary(res.data.summary);
    } catch { alert("Failed to get summary"); }
  };

  return (
    <div className="container">
      <h1>📝 Notes AI</h1>
      <textarea
        rows={4}
        value={note}
        onChange={e => setNote(e.target.value)}
        placeholder="Write a note..."
      />
      <div>
        <button onClick={addNote}>Save</button>
        <button onClick={getSummary}>Get Summary</button>
      </div>

      <h2>Saved Notes</h2>
      <ul className="notes">
        {notes.map(n => (
          <li key={n.id}>
            <span>{n.content}</span>
            <button onClick={() => deleteNote(n.id)}>Delete</button>
          </li>
        ))}
      </ul>

      {summary && <div><h3>Summary</h3><p>{summary}</p></div>}
    </div>
  );
}
