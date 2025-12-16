# Phase 2 Plan: Crew Pages + Visualizations (Week 2)

## Overview

Phase 2 builds on Phase 1 foundation to create the full multi-page Streamlit application with:
- **5 Crew Pages** (Underwriting, Reserves, Hedging, Behavior, Scenarios)
- **Chart Components** (Plotly visualizations)
- **Real Crew Integration** (call actual LangGraph workflows)
- **Advanced Interactivity** (parameter sliders, what-if analysis)

## Phase 2 Timeline (48 hours / 6 days)

### Day 1-2: Crew Pages Foundation
- **pages/02_underwriting.py** (8 hrs)
  - Display extraction results
  - Risk classification + approval decision
  - Confidence scores + validation metrics

- **pages/03_reserves.py** (8 hrs)
  - CTE70 calculation display
  - Sensitivity analysis results
  - Convergence metrics (n=100 vs n=1000)

### Day 3: Charts & Metrics
- **components/charts.py** (8 hrs)
  - Plotly histogram (CTE70 distribution)
  - Tornado chart (sensitivity drivers)
  - Lapse curve (moneyness vs lapse)
  - Greeks heatmap (delta/vega surface)
  - 3D volatility surface (SABR)

### Day 4: Behavior + Hedging Pages
- **pages/05_behavior.py** (6 hrs)
  - Dynamic lapse modeling display
  - Withdrawal strategy visualization
  - Reserve impact metrics

- **pages/04_hedging.py** (6 hrs)
  - Greeks display (Delta, Gamma, Vega, Theta, Rho)
  - Hedge recommendations
  - Cost-benefit analysis

### Day 5: Scenario Comparison + Polish
- **pages/06_scenarios.py** (8 hrs)
  - Side-by-side scenario comparison
  - What-if analysis (slider-based parameter adjustment)
  - Portfolio-level aggregation

- **Polish & Testing** (4 hrs)
  - Style consistency
  - Error handling in charts
  - Mobile responsiveness

### Day 6: Real Crew Integration + Tests
- **Real Crew Wrappers** (6 hrs)
  - Replace mock functions with actual LangGraph calls
  - Handle online mode (Claude API, market data)
  - Error handling for API failures

- **Integration Tests** (6 hrs)
  - AppTest-based Streamlit tests
  - Fixture validation tests
  - E2E scenario tests

## Deliverables (Phase 2)

### New Files (~2,500 lines)

```
src/insurance_ai/web/
├── pages/
│   ├── 02_underwriting.py          (250 lines)
│   ├── 03_reserves.py              (300 lines)
│   ├── 04_hedging.py               (250 lines)
│   ├── 05_behavior.py              (250 lines)
│   └── 06_scenarios.py             (350 lines)
│
├── components/
│   ├── charts.py                   (600 lines)
│   ├── metrics.py                  (150 lines)
│   └── forms.py                    (100 lines)
│
└── utils/
    └── crew_wrappers.py            (200 lines)

tests/
└── integration/
    └── test_streamlit_foundation.py (200 lines)
```

## Key Decisions for Phase 2

### Decision: Crew Page Layout
Each crew page follows this pattern:
```
┌─────────────────────────────────────────────┐
│ Page Title + Description                    │
├─────────────────────────────────────────────┤
│ Guardian Callout (time savings, benefits)   │
├─────────────────────────────────────────────┤
│ Key Metrics (KPI cards in 3-4 columns)      │
├─────────────────────────────────────────────┤
│ Visualization (Chart 1)    │ Visualization 2 │
├─────────────────────────────────────────────┤
│ Detailed Results Table (expandable)         │
├─────────────────────────────────────────────┤
│ Sensitivity / What-If Controls (sliders)    │
├─────────────────────────────────────────────┤
│ Validation Warnings (if any)                │
└─────────────────────────────────────────────┘
```

### Decision: Chart Technology
- **Plotly Express** for quick charts (histograms, box plots)
- **Plotly Graph Objects** for custom layouts (heatmaps, 3D surfaces)
- **Streamlit + Plotly** integration via `st.plotly_chart()`
- All charts cached with `@st.cache_resource` for performance

### Decision: Real Crew Integration
Phase 2 will add actual crew wrappers that:
1. **Offline Mode**: Return mock results (current behavior)
2. **Online Mode**: Call actual LangGraph crews
   - UnderwritingCrew: Claude Vision PDF extraction
   - ReserveCrew: Real Monte Carlo simulation
   - HedgingCrew: Real options Greeks + calibration
   - BehaviorCrew: Real lapse modeling + paths

