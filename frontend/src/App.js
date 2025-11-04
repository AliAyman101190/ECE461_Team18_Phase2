import { BrowserRouter as Router, Routes, Route, Link } from "react-router-dom";
import Home from "./pages/Home";
import Ingest from "./pages/Ingest";
import { useState } from "react";
import "./App.css";


function App() {
  const [modelUrl, setModelUrl] = useState("");
  const [status, setStatus] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!modelUrl.trim()) {
      setStatus("⚠️ Please enter a Hugging Face model link.");
      return;
    }

    // Placeholder for actual API call
    try {
      // Later you'll replace this with a fetch() to your backend
      console.log("Requesting ingestion for:", modelUrl);
      await new Promise((resolve) => setTimeout(resolve, 500));
      setStatus("✅ Model ingestion request submitted!");
      setModelUrl("");
    } catch (err) {
      setStatus("❌ Failed to send ingestion request.");
    }
  };

  return (
    <Router>
      <div className="app">
        <header className="navbar">
          <h1>LLM Grader Portal</h1>
          <nav>
            <Link to="/" className="nav-link">Home</Link>
            <Link to="/ingest" className="nav-link">Ingest Model</Link>
          </nav>
        </header>

        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/ingest" element={<Ingest />} />
        </Routes>

        <footer className="footer">
          <p>© 2025 Team 18 – Purdue ECE 461 Phase 2</p>
        </footer>
      </div>
    </Router>
  );

}

export default App;
