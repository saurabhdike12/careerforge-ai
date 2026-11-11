# CareerForge AI — Demo Script
# IBM SkillsBuild University Education — Problem Statement #22

---

## 🎬 Demo Walkthrough (2-3 minutes)

### Scene 1: Landing & Setup (0:00–0:40)

**Narrator:** "Meet CareerForge AI — an intelligent interview trainer powered by IBM Granite and watsonx.ai. Unlike generic prep tools, CareerForge learns from your resume and adapts every question to your exact profile."

**On screen:**
1. Open `frontend/index.html` in browser
2. Show the hero landing with "Powered by IBM Granite · watsonx.ai · RAG" badge
3. Fill in the setup form:
   - Name: "Priya Sharma"
   - Role: "Software Engineer"  
   - Experience: "Mid (3-6 years)"
   - Focus: Technical + Behavioral
   - Skills: Python, AWS, System Design
4. Upload a sample resume PDF
5. Click "🚀 Start Interview Session"

**Key talking point:** "CareerForge uses LangChain RAG to retrieve role-specific interview patterns from a curated knowledge base, then IBM Granite-13b-chat-v2 generates questions personalized to Priya's profile."

---

### Scene 2: Interview in Action (0:40–1:40)

**On screen:**
1. Session starts — show the session roadmap in the sidebar (9 questions planned)
2. First question appears:
   - Badge: "HR · Easy"
   - Question: "Tell me about yourself and why you're interested in this Software Engineer position."
   - Timer starts automatically
3. Type an answer (demo answer): 
   ```
   I'm a Software Engineer with 4 years of experience specializing in Python 
   backend development and AWS cloud infrastructure. In my current role at 
   TechCorp, I've reduced API latency by 40% by migrating our monolith to 
   microservices. I'm excited about this role because of your focus on 
   distributed systems at scale, which aligns perfectly with my expertise.
   ```
4. Click "✅ Submit Answer"
5. Show IBM Granite evaluating in real-time (loading state)
6. Feedback panel appears:
   - Overall Score: 8.2/10 ✅
   - Relevance: 9.0, STAR: 7.5, Technical: 8.5, Communication: 8.0, Originality: 8.0
   - Strengths: ["Quantified impact (40% latency reduction)", "Clear narrative arc", "Connected to company mission"]
   - Improvement: ["Elaborate more on future goals", "Mention team collaboration"]
   - Keywords Used: ✓ Python ✓ microservices ✓ AWS
   - Keywords Missed: ✗ distributed systems

**Key talking point:** "IBM Granite analyzes the answer against the STAR framework, technical accuracy, and domain keywords. The feedback is specific, actionable, and explains its reasoning — a core tenet of IBM's Ethical AI principles."

---

### Scene 3: AI Coach Chat (1:40–2:10)

**On screen:**
1. Click "🤖 AI Coach" in the sidebar
2. Type: "How should I answer system design questions for senior roles?"
3. IBM Granite responds with specific guidance about capacity estimation, component design, trade-off analysis

**Key talking point:** "The coach is always available for guidance, powered by RAG — it retrieves relevant interview patterns before generating advice, ensuring grounded, accurate coaching rather than hallucinated responses."

---

### Scene 4: Session Summary & Analytics (2:10–2:45)

**On screen:**
1. Skip to end of session → "🏁 Finish & Get Full Report"
2. Show Summary screen:
   - Score: 7.8/10 — Strong performance
   - Radar chart showing performance by category
   - Top Strengths: ["Clear quantification of impact", "Strong technical vocabulary"]
   - Action Plan: ["Deep-dive on system design", "Practice 2 mock interviews/week"]
3. Show Print Report button

**Key talking point:** "CareerForge doesn't just score — it builds a personalized action plan. Sessions are persisted in SQLite, enabling progress tracking across multiple practice rounds."

---

## 💡 Key Differentiators to Highlight

| Feature | CareerForge AI | Generic Tools |
|---------|---------------|---------------|
| Question generation | IBM Granite + RAG (role-specific) | Static question banks |
| Feedback | AI-powered STAR analysis | Pre-written answers |
| Personalization | Resume-aware, skill-matched | One-size-fits-all |
| AI backbone | IBM Granite (enterprise-grade) | Unspecified/consumer AI |
| Ethical AI | Transparent reasoning, bias monitoring | Not addressed |
| Architecture | Full-stack production app | Simple chatbot |

---

## 🔧 Technical Demo Notes

- Backend must be running: `uvicorn backend.main:app --reload`
- IBM watsonx.ai credentials in `.env` file
- Without credentials: app still works in "degraded mode" with fallback responses
- Demonstrate the `/docs` Swagger UI for API exploration
- Show ChromaDB vector store health in `/health` endpoint
