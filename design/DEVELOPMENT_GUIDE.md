# Development Guide - Market Mayhem

## 🎯 **AI Development Instructions**

This guide tells AI assistants exactly which files to follow and in what order to build Market Mayhem - a portfolio-building, news-driven investing game where players compete against a trash-talking Villain AI.

## **Game Concept in One Sentence**
Market Mayhem is a portfolio-building, news-driven investing game where a player starts with $1,000,000, reacts to real-world style events while a trash-talking Villain AI tries to mislead them, and—using a Data tab—they aim to make rational choices.

---

## 📋 **Core Design Files (Follow in Order)**

### **1. Start Here: Architecture Overview**
**File**: `software_architecture.md`
- **Purpose**: High-level system design and components for Market Mayhem
- **What to read**: Portfolio system, Data tab, Villain AI, decision tracking, outcome replay
- **When to use**: Before starting any implementation

### **2. Domain Design**
**File**: `domain_driven_design.md`
- **Purpose**: Business logic and domain models for Market Mayhem
- **What to read**: Portfolio, Position, Event, Decision, Behavioral Profile entities
- **When to use**: When building domain layer (Phase 1)

### **3. Technology Stack**
**File**: `tech_stack.md`
- **Purpose**: All libraries, versions, and dependencies
- **What to read**: Package versions, API keys, deployment config
- **When to use**: When setting up environment (Phase 0)

### **4. Multi-Agent System**
**File**: `agent_architecture_and_flow.md`
- **Purpose**: 6 specialized AI agents (Event Generator, Portfolio, News, Price, Villain, Insight) and their collaboration
- **What to read**: Event Generator Agent (scenario creation), Portfolio Agent (portfolio management), News Agent (headlines+stance), Price Agent (historical replay), Villain Agent (trash-talking bias), Insight Agent (coaching)
- **When to use**: When building agents (Phase 3)

### **5. LangGraph Implementation**
**File**: `langgraph_workflow.md`
- **Purpose**: How to implement agents with LangGraph
- **What to read**: Agent creation, tool definitions, graph construction
- **When to use**: When coding agents (Phase 3)

### **6. External API Integration**
**File**: `tavily_integration.md`
- **Purpose**: How to use Tavily for news fetching, stance detection, and contradiction scoring
- **What to read**: API usage, stance tagging, caching, rate limits
- **When to use**: When implementing tools (Phase 3)

### **7. Observability & LangSmith Visualization**
**File**: `opik_integration.md`
- **Purpose**: LLM observability, tracing, and LangSmith agent visualization
- **What to read**: Agent tracing, custom metrics, dashboards, LangSmith setup
- **When to use**: When adding monitoring and visualization (Phase 7.5)

### **8. Step-by-Step Implementation**
**File**: `implementation_roadmap.md`
- **Purpose**: Complete build instructions
- **What to read**: All phases, code examples, checkpoints
- **When to use**: Throughout entire development process

---

## 🚀 **Development Sequence**

### **Phase 0: Setup** (30 minutes)
1. **Read**: `tech_stack.md` → Get all package versions and API keys
2. **Read**: `software_architecture.md` → Understand system design
3. **Follow**: `implementation_roadmap.md` Phase 0 → Setup project structure

### **Phase 1: Domain Layer** (2 hours)
1. **Read**: `domain_driven_design.md` → Build pure business logic
2. **Follow**: `implementation_roadmap.md` Phase 1 → Create domain models
3. **Test**: Verify domain logic works independently

### **Phase 2: Tools** (1 hour)
1. **Read**: `tavily_integration.md` → Understand external APIs
2. **Follow**: `implementation_roadmap.md` Phase 2 → Build 16 custom tools
3. **Test**: Verify tools work with real APIs

### **Phase 3: Agents** (3 hours)
1. **Read**: `agent_architecture_and_flow.md` → Understand agent design
2. **Read**: `langgraph_workflow.md` → Learn LangGraph implementation
3. **Follow**: `implementation_roadmap.md` Phase 3 → Build 5 agents
4. **Test**: Verify agents can reason and use tools

### **Phase 4: Application Layer** (2 hours)
1. **Follow**: `implementation_roadmap.md` Phase 4 → Build handlers
2. **Test**: Verify business logic flows correctly

### **Phase 5: API Layer** (2 hours)
1. **Follow**: `implementation_roadmap.md` Phase 5 → Build FastAPI endpoints
2. **Test**: Verify API endpoints work

### **Phase 6: Frontend** (3 hours)
1. **Follow**: `implementation_roadmap.md` Phase 6 → Build Next.js UI
2. **Test**: Verify frontend connects to backend

### **Phase 7: Database** (1 hour)
1. **Follow**: `implementation_roadmap.md` Phase 7 → Setup Supabase
2. **Test**: Verify data persistence works

### **Phase 7.5: Observability** (1 hour, Optional)
1. **Read**: `opik_integration.md` → Add LLM tracing
2. **Follow**: `implementation_roadmap.md` Phase 7.5 → Add Opik
3. **Test**: Verify traces appear in dashboard

### **Phase 8: Testing** (2 hours)
1. **Follow**: `implementation_roadmap.md` Phase 8 → Test everything
2. **Verify**: Complete game flow works end-to-end

---

## 📁 **File Priority Matrix**

