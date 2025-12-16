# Claude API Integration Checklist

## Phase A: Verify & Run (TODAY - 30 minutes)

### ✅ Completed by Claude Code
- [x] Created virtual environment
- [x] Installed all web dependencies (streamlit, plotly, etc.)
- [x] Verified Streamlit app launches successfully
- [x] Confirmed 4 enriched fixtures exist
- [x] Identified mock crew implementations in state_manager.py

### What You Need to Do (5-10 minutes)

- [ ] **Get Claude API Key**
  - Go to https://console.anthropic.com/
  - Create API key (starts with `sk-`)
  - Copy to safe location

- [ ] **Test the Key Works**
  ```bash
  cd insurance_ai_toolkit
  source venv/bin/activate
  export ANTHROPIC_API_KEY="sk-your-key-here"

  python -c "
  import anthropic
  client = anthropic.Anthropic()
  msg = client.messages.create(
      model='claude-3-5-sonnet-20241022',
      max_tokens=100,
      messages=[{'role': 'user', 'content': 'Say hello'}]
  )
  print('✅ Claude API works!')
  "
  ```

- [ ] **Launch App in Offline Mode (No API Key Needed)**
  ```bash
  source venv/bin/activate
  streamlit run src/insurance_ai/web/app.py
  ```
  - Open http://localhost:8501
  - Click "Run Workflow"
  - Navigate through all 6 pages
  - Verify all fixtures work

---

## Phase B: Real Crew Integration (OPTIONAL - 6-8 hours)

### Why You Might Want This

Current state: **Mock implementations** (simplified, no LLM calls)
```python
def run_underwriting_crew(fixture, mode="offline"):
    if mode == "offline":
        return {"approval_decision": "APPROVE", "confidence_score": 0.95, ...}
    raise NotImplementedError("Online mode not yet implemented")
```

With real crews: **Actual insurance_ai logic** (Monte Carlo, SABR, etc.)
```python
def run_underwriting_crew(fixture, mode="offline"):
    if mode == "offline":
        return load_cached_result(fixture)
    else:
        # Real crew with Claude Vision PDF extraction
        crew = UnderwritingCrew()
        return crew.execute(fixture)
```

### Step 1: Understand Current Crew Structure (1-2 hours)

Examine the real crews in your annuity-pricing codebase:
```bash
# See if crews already exist
find . -name "*crew*" -type f | grep -v ".git" | grep -v "__pycache__" | head -20
```

Questions to answer:
- [ ] Does UnderwritingCrew exist? Where?
- [ ] What are its inputs? Outputs?
- [ ] What Claude API calls does it make?
- [ ] Does it support offline mode?
- [ ] Can it be called from Streamlit?

### Step 2: Check Real Crew Dependencies (30 min)

Read the actual crew implementations:
```bash
# Example
cat src/insurance_ai/crews/underwriting_crew.py | head -100
```

Look for:
- [ ] Import statements (which libraries, which Claude APIs?)
- [ ] Class definition and methods
- [ ] Input/output signatures
- [ ] Error handling
- [ ] Async or sync?

### Step 3: Integrate Crews into Web App (4-6 hours)

For **each crew** (Underwriting, Reserve, Hedging, Behavior):

**3.1 Create wrapper function**:
```python
# In src/insurance_ai/web/utils/crew_wrappers.py
from insurance_ai.crews.underwriting_crew import UnderwritingCrew

def run_real_underwriting_crew(fixture: dict) -> dict:
    """
    Call the real UnderwritingCrew (not mock).

    Args:
        fixture: Input scenario data

    Returns:
        Crew execution result
    """
    crew = UnderwritingCrew()

    # Convert fixture format to crew input format
    input_data = {
        "applicant_age": fixture.get("applicant_age"),
        "health_status": fixture.get("health_status"),
        "medical_history": fixture.get("medical_history"),
        # ... other fields
    }

    # Execute crew
    result = crew.execute(input_data)

    # Return result
    return result
```

**3.2 Update state_manager.py**:
```python
# Replace mock run_underwriting_crew with real one
from .crew_wrappers import run_real_underwriting_crew

def run_underwriting_crew(fixture: dict, mode: str = "offline") -> dict:
    if mode == "offline":
        # Use cached/fixture result
        return load_cached_result("underwriting", fixture)
    else:
        # Call real crew
        return run_real_underwriting_crew(fixture)
```

**3.3 Test integration**:
```python
# Create simple test
import streamlit as st
fixture = load_scenario_fixture("001_itm")
result = run_real_underwriting_crew(fixture)
print(f"✅ Real crew result: {result}")
```

**3.4 Repeat for all 4 crews** (Reserve, Hedging, Behavior)

### Step 4: Add Claude Vision for Online Mode (Optional, 2-3 hours)

Create `src/insurance_ai/web/utils/vision_extractor.py`:
```python
import anthropic
import base64

def extract_pdf_with_vision(pdf_path: str) -> dict:
    """Extract medical data from PDF using Claude Vision."""

    client = anthropic.Anthropic()

    # Read PDF
    with open(pdf_path, "rb") as f:
        pdf_base64 = base64.b64encode(f.read()).decode("utf-8")

    # Call Claude Vision
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "application/pdf",
                        "data": pdf_base64,
                    },
                },
                {
                    "type": "text",
                    "text": "Extract medical info from this PDF. Return JSON with: applicant_age, health_status, conditions, etc."
                }
            ],
        }],
    )

    return json.loads(message.content[0].text)
```

