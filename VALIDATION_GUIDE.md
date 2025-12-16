# Local Validation Guide

**Purpose**: Validate that the InsuranceAI Toolkit Streamlit web UI is properly configured and ready for Guardian demo.

**Audience**: Developers, QA, Guardian technical team

**Duration**: ~15 minutes for full validation

---

## Prerequisites

- Python 3.11+
- pip or uv package manager
- Git
- ~500MB disk space
- Internet connection (for pypi.org, only needed once for installation)

---

## Step 1: Clone & Install (5 minutes)

### 1.1 Clone Repository

```bash
git clone https://github.com/yourusername/insurance_ai_toolkit.git
cd insurance_ai_toolkit
```

### 1.2 Create Virtual Environment (Optional but Recommended)

```bash
# Using venv
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Or using uv (faster)
uv venv
source .venv/bin/activate
```

### 1.3 Install Dependencies

```bash
# Install with web extras (Streamlit + Plotly required for UI)
pip install -e ".[web]"

# Or using uv
uv pip install -e ".[web]"
```

**Expected Output**:
```
Successfully installed streamlit-1.28.x plotly-5.14.x pandas-2.x ...
```

---

## Step 2: Validate Installation (2 minutes)

### 2.1 Check Python Version

```bash
python --version
```

**Expected**: Python 3.11.x or higher

### 2.2 Verify Key Dependencies

```bash
python -c "import streamlit; import plotly; import pandas; print('✅ All dependencies installed')"
```

**Expected Output**:
```
✅ All dependencies installed
```

### 2.3 Verify Project Structure

```bash
ls -la src/insurance_ai/web/
```

**Expected Files**:
```
app.py                          ✅ Main entry point
config.py                       ✅ Configuration
pages/                          ✅ Multi-page directory
  ├── 01_dashboard.py
  ├── 02_underwriting.py
  ├── 03_reserves.py
  ├── 04_hedging.py
  ├── 05_behavior.py
  └── 06_scenarios.py
components/                     ✅ Component modules
  ├── charts.py                 ✅
  ├── metrics.py                ✅ (NEW)
  ├── forms.py                  ✅ (NEW)
  ├── sidebar.py
  └── warnings.py
data/                           ✅ Demo data
  ├── demo_scenarios.py
  └── constants.py
utils/                          ✅ Utilities
  ├── state_manager.py
  └── formatters.py             ✅ (NEW)
```

---

## Step 3: Run Tests (3 minutes)

### 3.1 Run All Tests

```bash
pytest tests/ -v
```

**Expected Output**:
```
tests/integration/test_streamlit_pages.py::TestMainApp::test_main_app_loads PASSED
tests/integration/test_streamlit_pages.py::TestUnderwritingPage::... SKIPPED
tests/unit/test_chart_functions.py::... SKIPPED
...
========= 1 passed, 55 skipped in 2.45s =========
```

### 3.2 Run Only Passing Tests

```bash
pytest tests/ -v -k "not Skipped" --tb=short
```

**Expected**: 1-8 tests passed (depending on optional dependencies)

### 3.3 Check Coverage

```bash
pytest tests/ --cov=src/insurance_ai/web --cov-report=term-missing
```

**Expected**: Coverage report showing tested modules

---

## Step 4: Launch Streamlit App (5 minutes)

### 4.1 Start the App

```bash
streamlit run src/insurance_ai/web/app.py
```

**Expected Output**:
```
  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.x.x:8501
```

### 4.2 Open in Browser

Navigate to **http://localhost:8501**