| File | Priority | When to Read | Purpose |
|------|----------|--------------|---------|
| `implementation_roadmap.md` | **CRITICAL** | Always | Step-by-step instructions |
| `tech_stack.md` | **HIGH** | Phase 0 | Dependencies and versions |
| `software_architecture.md` | **HIGH** | Phase 0 | System design |
| `agent_architecture_and_flow.md` | **HIGH** | Phase 3 | Agent design |
| `langgraph_workflow.md` | **HIGH** | Phase 3 | Agent implementation |
| `domain_driven_design.md` | **MEDIUM** | Phase 1 | Domain models |
| `tavily_integration.md` | **MEDIUM** | Phase 2 | External APIs |
| `opik_integration.md` | **LOW** | Phase 7.5 | Optional monitoring |

---

## 🎯 **Quick Start for AI Assistant**

### **If Building from Scratch:**
1. **Start with**: `implementation_roadmap.md` Phase 0
2. **Reference**: `tech_stack.md` for versions
3. **Follow**: Each phase in `implementation_roadmap.md`
4. **Read**: Specific design files as needed per phase

### **If Debugging Specific Issues:**
1. **Agent problems**: Read `agent_architecture_and_flow.md` + `langgraph_workflow.md`
2. **API issues**: Read `tavily_integration.md`
3. **Domain logic**: Read `domain_driven_design.md`
4. **System design**: Read `software_architecture.md`

### **If Adding Features:**
1. **New agent**: Follow `agent_architecture_and_flow.md` pattern
2. **New tool**: Follow `tavily_integration.md` pattern
3. **New domain concept**: Follow `domain_driven_design.md` pattern

---

## 📋 **Development Checklist**

### **Before Starting:**
- [ ] Read `software_architecture.md` for system overview
- [ ] Read `tech_stack.md` for all dependencies
- [ ] Get API keys (Gemini, Tavily, Supabase, Upstash, Opik)
- [ ] Setup development environment

### **During Development:**
- [ ] Follow `implementation_roadmap.md` phase by phase
- [ ] Reference specific design files as needed
- [ ] Test each phase before moving to next
- [ ] Use checkpoints to verify progress

### **Before Deployment:**
- [ ] Complete all phases in `implementation_roadmap.md`
- [ ] Test complete game flow
- [ ] Verify all agents work together
- [ ] Check observability (if using Opik)

---

## 🔧 **Common Development Patterns**

### **Adding New Agent:**
1. Read `agent_architecture_and_flow.md` for design pattern
2. Read `langgraph_workflow.md` for implementation
3. Follow `implementation_roadmap.md` Phase 3 pattern
4. Add to `opik_integration.md` if using observability

### **Adding New Tool:**
1. Read `tavily_integration.md` for API pattern
2. Follow `implementation_roadmap.md` Phase 2 pattern
3. Add to agent in `langgraph_workflow.md`
4. Add tracing in `opik_integration.md`

### **Adding New Domain Concept:**
1. Read `domain_driven_design.md` for patterns
2. Follow `implementation_roadmap.md` Phase 1 pattern
3. Update repositories and handlers
4. Add to application layer

---

## 📚 **File Dependencies**

```
implementation_roadmap.md (MASTER)
├── tech_stack.md (dependencies)
├── software_architecture.md (system design)
├── domain_driven_design.md (domain models)
├── agent_architecture_and_flow.md (agent design)
├── langgraph_workflow.md (agent implementation)
├── tavily_integration.md (external APIs)
└── opik_integration.md (observability)
```

---

## ⚡ **Quick Reference**

### **Need to understand Market Mayhem?**
→ Read `software_architecture.md` (Portfolio, Villain AI, Data tab)

### **Need to start coding?**
→ Follow `implementation_roadmap.md`

### **Need to build the 6 agents?**
→ Read `agent_architecture_and_flow.md` (Event Generator/Portfolio/News/Price/Villain/Insight) + `langgraph_workflow.md`

### **Need to integrate news APIs?**
→ Read `tavily_integration.md` (headline fetching, stance detection)

### **Need to add monitoring and visualization?**
→ Read `opik_integration.md` (Opik tracing + LangSmith visualization)

### **Need to understand domain?**
→ Read `domain_driven_design.md` (Portfolio, Position, Decision Tracker)

---

## 🎯 **Success Criteria**

**Market Mayhem is complete when:**
- [ ] All phases in `implementation_roadmap.md` completed
- [ ] 6 agents working (Event Generator, Portfolio, News, Price, Villain, Insight)
- [ ] Complete game flow: Portfolio Setup → Round 0 → 5-7 Event Rounds → Final Summary
- [ ] Data tab shows: headlines with stance, fundamentals, recent price behavior, historical outcomes
- [ ] Villain AI generates biased takes with labeled cognitive biases
- [ ] Outcomes replay using matched historical price windows (not random)
- [ ] Decision tracker logs every round with full context
- [ ] Final report generates behavioral profile + coaching
- [ ] Frontend connects to backend
- [ ] Data persists in database
- [ ] Observability + LangSmith visualization working

**Total Development Time**: ~20-25 hours
**Files to Follow**: 8 design documents
**Phases to Complete**: 8 phases + observability + LangSmith

---

**This guide ensures AI assistants follow the correct sequence and reference the right files for building Market Mayhem.** 🚀
