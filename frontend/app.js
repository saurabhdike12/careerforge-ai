// =====================================================================
// CareerForge AI — Main React Application
// IBM Granite-powered Interview Trainer
// =====================================================================

const { useState, useEffect, useRef, useCallback } = React;
const API_BASE = "http://localhost:8000";

// ─── API Client ───────────────────────────────────────────────────────────────

const api = {
  async startSession(profile) {
    const r = await fetch(`${API_BASE}/api/v1/session/start`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(profile),
    });
    if (!r.ok) throw new Error((await r.json()).detail || "Failed to start session");
    return r.json();
  },

  async submitAnswer(sessionId, payload) {
    const r = await fetch(`${API_BASE}/api/v1/session/${sessionId}/answer`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, ...payload }),
    });
    if (!r.ok) throw new Error((await r.json()).detail || "Failed to submit answer");
    return r.json();
  },

  async getProgress(sessionId) {
    const r = await fetch(`${API_BASE}/api/v1/session/${sessionId}/progress`);
    return r.json();
  },

  async getSummary(sessionId) {
    const r = await fetch(`${API_BASE}/api/v1/session/${sessionId}/summary`);
    return r.json();
  },

  async chat(sessionId, message) {
    const r = await fetch(`${API_BASE}/api/v1/session/${sessionId}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, message }),
    });
    return r.json();
  },

  async uploadResume(sessionId, file) {
    const form = new FormData();
    form.append("file", file);
    const r = await fetch(`${API_BASE}/api/v1/session/${sessionId}/upload-resume`, {
      method: "POST",
      body: form,
    });
    return r.json();
  },
};

// ─── Utilities ────────────────────────────────────────────────────────────────

const scoreColor = (s) => {
  if (s >= 8) return "high";
  if (s >= 6) return "mid";
  return "low";
};

const scoreEmoji = (s) => {
  if (s >= 8.5) return "🌟";
  if (s >= 7) return "✅";
  if (s >= 5.5) return "📈";
  return "🎯";
};

const badgeTypeClass = (type) => `badge-${type}`;
const badgeDiffClass = (diff) => `badge-${diff}`;

function useTimer() {
  const [seconds, setSeconds] = useState(0);
  const [running, setRunning] = useState(false);
  const ref = useRef(null);

  const start = () => {
    setSeconds(0);
    setRunning(true);
  };

  const stop = () => {
    setRunning(false);
    return seconds;
  };

  useEffect(() => {
    if (running) {
      ref.current = setInterval(() => setSeconds((s) => s + 1), 1000);
    } else {
      clearInterval(ref.current);
    }
    return () => clearInterval(ref.current);
  }, [running]);

  const fmt = `${String(Math.floor(seconds / 60)).padStart(2, "0")}:${String(seconds % 60).padStart(2, "0")}`;
  return { seconds, fmt, running, start, stop };
}

// ─── Sub-components ───────────────────────────────────────────────────────────

function Spinner({ dark = false }) {
  return <span className={`spinner ${dark ? "dark" : ""}`} />;
}

function LoadingOverlay({ message, subtext }) {
  return (
    <div className="loading-overlay">
      <div className="loading-card">
        <div className="loading-pulse">
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none">
            <circle cx="12" cy="12" r="10" stroke="#0f62fe" strokeWidth="2" />
            <path d="M8 12l3 3 5-5" stroke="#0f62fe" strokeWidth="2" strokeLinecap="round" />
          </svg>
        </div>
        <h3>{message}</h3>
        <p>{subtext}</p>
      </div>
    </div>
  );
}

function Alert({ type = "info", children }) {
  const icons = { info: "ℹ️", success: "✅", error: "❌", warning: "⚠️" };
  return (
    <div className={`alert alert-${type}`}>
      <span>{icons[type]}</span>
      <span>{children}</span>
    </div>
  );
}

function ScoreDisplay({ score }) {
  const dims = [
    { key: "relevance", label: "Relevance" },
    { key: "star_method", label: "STAR Method" },
    { key: "technical_depth", label: "Technical" },
    { key: "communication", label: "Communication" },
    { key: "originality", label: "Originality" },
  ];
  return (
    <div>
      <div className="overall-score">
        <div className="overall-score-value">{score.overall.toFixed(1)}</div>
        <div className="overall-score-label">Overall Score / 10</div>
      </div>
      <div className="score-grid">
        {dims.map(({ key, label }) => (
          <div key={key} className="score-item">
            <div className="score-item-label">{label}</div>
            <div className={`score-item-value ${scoreColor(score[key])}`}>
              {score[key].toFixed(1)}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function FeedbackPanel({ feedback, onNext, isLastQuestion }) {
  return (
    <div className="feedback-panel card">
      <div className="card-header">
        <div className="card-icon blue">📊</div>
        <h2>IBM Granite Feedback</h2>
      </div>
      <div className="card-body">
        <ScoreDisplay score={feedback.score} />

        <div className="feedback-section">
          <h4>✅ Strengths</h4>
          <ul className="feedback-list strengths">
            {feedback.strengths.map((s, i) => <li key={i}>💪 {s}</li>)}
          </ul>
        </div>

        <div className="feedback-section">
          <h4>📈 Areas to Improve</h4>
          <ul className="feedback-list improvements">
            {feedback.improvements.map((s, i) => <li key={i}>🔧 {s}</li>)}
          </ul>
        </div>

        <div className="feedback-section">
          <h4>💡 Model Answer Hint</h4>
          <div className="alert alert-info" style={{ marginBottom: 0 }}>
            {feedback.model_answer_hint}
          </div>
        </div>

        {feedback.follow_up_question && (
          <div className="feedback-section">
            <h4>🔍 Follow-up Question</h4>
            <div className="alert alert-warning" style={{ marginBottom: 0, fontStyle: "italic" }}>
              "{feedback.follow_up_question}"
            </div>
          </div>
        )}

        <div className="feedback-section">
          <h4>🏷️ Keywords</h4>
          <div className="keyword-pills">
            {feedback.keywords_used.map((k, i) => (
              <span key={i} className="keyword-pill used">✓ {k}</span>
            ))}
            {feedback.keywords_missed.map((k, i) => (
              <span key={i} className="keyword-pill missed">✗ {k}</span>
            ))}
          </div>
        </div>

        <div className="divider" />

        <button
          className={`btn ${isLastQuestion ? "btn-danger" : "btn-primary"} btn-full`}
          onClick={onNext}
        >
          {isLastQuestion ? "🏁 Finish & Get Full Report" : "Next Question →"}
        </button>
      </div>
    </div>
  );
}

// ─── Chat Coach Panel ─────────────────────────────────────────────────────────

function ChatCoach({ sessionId }) {
  const [messages, setMessages] = useState([
    {
      role: "ai",
      text: "Hi! I'm your IBM Granite interview coach. Ask me anything about interview prep, specific topics, or how to improve your answers. 🎯",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);

  const sendMessage = async () => {
    const msg = input.trim();
    if (!msg || loading) return;

    setMessages((m) => [...m, { role: "user", text: msg }]);
    setInput("");
    setLoading(true);

    try {
      const res = await api.chat(sessionId, msg);
      setMessages((m) => [...m, { role: "ai", text: res.reply }]);
    } catch {
      setMessages((m) => [
        ...m,
        { role: "ai", text: "Sorry, I'm having trouble connecting. Please check your API configuration." },
      ]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="card chat-panel" style={{ height: "100%", display: "flex", flexDirection: "column" }}>
      <div className="card-header" style={{ flexShrink: 0 }}>
        <div className="card-icon purple">🤖</div>
        <div>
          <h2>AI Coach</h2>
          <div style={{ fontSize: "0.72rem", color: "var(--text-muted)" }}>IBM Granite powered</div>
        </div>
      </div>
      <div className="chat-messages">
        {messages.map((m, i) => (
          <div key={i} className={`chat-message ${m.role}`}>
            {m.role === "ai" && <div className="ai-label">CareerForge AI</div>}
            {m.text}
          </div>
        ))}
        {loading && (
          <div className="chat-message ai">
            <div className="ai-label">CareerForge AI</div>
            <Spinner dark /> Thinking with IBM Granite...
          </div>
        )}
        <div ref={bottomRef} />
      </div>
      <div className="chat-input-area" style={{ flexShrink: 0 }}>
        <div className="chat-input-row">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about interview tips, STAR method, technical concepts..."
            onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(); } }}
            rows={1}
          />
          <button
            className="btn btn-primary"
            onClick={sendMessage}
            disabled={loading || !input.trim()}
          >
            {loading ? <Spinner /> : "Send"}
          </button>
        </div>
      </div>
    </div>
  );
}

// ─── Setup / Onboarding Screen ────────────────────────────────────────────────

const EXPERIENCE_OPTIONS = [
  { value: "fresher", label: "Fresher", years: "0 yrs" },
  { value: "junior", label: "Junior", years: "1–3 yrs" },
  { value: "mid", label: "Mid", years: "3–6 yrs" },
  { value: "senior", label: "Senior", years: "6–10 yrs" },
  { value: "principal", label: "Principal", years: "10+ yrs" },
];

const FOCUS_AREA_OPTIONS = [
  { value: "technical", label: "⚙️ Technical" },
  { value: "behavioral", label: "🧠 Behavioral" },
  { value: "situational", label: "🎭 Situational" },
  { value: "hr", label: "👥 HR / Culture" },
  { value: "case_study", label: "📊 Case Study" },
  { value: "culture_fit", label: "💼 Culture Fit" },
];

const POPULAR_ROLES = [
  "Software Engineer", "Data Scientist", "Product Manager",
  "DevOps Engineer", "Machine Learning Engineer", "UX Designer",
  "Backend Engineer", "Frontend Engineer", "Data Analyst",
];

function SetupScreen({ onStart }) {
  const [form, setForm] = useState({
    name: "",
    job_role: "",
    experience_level: "mid",
    years_of_experience: "",
    target_company: "",
    industry: "",
    difficulty: "medium",
    focus_areas: ["technical", "behavioral"],
    skills: [],
  });
  const [skillInput, setSkillInput] = useState("");
  const [resumeFile, setResumeFile] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const update = (key, val) => setForm((f) => ({ ...f, [key]: val }));

  const toggleFocus = (val) => {
    setForm((f) => ({
      ...f,
      focus_areas: f.focus_areas.includes(val)
        ? f.focus_areas.filter((x) => x !== val)
        : [...f.focus_areas, val],
    }));
  };

  const addSkill = () => {
    const s = skillInput.trim();
    if (s && !form.skills.includes(s)) {
      update("skills", [...form.skills, s]);
    }
    setSkillInput("");
  };

  const removeSkill = (s) => update("skills", form.skills.filter((x) => x !== s));

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    const f = e.dataTransfer.files[0];
    if (f) setResumeFile(f);
  };

  const handleStart = async (e) => {
    e.preventDefault();
    setError("");

    if (!form.name.trim() || !form.job_role.trim()) {
      setError("Name and Job Role are required.");
      return;
    }

    setLoading(true);

    try {
      const profile = {
        ...form,
        years_of_experience: form.years_of_experience ? parseFloat(form.years_of_experience) : null,
        resume_text: null,
      };
      onStart(profile, resumeFile);
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  };

  return (
    <div className="setup-screen">
      {loading && <LoadingOverlay message="Building your interview plan..." subtext="IBM Granite is crafting personalized questions for your profile" />}

      <div className="setup-hero">
        <div className="ibm-powered-badge">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="#0f62fe">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 14.5v-9l6 4.5-6 4.5z"/>
          </svg>
          Powered by IBM Granite · watsonx.ai · RAG
        </div>
        <h1>CareerForge AI</h1>
        <p>Your intelligent interview trainer. Get personalized questions, AI-powered feedback, and actionable coaching to ace any interview.</p>
        <div className="feature-pills">
          {["📄 Resume-Aware RAG", "🎯 Real-time Scoring", "🧠 STAR Method Analysis", "📊 Session Analytics", "🔒 Ethical AI"].map((f) => (
            <span key={f} className="feature-pill">{f}</span>
          ))}
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <div className="card-icon blue">👤</div>
          <h2>Set Up Your Interview Session</h2>
        </div>
        <div className="card-body">
          {error && <Alert type="error">{error}</Alert>}

          <form onSubmit={handleStart}>
            {/* Basic Info */}
            <div className="form-grid-2">
              <div className="form-group">
                <label className="form-label">Full Name <span className="required">*</span></label>
                <input
                  className="form-input"
                  placeholder="e.g. Alex Johnson"
                  value={form.name}
                  onChange={(e) => update("name", e.target.value)}
                  required
                />
              </div>
              <div className="form-group">
                <label className="form-label">Target Company (optional)</label>
                <input
                  className="form-input"
                  placeholder="e.g. Google, IBM, Infosys"
                  value={form.target_company}
                  onChange={(e) => update("target_company", e.target.value)}
                />
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">Job Role <span className="required">*</span></label>
              <input
                className="form-input"
                placeholder="e.g. Software Engineer, Data Scientist, Product Manager"
                value={form.job_role}
                onChange={(e) => update("job_role", e.target.value)}
                list="roles-list"
                required
              />
              <datalist id="roles-list">
                {POPULAR_ROLES.map((r) => <option key={r} value={r} />)}
              </datalist>
              <div className="form-hint">Or type any custom role</div>
            </div>

            {/* Experience Level */}
            <div className="form-group">
              <label className="form-label">Experience Level <span className="required">*</span></label>
              <div className="experience-selector">
                {EXPERIENCE_OPTIONS.map((opt) => (
                  <div
                    key={opt.value}
                    className={`exp-option ${form.experience_level === opt.value ? "selected" : ""}`}
                    onClick={() => update("experience_level", opt.value)}
                  >
                    <span className="exp-label">{opt.label}</span>
                    <span className="exp-years">{opt.years}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Focus Areas */}
            <div className="form-group">
              <label className="form-label">Interview Focus Areas</label>
              <div className="focus-area-grid">
                {FOCUS_AREA_OPTIONS.map((opt) => (
                  <div
                    key={opt.value}
                    className={`focus-area-option ${form.focus_areas.includes(opt.value) ? "selected" : ""}`}
                    onClick={() => toggleFocus(opt.value)}
                  >
                    <span>{opt.label}</span>
                    {form.focus_areas.includes(opt.value) && <span style={{ marginLeft: "auto" }}>✓</span>}
                  </div>
                ))}
              </div>
            </div>

            {/* Difficulty */}
            <div className="form-group">
              <label className="form-label">Difficulty Level</label>
              <select
                className="form-select"
                value={form.difficulty}
                onChange={(e) => update("difficulty", e.target.value)}
              >
                <option value="easy">Easy — Warm-up, foundational</option>
                <option value="medium">Medium — Standard interview (recommended)</option>
                <option value="hard">Hard — FAANG / senior-level</option>
              </select>
            </div>

            {/* Skills */}
            <div className="form-group">
              <label className="form-label">Key Skills (optional)</label>
              <div className="skill-input-row">
                <input
                  className="form-input"
                  placeholder="e.g. Python, System Design, Agile..."
                  value={skillInput}
                  onChange={(e) => setSkillInput(e.target.value)}
                  onKeyDown={(e) => { if (e.key === "Enter") { e.preventDefault(); addSkill(); } }}
                />
                <button type="button" className="btn btn-secondary btn-sm" onClick={addSkill}>Add</button>
              </div>
              {form.skills.length > 0 && (
                <div className="skills-tags mt-4">
                  {form.skills.map((s) => (
                    <span key={s} className="skill-tag">
                      {s}
                      <span className="remove-skill" onClick={() => removeSkill(s)}>×</span>
                    </span>
                  ))}
                </div>
              )}
              <div className="form-hint">Add skills for more targeted technical questions</div>
            </div>

            {/* Resume Upload */}
            <div className="form-group">
              <label className="form-label">Upload Resume (optional — enhances personalization)</label>
              <div
                className={`upload-zone ${dragOver ? "dragover" : ""} ${resumeFile ? "uploaded" : ""}`}
                onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
                onDragLeave={() => setDragOver(false)}
                onDrop={handleDrop}
                onClick={() => document.getElementById("resume-input").click()}
              >
                {resumeFile ? (
                  <>
                    <div className="upload-icon">📄</div>
                    <p style={{ color: "var(--ibm-green)", fontWeight: 600 }}>{resumeFile.name}</p>
                    <small>Click to replace</small>
                  </>
                ) : (
                  <>
                    <div className="upload-icon">📎</div>
                    <p>Drop your resume here or click to browse</p>
                    <small>Supports PDF, DOCX, TXT — parsed using Docling</small>
                  </>
                )}
                <input
                  id="resume-input"
                  type="file"
                  accept=".pdf,.docx,.doc,.txt"
                  style={{ display: "none" }}
                  onChange={(e) => setResumeFile(e.target.files[0])}
                />
              </div>
            </div>

            <div className="divider" />
            <button type="submit" className="btn btn-primary btn-lg btn-full" disabled={loading}>
              {loading ? <><Spinner /> Building your session...</> : "🚀 Start Interview Session"}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

// ─── Interview Screen ─────────────────────────────────────────────────────────

function InterviewScreen({ session, onComplete }) {
  const [currentQuestion, setCurrentQuestion] = useState(session.first_question);
  const [answer, setAnswer] = useState("");
  const [feedback, setFeedback] = useState(null);
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState({
    answered: 0,
    total: session.total_planned_questions,
    progress_pct: 0,
    average_score: 0,
  });
  const [showTips, setShowTips] = useState(false);
  const [showChat, setShowChat] = useState(false);
  const [error, setError] = useState("");
  const timer = useTimer();

  useEffect(() => {
    timer.start();
  }, [currentQuestion]);

  const handleSubmit = async () => {
    if (!answer.trim() || answer.trim().length < 10) {
      setError("Please write at least 10 characters in your answer.");
      return;
    }
    setError("");
    const timeTaken = timer.stop();
    setLoading(true);

    try {
      const res = await api.submitAnswer(session.session_id, {
        question_id: currentQuestion.question_id,
        question_text: currentQuestion.question_text,
        answer_text: answer.trim(),
        time_taken_seconds: timeTaken,
      });
      setFeedback(res.feedback);
      setProgress(res.session_progress);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleNext = async () => {
    if (progress.is_complete || !feedback?.next_question === null) {
      onComplete(session.session_id);
      return;
    }

    // Move to next question
    try {
      const res = await api.submitAnswer(session.session_id, {
        question_id: currentQuestion.question_id,
        question_text: currentQuestion.question_text,
        answer_text: answer,
        time_taken_seconds: 0,
      });
      const next = res.next_question;
      if (!next || res.session_progress.is_complete) {
        onComplete(session.session_id);
      } else {
        setCurrentQuestion(next);
        setFeedback(null);
        setAnswer("");
        setShowTips(false);
        timer.start();
      }
      setProgress(res.session_progress);
    } catch {
      // Try to advance anyway
      const nextFromFeedback = feedback?.next_question;
      if (nextFromFeedback) {
        setCurrentQuestion(nextFromFeedback);
        setFeedback(null);
        setAnswer("");
        setShowTips(false);
        setProgress((p) => ({
          ...p,
          answered: p.answered + 1,
          progress_pct: Math.round(((p.answered + 1) / p.total) * 100),
        }));
        timer.start();
      } else {
        onComplete(session.session_id);
      }
    }
  };

  const isLastQuestion = progress.answered >= progress.total - 1;

  return (
    <div className="main-content">
      {/* Sidebar */}
      <div className="sidebar">
        <div className="sidebar-header">
          <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginBottom: "4px" }}>Session</div>
          <div style={{ fontSize: "0.875rem", fontWeight: 600, color: "white" }}>{session.session_id.slice(0, 8)}...</div>
        </div>

        <div className="sidebar-session-info">
          <div className="session-label">Candidate</div>
          <div className="session-value">{session.profile?.name || "—"}</div>
          <div className="session-label" style={{ marginTop: "10px" }}>Role</div>
          <div className="session-value">{session.profile?.job_role || "—"}</div>
        </div>

        <div className="progress-section">
          <div className="progress-label">
            <span>Progress</span>
            <span>{progress.answered}/{progress.total}</span>
          </div>
          <div className="progress-bar-track">
            <div className="progress-bar-fill" style={{ width: `${progress.progress_pct}%` }} />
          </div>
          {progress.average_score > 0 && (
            <div className="score-badge">
              <div className="score-ring">{progress.average_score}</div>
              <div style={{ fontSize: "0.7rem", color: "var(--text-muted)", marginTop: "2px" }}>Avg Score</div>
            </div>
          )}
        </div>

        <div className="sidebar-nav">
          <div className="sidebar-nav-item" onClick={() => setShowChat(!showChat)}>
            <span className="nav-icon">🤖</span> AI Coach
          </div>
          {session.session_roadmap?.map((item, i) => (
            <div
              key={i}
              className={`sidebar-nav-item ${i === progress.answered ? "active" : ""}`}
              style={{ paddingLeft: "24px", opacity: i < progress.answered ? 0.5 : 1 }}
            >
              <span className="nav-icon" style={{ fontSize: "0.75rem" }}>
                {i < progress.answered ? "✅" : i === progress.answered ? "▶" : "○"}
              </span>
              <span style={{ fontSize: "0.78rem" }}>Q{i + 1}: {item.type}</span>
              <span className={`question-badge ${badgeDiffClass(item.difficulty)}`} style={{ marginLeft: "auto", padding: "2px 6px", fontSize: "0.65rem" }}>
                {item.difficulty}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Main Content */}
      <div className="content-area">
        <div className="interview-layout">
          {/* Left: Question + Answer */}
          <div>
            <div className="card mb-4">
              <div className="card-header">
                <div className="card-icon blue">❓</div>
                <div>
                  <h2>Question {progress.answered + 1} of {progress.total}</h2>
                  <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
                    {session.profile?.job_role} · {session.profile?.experience_level}
                  </div>
                </div>
                <div className="topbar-spacer" />
                <div className={`timer-display ${timer.running ? "running" : ""}`}>
                  ⏱ {timer.fmt}
                </div>
              </div>
              <div className="card-body">
                <div style={{ display: "flex", gap: "6px", flexWrap: "wrap", marginBottom: "12px" }}>
                  <span className={`question-badge ${badgeTypeClass(currentQuestion.question_type)}`}>
                    {currentQuestion.question_type.replace("_", " ")}
                  </span>
                  <span className={`question-badge ${badgeDiffClass(currentQuestion.difficulty)}`}>
                    {currentQuestion.difficulty}
                  </span>
                  {currentQuestion.expected_duration_minutes && (
                    <span className="question-badge" style={{ background: "#f4f4f4", color: "#525252" }}>
                      ~{currentQuestion.expected_duration_minutes} min
                    </span>
                  )}
                </div>

                <div className="question-text">{currentQuestion.question_text}</div>

                {currentQuestion.context && (
                  <div className="question-context">💡 {currentQuestion.context}</div>
                )}

                {currentQuestion.tips && currentQuestion.tips.length > 0 && (
                  <div className="tips-section">
                    <button className="tips-toggle" onClick={() => setShowTips(!showTips)}>
                      {showTips ? "▾" : "▸"} Preparation Tips
                    </button>
                    {showTips && (
                      <ul className="tips-list">
                        {currentQuestion.tips.map((t, i) => <li key={i}>{t}</li>)}
                      </ul>
                    )}
                  </div>
                )}

                {!feedback && (
                  <div className="answer-area">
                    <div className="answer-meta">
                      <label className="form-label" style={{ margin: 0 }}>Your Answer</label>
                      <span className={`char-count ${answer.length > 1200 ? "warning" : ""}`}>
                        {answer.length} characters
                      </span>
                    </div>
                    <textarea
                      className="form-textarea"
                      style={{ minHeight: "180px" }}
                      placeholder="Type your answer here... Use the STAR method for behavioral questions: Situation, Task, Action, Result."
                      value={answer}
                      onChange={(e) => setAnswer(e.target.value)}
                    />
                    {error && <Alert type="error">{error}</Alert>}
                    <div className="action-row">
                      <button
                        className="btn btn-primary btn-lg"
                        onClick={handleSubmit}
                        disabled={loading || !answer.trim()}
                      >
                        {loading ? <><Spinner /> Evaluating with IBM Granite...</> : "✅ Submit Answer"}
                      </button>
                      <button
                        className="btn btn-ghost"
                        onClick={handleNext}
                        disabled={loading}
                      >
                        Skip →
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {feedback && (
              <FeedbackPanel
                feedback={feedback}
                onNext={handleNext}
                isLastQuestion={isLastQuestion}
              />
            )}
          </div>

          {/* Right: Chat Coach */}
          <div style={{ height: "calc(100vh - 56px - 48px)", position: "sticky", top: "24px" }}>
            <ChatCoach sessionId={session.session_id} />
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── Summary Screen ────────────────────────────────────────────────────────────

function SummaryScreen({ sessionId, profile, onRestart }) {
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const chartRef = useRef(null);
  const chartInstance = useRef(null);

  useEffect(() => {
    api.getSummary(sessionId)
      .then(setSummary)
      .catch(() => setSummary(null))
      .finally(() => setLoading(false));
  }, [sessionId]);

  useEffect(() => {
    if (summary && chartRef.current) {
      if (chartInstance.current) chartInstance.current.destroy();
      const labels = Object.keys(summary.topic_performance);
      const data = Object.values(summary.topic_performance);
      chartInstance.current = new Chart(chartRef.current, {
        type: "radar",
        data: {
          labels,
          datasets: [{
            label: "Performance Score",
            data,
            backgroundColor: "rgba(15,98,254,0.15)",
            borderColor: "#0f62fe",
            pointBackgroundColor: "#0f62fe",
            pointRadius: 5,
          }],
        },
        options: {
          responsive: true,
          scales: { r: { min: 0, max: 10, ticks: { stepSize: 2 } } },
          plugins: { legend: { display: false } },
        },
      });
    }
  }, [summary]);

  if (loading) return <LoadingOverlay message="Generating your performance report..." subtext="IBM Granite is analyzing your session" />;

  if (!summary) {
    return (
      <div className="summary-screen">
        <Alert type="error">Could not load session summary. The backend may not be running.</Alert>
        <button className="btn btn-primary" onClick={onRestart}>Start New Session</button>
      </div>
    );
  }

  const score = summary.average_score;

  return (
    <div className="content-area">
      <div className="summary-screen">
        {/* Header */}
        <div className="summary-header">
          <div className="summary-score-hero">
            <div className="score-val">{score.toFixed(1)}</div>
            <div className="score-sub">/ 10</div>
          </div>
          <h1 style={{ fontSize: "1.8rem", fontWeight: 700 }}>
            {scoreEmoji(score)} Session Complete!
          </h1>
          <p style={{ color: "var(--text-secondary)", marginTop: "8px" }}>
            {summary.candidate_name} · {summary.job_role} · {new Date(summary.created_at).toLocaleDateString()}
          </p>
        </div>

        {/* Stats Grid */}
        <div className="summary-grid mb-4">
          <div className="summary-stat-card">
            <div className="stat-label">Questions Answered</div>
            <div className="stat-value">{summary.answered_questions} / {summary.total_questions}</div>
          </div>
          <div className="summary-stat-card">
            <div className="stat-label">Average Score</div>
            <div className="stat-value" style={{ color: score >= 7 ? "var(--ibm-green)" : score >= 5.5 ? "var(--ibm-orange)" : "var(--ibm-red)" }}>
              {score.toFixed(1)} / 10
            </div>
          </div>
        </div>

        {/* Recommendation */}
        <div className="recommendation-box">
          <strong>IBM Granite Assessment:</strong><br />
          {summary.recommendation}
        </div>

        {/* Performance Chart */}
        {Object.keys(summary.topic_performance).length > 1 && (
          <div className="card mb-4">
            <div className="card-header">
              <div className="card-icon blue">📊</div>
              <h2>Performance by Category</h2>
            </div>
            <div className="card-body" style={{ display: "flex", justifyContent: "center" }}>
              <canvas ref={chartRef} style={{ maxWidth: "380px", maxHeight: "280px" }} />
            </div>
          </div>
        )}

        <div className="summary-grid">
          {/* Strengths */}
          <div className="card">
            <div className="card-header">
              <div className="card-icon green">💪</div>
              <h2>Top Strengths</h2>
            </div>
            <div className="card-body">
              {summary.top_strengths.length ? (
                <ul className="feedback-list strengths">
                  {summary.top_strengths.map((s, i) => <li key={i}>✅ {s}</li>)}
                </ul>
              ) : <p className="text-muted">Keep practicing to identify strengths!</p>}
            </div>
          </div>

          {/* Weaknesses */}
          <div className="card">
            <div className="card-header">
              <div className="card-icon orange">🔧</div>
              <h2>Areas to Improve</h2>
            </div>
            <div className="card-body">
              {summary.top_weaknesses.length ? (
                <ul className="feedback-list improvements">
                  {summary.top_weaknesses.map((w, i) => <li key={i}>📈 {w}</li>)}
                </ul>
              ) : <p className="text-muted">Excellent work — no critical gaps found!</p>}
            </div>
          </div>
        </div>

        {/* Next Steps */}
        <div className="card mt-4">
          <div className="card-header">
            <div className="card-icon purple">🗺️</div>
            <h2>Your Action Plan</h2>
          </div>
          <div className="card-body">
            <ol style={{ paddingLeft: "20px" }}>
              {summary.next_steps.map((step, i) => (
                <li key={i} style={{ marginBottom: "10px", fontSize: "0.9rem", color: "var(--text-secondary)" }}>
                  {step}
                </li>
              ))}
            </ol>
          </div>
        </div>

        <div className="divider" />
        <div style={{ display: "flex", gap: "12px", justifyContent: "center" }}>
          <button className="btn btn-primary btn-lg" onClick={onRestart}>
            🔄 Start New Session
          </button>
          <button className="btn btn-secondary btn-lg" onClick={() => window.print()}>
            🖨️ Print Report
          </button>
        </div>

        <div style={{ textAlign: "center", marginTop: "32px", fontSize: "0.75rem", color: "var(--text-muted)" }}>
          Powered by IBM Granite (watsonx.ai) · CareerForge AI v1.0 · IBM SkillsBuild University Challenge
        </div>
      </div>
    </div>
  );
}

// ─── Root Application ─────────────────────────────────────────────────────────

function App() {
  const [screen, setScreen] = useState("setup"); // "setup" | "interview" | "summary"
  const [session, setSession] = useState(null);
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleStart = async (profileData, resumeFile) => {
    setLoading(true);
    setError("");

    try {
      const sess = await api.startSession(profileData);
      setSession({ ...sess, profile: profileData });
      setProfile(profileData);

      // Upload resume after session is created
      if (resumeFile) {
        try {
          const uploadRes = await api.uploadResume(sess.session_id, resumeFile);
          console.log("Resume uploaded:", uploadRes);
        } catch {
          console.warn("Resume upload failed — continuing without personalization.");
        }
      }

      setScreen("interview");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleComplete = (sessionId) => {
    setScreen("summary");
  };

  const handleRestart = () => {
    setSession(null);
    setProfile(null);
    setError("");
    setScreen("setup");
  };

  return (
    <div className="app-shell">
      {loading && <LoadingOverlay message="Connecting to IBM watsonx.ai..." subtext="Initializing IBM Granite RAG pipeline for your session" />}

      {/* Top Navigation */}
      <nav className="topbar">
        <div className="topbar-logo">
          <div className="logo-icon">CF</div>
          <div>
            <div>CareerForge AI</div>
            <div className="topbar-subtitle">Intelligent Interview Trainer</div>
          </div>
        </div>
        <div className="topbar-spacer" />
        {session && (
          <span style={{ fontSize: "0.8rem", color: "#c6c6c6" }}>
            Session: {session.session_id.slice(0, 8)}
          </span>
        )}
        <span className="topbar-ibm-badge">IBM Granite</span>
        {session && screen === "interview" && (
          <button className="btn btn-ghost btn-sm" style={{ color: "white", borderColor: "#525252" }} onClick={handleRestart}>
            New Session
          </button>
        )}
      </nav>

      {/* Screen Router */}
      {screen === "setup" && (
        <div className="content-area">
          {error && (
            <div style={{ padding: "16px 24px 0" }}>
              <Alert type="error">{error} — Make sure the backend is running on port 8000.</Alert>
            </div>
          )}
          <SetupScreen onStart={handleStart} />
        </div>
      )}

      {screen === "interview" && session && (
        <InterviewScreen session={session} onComplete={handleComplete} />
      )}

      {screen === "summary" && session && (
        <SummaryScreen
          sessionId={session.session_id}
          profile={profile}
          onRestart={handleRestart}
        />
      )}
    </div>
  );
}

// ─── Mount ────────────────────────────────────────────────────────────────────
const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(<App />);
