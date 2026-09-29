# Strategic Decisions Log

## 2025-11-17: Pivot from Deployment to Innovation Focus

**DECISION**: Pivot primary focus from `sustainability_tech_deployment` to `sustainability_tech_innovation`

**Context:**
- sustainability_tech_deployment v3 has 0% false positive rate (PRODUCTION READY)
- However, v3's tight prefilter (99% block rate) results in severe data scarcity
- From 151k raw articles, only ~1,500 scored articles available
- Other filters trained on ~7k articles, 1.5k is only 20% of target

**Rationale:**
1. **Data availability**: Innovation filter will have much higher pass rate → more training data
2. **Narrative value**: "Climate innovation is accelerating" is still powerful and actionable
3. **Broader scope**: Includes R&D, pilots, early-stage tech, AND deployment
4. **Feasibility**: Can actually train a good model with available data

**Deployment narrative preserved for future:**
- Deployment narrative ("Climate tech works TODAY") is MORE POWERFUL when provable
- Keep v3 prefilter running in production to accumulate deployment-specific data
- When sufficient deployment data accumulated (5k+ articles), train deployment model
- Innovation model trains NOW, deployment model trains LATER

**Discovery: Innovation Filter Exists But Broken**

After decision to pivot, discovered `sustainability_tech_innovation/v1` exists but **FAILED validation** (2025-11-15):
- Status: NOT PRODUCTION READY ❌
- False positive rate: 85.7% (target <10%)
- Pass rate: 2.3% (target 5-20%)
- Critical issues: Gatekeeper not enforced, oracle confuses proposals with pilots

**Final Decision (2025-11-17): Two-Track Approach**

1. **Deployment v3: Production deployment for data accumulation**
   - Status: PRODUCTION READY (0% FP rate, 98% block rate)
   - Deploy to production pipeline immediately
   - Accumulate clean deployment data over 10-12 months (target: 5k+ articles)
   - Train deployment model in Q4 2025 when data sufficient
   - Documentation: `filters/sustainability_tech_deployment/v3/DEPLOYMENT_STRATEGY.md` <!-- placeholder -->

2. **Innovation v1: Fix and train NOW**
   - Status: BROKEN (85.7% FP rate, 2.3% pass rate)
   - Fix critical issues (gatekeeper enforcement, prefilter rewrite)
   - Validate fixes and achieve production readiness
   - Score and train model immediately (target: 5k+ articles)
   - Focus: Pilots + validated research + deployed tech

**Action items:**
1. ✅ Stop current v3 scoring (data scarcity identified)
2. ✅ Document v3 deployment strategy
3. ⏳ Fix innovation v1 critical issues (gatekeeper, prefilter, prompt)
4. ⏳ Validate fixed innovation v1
5. ⏳ Score and train innovation model
6. ⏳ Deploy both filters to production (parallel operation)

**Expected outcomes:**
- Innovation model: Trainable NOW (after fixes) with 5k+ scored articles
- Deployment model: Trainable Q4 2025 after data accumulation
- Best of both worlds: Immediate innovation tracking + future deployment proof
- Complementary narratives: "Innovation accelerating" + "Tech works TODAY"