### Decision: Online Mode Setup
```python
# Online mode requires:
ANTHROPIC_API_KEY=sk-... streamlit run app.py

# Or configure in sidebar:
- API key validation on mode switch
- Graceful fallback to offline if API fails
- Show "🌐 Online" indicator in sidebar
```

## Chart Specifications

### Underwriting Page
- **Confidence Score Gauge** (0-100%)
- **Risk Class Badge** (Standard, Preferred, Rated)
- **Approval Decision (Large)**

### Reserves Page
- **CTE70 Distribution Histogram**
  - X-axis: Reserve amount
  - Y-axis: Frequency
  - Overlay: CTE70 line, Mean line
- **Sensitivity Tornado Chart**
  - Top 5 drivers of reserve
  - Rate, Vol, Lapse, Withdrawal, Expense
- **Convergence Graph**
  - X-axis: Number of scenarios (100 to 10000)
  - Y-axis: CTE70 value
  - Shows stability of estimate

### Hedging Page
- **Greeks Display (5 cards)**
  - Delta, Gamma, Vega, Theta, Rho
- **Greeks Heatmap**
  - X: Underlying price (-20% to +20%)
  - Y: Volatility (-20% to +20%)
  - Color: Delta / Vega value
- **Hedge Recommendation Card**
  - Action: "Buy Put Spreads"
  - Cost: $5,000
  - Delta Reduction: 80%

### Behavior Page
- **Lapse Curve (Moneyness)**
  - X: Moneyness (0.5 to 1.5)
  - Y: Lapse rate (0% to 20%)
  - Show: Base, ITM, OTM, ATM points
- **Account Path Chart (Box Plot)**
  - X: Year
  - Y: Account value
  - Show: Mean, median, quartiles

### Scenarios Page
- **Comparison Matrix Table**
  - Rows: Scenarios
  - Cols: Moneyness, Account Value, Reserve, Lapse, Hedge Cost
  - Highlight: Best/worst by metric
- **What-If Slider Panel**
  - Parameters: Account Value, Benefit Base, Volatility, Rates
  - Real-time reserve update
  - Show delta vs baseline

## Testing Strategy (Phase 2)

### Unit Tests
```python
# tests/integration/test_streamlit_foundation.py
- test_config_loads_fixtures()
- test_underwriting_page_renders()
- test_reserve_charts_display()
- test_scenario_comparison_calculates()
- test_online_mode_requires_api_key()
- test_graceful_degradation_on_crew_failure()
```

### Manual Testing
```
# Test each page:
1. Select scenario
2. Run workflow
3. Navigate to each crew page
4. Verify charts render
5. Test what-if sliders
6. Check error handling
```

### Performance Testing
```
# Benchmark targets:
- Page load: <1 second
- Chart render: <500ms
- Scenario switch: <200ms (cached)
- Slider update: <1 second (real-time calculation)
```

## Success Criteria (Phase 2)

✅ **Functional**
- All 5 crew pages display correctly
- Charts render for all scenarios
- Sliders adjust calculations in real-time
- Online mode API calls work (with API key)
- Error handling doesn't crash UI

✅ **Visual**
- Guardian branding consistent across pages
- Professional chart styling (Plotly)
- Responsive layout (works on mobile)
- Clear data hierarchy

✅ **Performance**
- Page loads <1s
- Charts render <500ms
- No memory leaks
- Caching working correctly

✅ **Testing**
- 20+ integration tests passing
- E2E tests validate workflows
- Coverage >80% for page logic

---

## Phase 2 Status: PAGES IMPLEMENTATION COMPLETE

Ready to implement:
1. ✅ **pages/02_underwriting.py** (Underwriting crew page) - COMPLETE
2. ✅ **components/charts.py** (Plotly chart wrappers) - COMPLETE (added plot_payoff_diagram)
3. ✅ **pages/03_reserves.py** (Reserve crew page with charts) - COMPLETE
4. ✅ **pages/04_hedging.py** (Hedging crew page) - COMPLETE
5. ✅ **pages/05_behavior.py** (Behavior crew page) - COMPLETE
6. ✅ **pages/06_scenarios.py** (Scenario comparison page) - COMPLETE

**Pending Phase 2 Tasks:**
- [ ] **components/metrics.py** (KPI card components - optional, using st.metric() directly)
- [ ] **components/forms.py** (Interactive form controls - optional, using st.slider() directly)
- [ ] **tests/integration/test_streamlit_foundation.py** (AppTest-based integration tests)
- [ ] **Phase 2 Polish** (Style consistency, error handling, mobile responsiveness)
- [ ] **PHASE_2_COMPLETION.md** (Completion checklist)

Would you like to proceed with Phase 3 (Polish & Testing) or add optional component libraries?