**Expected Initial State**:
- ✅ Guardian branding visible (logo, blue header #003DA5)
- ✅ Dashboard page loaded
- ✅ Sidebar with 6 pages visible:
  - 📊 Dashboard
  - 📋 Underwriting
  - 📈 Reserves
  - 🛡️ Hedging
  - 👤 Behavior
  - 🔄 Scenarios
- ✅ "Select Scenario" dropdown showing scenarios:
  - 💰 In-The-Money
  - 🔽 Out-The-Money
  - ⚖️ At-The-Money
  - 📉 High Withdrawal Stress
- ✅ "🚀 Run Workflow" button visible
- ✅ No errors in browser console (F12 → Console)

---

## Step 5: Interactive Validation (5+ minutes)

### 5.1 Test Scenario Selection

1. Click scenario dropdown
2. Select "💰 In-The-Money"
3. Verify selection changes in dropdown

**Expected**: Dropdown updates without errors

### 5.2 Test Workflow Execution

1. Click "🚀 Run Workflow" button
2. Wait for status updates (should complete in <10 seconds)
3. Observe workflow status badges updating

**Expected State After Workflow**:
```
✅ Underwriting | ✅ Reserves | ✅ Behavior | ⏳ Hedging
(or similar combination showing crew execution)
```

### 5.3 Test Page Navigation

1. Click "📋 Underwriting" in sidebar
2. Verify page loads with:
   - ✅ Approval badge (APPROVE/DECLINE/RATED)
   - ✅ Confidence score displayed
   - ✅ Extracted data section
   - ✅ Validation checks list
3. Click "📈 Reserves" in sidebar
4. Verify page loads with:
   - ✅ CTE70 metric cards
   - ✅ Histogram chart
   - ✅ Sensitivity tornado chart
   - ✅ Convergence graph
5. Navigate to remaining pages (Hedging, Behavior, Scenarios)

**Expected**: All pages load without errors, charts render

### 5.4 Test Interactive Elements

1. Go to "🔄 Scenarios" page
2. Locate "Parameter Adjustment" sliders
3. Drag "Account Value" slider left/right
4. Observe metrics update in real-time

**Expected**: Sliders respond smoothly, metrics update without page reload

### 5.5 Test Error Handling

1. Optional: Temporarily break a data fixture
2. Re-run workflow
3. Observe graceful error handling (warning banners, not crashes)

**Expected**: App shows helpful warning message, doesn't crash

---

## Step 6: Performance Validation (2 minutes)

### 6.1 Measure Page Load Times

Use browser DevTools (F12 → Network tab):

1. Open Streamlit app
2. Click each page
3. Record load time from Network tab

**Expected Timings**:
- Page load: <2 seconds
- Chart render: <500ms
- Scenario switch: <100ms

### 6.2 Check Memory Usage

```bash
# In separate terminal, while app is running
ps aux | grep streamlit
```

**Expected**: Streamlit process using <500MB RAM

### 6.3 Check Network Tab (F12)

**Expected**:
- ✅ All requests succeed (status 200)
- ✅ No failed resources (404, 500)
- ✅ No console errors or warnings
- ✅ No CORS issues

---

## Step 7: Docker Validation (Optional, 3 minutes)

### 7.1 Build Docker Image

```bash
docker build -t insurance-ai-toolkit .
```

**Expected Output**:
```
Successfully tagged insurance-ai-toolkit:latest
```

### 7.2 Run Docker Container

```bash
docker run -p 8501:8501 insurance-ai-toolkit
```

**Expected Output**:
```
  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
```

### 7.3 Validate in Browser

Navigate to http://localhost:8501

**Expected**: Same behavior as Step 4-5 (validation works in Docker)

### 7.4 Clean Up

```bash
docker stop $(docker ps -q)
docker rmi insurance-ai-toolkit
```

---

## Step 8: Guardian Demo Checklist

### ✅ Pre-Demo Setup (10 minutes before)

- [ ] App installed and running locally
- [ ] All 6 pages visible and functional
- [ ] Scenario selector shows 4 options
- [ ] "Run Workflow" button present
- [ ] Browser network tab shows no errors
- [ ] App performance <2s page load
- [ ] Guardian branding colors consistent (#003DA5)

### ✅ Demo Sequence Validation

- [ ] Dashboard loads with key metrics
- [ ] Underwriting page shows approval badge + confidence
- [ ] Reserves page displays CTE70 histogram + tornado chart
- [ ] Hedging page shows Greeks + payoff diagram
- [ ] Behavior page displays lapse curve + paths
- [ ] Scenarios page has interactive sliders

### ✅ Talking Points Ready

- [ ] DEMO_SCRIPT.md reviewed (30-min narrative)
- [ ] Time savings talking points prepared (weeks → minutes)
- [ ] Competitive advantages clear (capital savings, speed, compliance)
- [ ] Regulatory context understood (VM-21, CTE70, NAIC)
- [ ] Questions anticipated (Q&A section in docs)

---

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'streamlit'"

**Solution**:
```bash
pip install -e ".[web]"
```

Verify installation:
```bash
python -c "import streamlit; print(streamlit.__version__)"
```

---

### Issue: "Port 8501 already in use"

**Solution**:
```bash
# Kill existing Streamlit process
lsof -ti:8501 | xargs kill -9

# Or use different port
streamlit run src/insurance_ai/web/app.py --server.port 8502
```

---

### Issue: Charts render blank / timeout

**Solution**:
```bash
# Clear Streamlit cache
rm -rf ~/.streamlit/cache/

# Reinstall Plotly
pip install --upgrade plotly

# Restart app
streamlit run src/insurance_ai/web/app.py
```

---

### Issue: "Session state key not found"

**Solution**:
1. Go to Dashboard page (01_dashboard.py)
2. Click "🚀 Run Workflow" button
3. Wait for workflow to complete
4. Navigate to crew pages

This initializes session state before viewing results.

---

### Issue: Charts missing or slow

**Solution**:
- Check browser console (F12) for errors
- Verify Plotly installed: `pip show plotly`
- Try clearing browser cache: Ctrl+Shift+Delete
- Check performance: DevTools → Performance tab

---

## Validation Report Template

Use this checklist to document validation results:

```markdown
# Validation Report - 2025-12-15

## Environment
- Python version: 3.11.x
- OS: [Linux/Mac/Windows]
- Browser: [Chrome/Firefox/Safari]

## Installation Status
- [ ] Dependencies installed successfully
- [ ] All required files present
- [ ] Virtual environment working (if used)

## Functional Tests
- [ ] App launches without errors
- [ ] All 6 pages load
- [ ] Charts render on all pages
- [ ] Workflow execution completes
- [ ] Session state persists

## Performance
- [ ] Page load <2s
- [ ] Charts <500ms
- [ ] No memory leaks
- [ ] No console errors

## Guardian Demo Readiness
- [ ] Branding consistent
- [ ] Talking points prepared
- [ ] Demo script reviewed
- [ ] Ready for presentation: [YES/NO]

## Issues Found
- [List any issues]

## Signed
- Validator: ___________
- Date: ___________
```

---

## Success Criteria

All of the following must be true for validation to pass:

✅ **Functional**
- All 6 Streamlit pages load without errors
- All 4 crews display correctly in workflow
- Charts render for all demo scenarios
- Session state persists across navigation
- Mode toggle works (offline/online)

✅ **Performance**
- Page load <2 seconds
- Chart render <500ms
- No memory leaks
- Smooth interactions (sliders, buttons)

✅ **Guardian Impression**
- Professional polish (not prototype feel)
- Clear time savings narrative
- Regulatory rigor evident
- Competitive advantages articulated
- Ready for L4/L5 hiring presentation

✅ **Code Quality**
- No hardcoded secrets
- Error messages helpful
- No console warnings
- Graceful error handling

---

## Next Steps

### After Validation ✅

If all validations pass:
1. **Guardian Presentation Ready**
   - Set up demo time with Guardian
   - Prepare 30-min walkthrough
   - Have documentation ready

2. **Optional Enhancements**
   - Real crew integration (replac fixtures with live crews)
   - Online mode setup (Claude Vision + market data)
   - Data export functionality
   - Mobile responsiveness

3. **Deployment**
   - Docker: `docker-compose up`
   - Streamlit Cloud: Setup secrets, deploy
   - AWS/Azure: Container registry + orchestration

---

## Support & Documentation

**For Installation Help**:
- `docs/STREAMLIT_GUIDE.md` - Installation + troubleshooting
- `README.md` - Project overview
- `pyproject.toml` - Dependencies

**For Demo Preparation**:
- `docs/DEMO_SCRIPT.md` - 30-minute walkthrough
- `docs/GUARDIAN_CONTEXT.md` - Business context
- `PHASE_3_COMPLETION.md` - Feature validation

**For Development**:
- `tests/integration/test_streamlit_pages.py` - Test suite
- `src/insurance_ai/web/` - Codebase structure
- Comments in code files

---

**Last Updated**: 2025-12-15
**Version**: InsuranceAI Toolkit v0.1.0
**Status**: ✅ Validation Guide Complete