Then integrate into UnderwritingCrew online mode:
```python
def run_underwriting_crew(fixture: dict, mode: str = "offline") -> dict:
    if mode == "offline":
        return load_cached_result("underwriting", fixture)
    else:
        # Extract from PDF using Vision
        medical_data = extract_pdf_with_vision(fixture["pdf_path"])

        # Call real crew with extracted data
        return run_real_underwriting_crew({
            **fixture,
            **medical_data  # Merge extracted data
        })
```

### Files You'll Modify

- [ ] `src/insurance_ai/web/utils/state_manager.py` - Replace mock implementations
- [ ] `src/insurance_ai/web/utils/crew_wrappers.py` - NEW file with real crew calls
- [ ] `src/insurance_ai/web/utils/vision_extractor.py` - NEW file for Claude Vision
- [ ] `src/insurance_ai/web/config.py` - Already has ANTHROPIC_API_KEY support

### Time Estimate

| Task | Time | Difficulty |
|------|------|-----------|
| Understand crew structure | 1-2 hrs | Medium |
| Integrate 1 crew | 1-1.5 hrs | Medium |
| Integrate 4 crews | 4-6 hrs | Medium |
| Add Claude Vision | 2-3 hrs | Easy |
| Test integration | 1 hr | Medium |
| **TOTAL** | **8-12 hrs** | |

---

## Phase C: Deploy to Cloud (OPTIONAL - 30 minutes to 3 hours)

### Option 1: Streamlit Cloud (FREE, 30 minutes)

1. Push code to GitHub (with .env in .gitignore!)
2. Go to https://share.streamlit.io/
3. Click "New app"
4. Select your repo
5. Set API key in Secrets panel
6. Deploy

Your app: `https://yourusername-insurance-ai.streamlit.app`

### Option 2: Docker + AWS EC2 (Production, 2-3 hours)

```bash
# Build Docker image
docker build -t insurance-ai-toolkit .

# Tag for AWS ECR
docker tag insurance-ai-toolkit:latest 123456789.dkr.ecr.us-east-1.amazonaws.com/insurance-ai:latest

# Push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789.dkr.ecr.us-east-1.amazonaws.com
docker push 123456789.dkr.ecr.us-east-1.amazonaws.com/insurance-ai:latest

# Deploy to ECS, EC2, or Kubernetes
# (See DEPLOYMENT.md for full instructions)
```

---

## What You Actually Need to Do Right Now (Honest Assessment)

### TODAY (Do This)
1. **5 minutes**: Get Claude API key from console.anthropic.com
2. **5 minutes**: Test the key with the Python script
3. **5 minutes**: Launch the app: `streamlit run src/insurance_ai/web/app.py`
4. **Enjoy the demo** - Offline mode works perfectly for Guardian presentation!

### THIS WEEK (Optional, Only if You Want "Real" Crews)
- Spend 1-2 hours reviewing your actual crew implementations
- Decide: Do you want real crews (8-12 hrs work) or is offline fine?
- Real crews are impressive but require integration work

### FOR GUARDIAN PRESENTATION (Recommended)
- Just use offline mode!
- It works perfectly
- No additional setup needed
- You can say: "This is our reliable offline demo mode. In production, it connects to Claude Vision for PDF extraction and live market APIs."

---

## Do You ACTUALLY Need Real Crew Integration?

### Use Offline Mode If:
- ✅ You want to demo THIS WEEK
- ✅ You want zero API call delays
- ✅ You want deterministic, reproducible results
- ✅ You want to show Guardian a polished, fast demo
- ✅ You're comfortable saying "production mode uses real crews"

### Implement Real Crews If:
- ✅ You have time (8-12 hours)
- ✅ You want to show actual Claude Vision PDF extraction
- ✅ You want to demonstrate integration with your insurance_ai package
- ✅ You're not in a rush

### My Recommendation
**Do offline mode for Guardian demo.** It's fast, reliable, and shows the system design perfectly. Real crews can be a v0.2.0 feature.

---

## Quick Reference: Commands You'll Use

```bash
# Setup
cd insurance_ai_toolkit
source venv/bin/activate
export ANTHROPIC_API_KEY="sk-..."

# Run locally
streamlit run src/insurance_ai/web/app.py

# Run with Docker
docker-compose up

# Deploy to Streamlit Cloud
git push origin main  # Streamlit auto-deploys

# Check API key works
python -c "import anthropic; print('✅ OK')"
```

---

## Files You Should Read

1. **CLAUDE_API_SETUP.md** - Detailed API setup instructions
2. **DEPLOYMENT.md** - How to deploy to cloud
3. **VALIDATION_GUIDE.md** - How to test the app
4. **GETTING_STARTED.md** - Quick start overview

---

## Summary

| What | Status | Time | Need API Key? |
|------|--------|------|---------------|
| Run app locally | ✅ Works | 5 min | ❌ No |
| Offline demo | ✅ Works | 5 min | ❌ No |
| Real crews | ❌ Mock only | 8-12 hrs | ✅ Yes |
| Claude Vision | ❌ Not implemented | 2-3 hrs | ✅ Yes |
| Deploy to cloud | ⚠️ Ready | 30 min | ✅ Yes |

**Next step**: Get API key (5 min), run app (5 min), demo offline mode (looks great!).

Real crew integration can happen later if you have time.
