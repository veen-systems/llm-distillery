"""
AI Engineering Practice Pre-Filter v1.1

ALLOWLIST APPROACH: Articles must mention BOTH:
1. AI tools/technologies (Copilot, LLM, ChatGPT, agentic workflows, etc.)
2. Engineering/development context (developer, engineer, CAD, PCB, embedded, etc.)

This is different from other filters that use blocklists.
Most random articles are NOT about AI in engineering, so we require positive signals.

Purpose: Reduce LLM costs by filtering out irrelevant content before oracle scoring.

v1.1 Changes (based on Gemini feedback):
- Expanded to cover ALL engineering domains (ME, EE, Embedded, not just software)
- Added 2025 AI tools and agentic patterns for future-proofing
- Removed fluid dynamics/thermodynamics from blocklist (these ARE engineering)
- Strengthened academic paper detection
- Expanded exception patterns for multi-domain practice insights
"""

import re
from typing import Dict, Tuple, List

from filters.common.base_prefilter import BasePreFilter


class AIEngineeringPracticePreFilterV1(BasePreFilter):
    """Fast rule-based pre-filter requiring AI + engineering context"""

    VERSION = "1.1"

    # =========================================================================
    # REQUIRED: AI/ML TOOL INDICATORS
    # Article must mention at least one of these
    # =========================================================================

    AI_TOOL_KEYWORDS = [
        # === SOFTWARE/CODING AI TOOLS ===
        # Established coding assistants
        'copilot', 'github copilot', 'codewhisperer', 'tabnine',
        'sourcegraph', 'continue.dev', 'aider',

        # 2025 "Pro" coding tools
        'cursor', 'windsurf', 'zed ai', 'cline', 'qodo', 'codium',
        'augment code', 'claude code', 'cody', 'replit agent', 'bolt.new',

        # LLMs used as tools
        'chatgpt', 'gpt-4', 'gpt4', 'gpt-4o', 'claude', 'gemini', 'llama',
        'deepseek', 'mistral', 'qwen',
        'using chatgpt', 'using claude', 'using gpt',

        # AI coding terms
        'ai coding', 'ai-assisted coding', 'ai pair programming',
        'ai code generation', 'ai code review', 'ai-generated code',
        'llm-assisted', 'code generation tool', 'ai autocomplete',
        'vibe coding',

        # === 2025 AGENTIC AI PATTERNS ===
        # Shift from "chat" to "agents"
        'agentic ai', 'ai agents', 'ai agent', 'autonomous agent',
        'multi-agent system', 'agentic workflow', 'agent framework',
        'inference-time compute', 'reasoning model',

        # === MECHANICAL/PHYSICAL ENGINEERING AI ===
        # CAD/CAM/CAE vendors with AI
        'matlab ai', 'simulink ai', 'mathworks ai',
        'siemens ai', 'siemens nx', 'siemens plm',
        'ansys ai', 'ansys simai', 'ansys simulation',
        'autodesk ai', 'fusion 360 ai', 'autocad ai',
        'solidworks ai', 'catia ai', 'ptc ai', 'creo ai',

        # 2025 Mechanical/Physical AI tools
        'bananaz ai', 'leo ai', 'monolith ai', 'neural concept',
        'physicsai', 'physics-ai',

        # AI in physical engineering domains
        'generative design', 'ai-assisted design', 'ai design',
        'ai simulation', 'ai-powered simulation',
        'digital twin ai', 'ai digital twin',
        'predictive maintenance ai', 'ai maintenance',
        'ai manufacturing', 'ai in manufacturing',
        'ai robotics', 'ai automation',
        'prompt-to-cad', 'text-to-cad',

        # === PHYSICS-AI CONVERGENCE (2025) ===
        'physics-ml', 'physics-informed', 'pinn', 'piml',
        'neural pde', 'surrogate model', 'surrogate modeling',
        'reduced order model', 'rom ai',

        # === EDA / CHIP DESIGN AI ===
        'dso.ai', 'cadence cerebrus', 'verdi ai',
        'ai-driven eda', 'auto-routing', 'ai routing',
        'hardware-software co-design',

        # === ROBOTICS / EMBODIED AI ===
        'deepfleet', 'end-to-end learning', 'embodied ai',
        'robot learning', 'sim-to-real',

        # === GENERAL AI TERMS (combined with engineering context) ===
        'artificial intelligence', 'machine learning',
        'ai tool', 'ai tools', 'ai assistant', 'ai assistants',
        'llm', 'large language model',
        'generative ai', 'genai', 'gen ai',
        'neural network', 'deep learning',
    ]

    AI_TOOL_PATTERNS = [
        # Tool usage patterns (verb-based for future-proofing)
        r'\b(using|with|leveraging|integrating)\s+(ai|ml|chatgpt|copilot|claude|gpt|llm)\b',
        r'\b(ai|ml|llm)[\s-]+(assisted|powered|driven|enabled|based|augmented)\b',
        r'\b(ai|ml|llm)\s+(tool|assistant|system|platform|agent)\b',

        # Agentic patterns (2025 trend)
        r'\b(agentic|autonomous)\s+(workflow|system|agent|pipeline)\b',
        r'\b(multi-agent|multiagent)\s+(system|architecture|framework)\b',

        # Engineering + AI combinations
        r'\b(engineer|engineering|design|simulation|cad|cam|cae|eda)\s+(with|using)\s+(ai|ml|llm)\b',
        r'\b(ai|ml)\s+(in|for)\s+(engineering|design|manufacturing|simulation|hardware)\b',
        r'\bgenerative\s+(design|engineering|ai)\b',

        # Developer/engineer productivity
        r'\b(developer|engineer)\s+(productivity|experience|workflow)\s+(with|using)?\s*(ai|ml|llm|copilot)?\b',

        # Studies about AI tool usage
        r'\b(study|survey|research)\s+(of|on)\s+(developers?|engineers?)\s+(using|with)\b',

        # Physics-AI patterns
        r'\bphysics[\s-]+(informed|guided|constrained)\s+(neural|ml|ai)\b',
        r'\b(neural|ai|ml)\s+(surrogate|emulator)\b',
    ]

    # =========================================================================
    # REQUIRED: ENGINEERING/DEVELOPMENT CONTEXT
    # Article must also mention at least one of these
    # =========================================================================

    ENGINEERING_KEYWORDS = [
        # === SOFTWARE ENGINEERING ===
        # Roles
        'developer', 'developers', 'engineer', 'engineers', 'programmer', 'programmers',
        'software engineer', 'software developer', 'coder', 'coders',
        'devops', 'sre', 'data engineer', 'ml engineer', 'mlops',

        # Activities
        'coding', 'programming', 'software development', 'code review',
        'debugging', 'testing', 'refactoring', 'deployment',
        'pull request', 'code commit', 'git', 'version control',

        # Domains
        'software engineering', 'frontend', 'backend', 'full stack', 'fullstack',
        'web development', 'mobile development', 'app development',

        # Tools/environments
        'ide', 'vscode', 'visual studio', 'jetbrains', 'intellij',
        'pycharm', 'vim', 'neovim', 'emacs',

        # Processes
        'agile', 'scrum', 'sprint', 'ci/cd', 'workflow',

        # === PHYSICAL/MECHANICAL ENGINEERING ===
        'cad', 'cam', 'cae', 'fea', 'cfd', 'pdm', 'plm',
        'solidworks', 'ansys', 'autodesk', 'fusion 360', 'creo', 'nx',
        'topology optimization', 'finite element', 'finite element analysis',
        'structural engineering', 'thermal analysis', 'mechanical engineering',
        'fluid dynamics', 'cfd simulation', 'aerodynamics',
        'manufacturing', 'additive manufacturing', '3d printing',

        # === ELECTRICAL/HARDWARE ENGINEERING ===
        'pcb', 'schematic', 'vlsi', 'eda', 'fpga', 'asic',
        'hdl', 'verilog', 'vhdl', 'systemverilog',
        'circuit design', 'signal integrity', 'chip design',
        'spice', 'kicad', 'altium', 'cadence', 'synopsys',
        'electrical engineering', 'electronics',

        # === EMBEDDED/SYSTEMS ENGINEERING ===
        'embedded systems', 'firmware', 'microcontroller', 'rtos',
        'soc', 'system-on-chip', 'hmi', 'iot',
        'mechatronics', 'control systems', 'plc', 'sensors',
        'mbse', 'systems engineering', 'v-model',
        'robotics', 'automation',

        # === PROFESSIONAL ARTIFACTS ===
        'requirements', 'specification', 'bill of materials', 'bom',
        'compliance', 'safety-critical', 'technical debt', 'legacy system',
        'prototype', 'prototyping', 'benchmarking',
        'iso', 'iec', 'do-178', 'iso 26262',
    ]

    ENGINEERING_PATTERNS = [
        # Software development
        r'\b(software|web|mobile|app)\s+(development|engineering)\b',
        r'\b(code|coding)\s+(practice|workflow|process)\b',
        r'\bdeveloper\s+(productivity|experience|tools)\b',
        r'\bengineering\s+(team|practice|workflow)\b',

        # Design & Simulation
        r'\b(design|simulation|modeling)\s+(workflow|verification|validation)\b',
        r'\b(structural|thermal|fluid|mechanical)\s+analysis\b',

        # Hardware/Firmware specifics
        r'\b(pcb|chip|circuit)\s+(layout|routing|design)\b',
        r'\b(embedded|firmware|hardware)\s+development\b',

        # Industrial Scale
        r'\b(manufacturing|production|industrial)\s+(automation|process)\b',
        r'\b(safety|mission|life|security)[\s-]critical\b',

        # Methodology
        r'\b(digital\s+twin|predictive\s+maintenance)\b',
        r'\b(requirements|systems)\s+engineering\b',
        r'\b(technical|engineering)\s+specification\b',
    ]

    # =========================================================================
    # BLOCKLIST: Obviously irrelevant domains
    # NOTE: arxiv is NOT blocked - it contains valuable research on AI practices!
    # NOTE: fluid dynamics/thermodynamics NOT blocked - they ARE engineering!
    # =========================================================================

    BLOCKED_DOMAINS = [
        # Biology/medicine research (not about AI tools)
        'biorxiv.org',
        'medrxiv.org',

        # Finance/business news
        'bloomberg.com',
        'reuters.com/markets',
        'wsj.com',
        'ft.com',

        # Consumer tech reviews
        'gsmarena.com',
        'phonearena.com',
        'notebookcheck.net',
    ]

    # =========================================================================
    # BLOCKLIST: Irrelevant topics
    # NOTE: Removed fluid dynamics/thermodynamics - these ARE engineering contexts!
    # =========================================================================

    IRRELEVANT_PATTERNS = [
        # Pure science (NOT engineering applications)
        r'\b(quantum\s+mechanics|quantum\s+physics|molecular\s+biology|cellular\s+biology)\b',
        r'\b(protein folding|gene expression|neural pathway|genomics|proteomics)\b',

        # Finance/business
        r'\b(stock|shares|dividend|ipo|acquisition|merger)\b',
        r'\b(quarterly earnings|revenue growth|market cap)\b',

        # Sports/entertainment
        r'\b(championship|tournament|playoffs|concert|album)\b',

        # Politics/general news
        r'\b(election|parliament|congress|legislation|vote)\b',
        r'\b(president|minister|senator|governor)\b',

        # Military (focus on action/warfare, not defense engineering)
        r'\b(battlefield|combat|warfare|lethal autonomous)\b',
        r'\b(target engagement|weapon system|military operations)\b',

        # Medical (AI applied TO medicine, not AI tools FOR engineers)
        r'\b(cardiovascular|patient outcomes|clinical trial)\b',
        r'\b(diagnosis|prognosis|treatment plan)\b',
        r'\b(drug discovery|gene therapy)\b',
    ]

    # =========================================================================
    # BLOCKLIST: Pure ML/AI research papers (not about tool usage)
    # These patterns indicate academic ML research, not practitioner content
    # =========================================================================

    ML_RESEARCH_PATTERNS = [
        # arXiv paper indicators
        r'arxiv:\d+\.\d+',  # arXiv ID
        r'arXiv:\d+',  # Alternative format
        r'announce type:\s*(new|replace)',  # arXiv announcement
        r'\babstract:\s',  # Academic abstract

        # Academic paper language
        r'\bwe (propose|present|introduce|develop)\s+(a|an|the)\s+(novel|new|framework|method|approach|model|algorithm)\b',
        r'\bour (method|approach|model|framework|algorithm|contribution)\b',
        r'\b(state-of-the-art|sota)\b',
        r'\b(benchmark|baseline|ablation)\s+(study|experiment|result)\b',
        r'\b(loss function|gradient descent|backpropagation|convergence|epoch)\b',
        r'\b(training|testing|validation)\s+(set|data|split|accuracy|loss)\b',

        # Academic citation/format indicators
        r'\bet\s+al\.',  # Citations
        r'\b(Figure|Table|Fig\.)\s+\d+[:\s]',  # Paper figures/tables
        r'\bnovel\s+architecture\b',
        r'\bproposed\s+(method|approach|framework|architecture)\b',

        # Model creation vs tool usage
        r'\b(open[\s-]source\s+dataset|pre[\s-]training\s+data)\b',
        r'\b(model\s+weights|model\s+parameters|checkpoint)\b',

        # Pure ML research topics
        r'\b(federated learning|reinforcement learning from human feedback|rlhf)\b',
        r'\b(attention mechanism|transformer architecture|self-attention)\b',
        r'\b(fine-tuning|pre-training|embeddings|tokenization)\b',
    ]

    # =========================================================================
    # EXCEPTIONS: Allow despite blocklist
    # These are the "gold mine" - bridges between academia and practice
    # =========================================================================

    EXCEPTION_PATTERNS = [
        # --- Human-Tool Interaction Studies ---
        r'\b(developer|programmer|engineer)\s+(survey|study|interview|observation)\b',
        r'\b(pair\s+programming|collaborative\s+design|human[\s-]ai)\s+(workflow|experiment|interaction)\b',

        # --- Adoption & Productivity Metrics ---
        r'\b(copilot|chatgpt|claude|gemini|cursor|llm)\s+(usage|adoption|productivity|velocity|efficiency)\b',
        r'\b(benchmarking|evaluation)\s+of\s+(ai|llm)\s+in\s+(engineering|design|development|production)\b',

        # --- Practice-Based Insights (must have AI context) ---
        r'\b(lessons\s+learned|best\s+practices|case\s+study|post[\s-]mortem)\s+(for|with|using|from)\s+(ai|llm|copilot|chatgpt)\b',
        r'\b(ai|llm|copilot)\s+(lessons\s+learned|best\s+practices|case\s+study)\b',
        r'\bhow\s+we\s+(integrated|use|adopted)\s+(ai|llm)\b',
        r'\b(pipeline|workflow|toolchain)\s+(with|using)\s+(ai|llm)\b',

        # --- Technical Implementation (V-Model Bridge) ---
        r'\b(verification|validation|unit\s+test|quality\s+assurance)\s+(with|using)\s+(ai|llm)\b',
        r'\bai[\s-]assisted\s+(topology\s+optimization|circuit\s+design|code\s+refactoring|design)\b',

        # --- Coding assistant specific studies ---
        r'\b(coding\s+assistant|code\s+completion)\s+(study|evaluation|comparison)\b',
        r'\b(ai|llm)[\s-]assisted\s+(coding|programming|development)\b',

        # --- Defense/Aerospace Engineering (not warfare) ---
        r'\b(digital\s+twin|predictive\s+maintenance|fleet\s+management)\b',
    ]

    def __init__(self):
        # Compile patterns for efficiency
        self._ai_patterns = [re.compile(p, re.IGNORECASE) for p in self.AI_TOOL_PATTERNS]
        self._eng_patterns = [re.compile(p, re.IGNORECASE) for p in self.ENGINEERING_PATTERNS]
        self._irrelevant_patterns = [re.compile(p, re.IGNORECASE) for p in self.IRRELEVANT_PATTERNS]
        self._ml_research_patterns = [re.compile(p, re.IGNORECASE) for p in self.ML_RESEARCH_PATTERNS]
        self._exception_patterns = [re.compile(p, re.IGNORECASE) for p in self.EXCEPTION_PATTERNS]

    def apply_filter(self, article: Dict) -> Tuple[bool, str]:
        """
        Determine if article should be sent to oracle for scoring.

        ALLOWLIST APPROACH: Must have BOTH AI tool AND engineering context.

        Flow:
        1. Validate structure and length
        2. Check exceptions (always allow if matched)
        3. Check blocked domains
        4. Check irrelevant topics
        5. REQUIRE: AI tool mention
        6. REQUIRE: Engineering context
        7. BLOCK: Pure ML research papers

        Args:
            article: Dict with 'title', 'content', 'url', etc.

        Returns:
            (should_score, reason)
            - (True, "passed"): Send to oracle
            - (False, "reason"): Block with reason string
        """
        # Validate structure
        is_valid, reason = self.validate_article(article)
        if not is_valid:
            return (False, reason)

        # NO length check here (#93, removed 2026-08-13). The 300-char floor is a
        # LABELLING-time precondition — its rationale is framework leakage in the
        # oracle *prompt*, and the student sees no prompt — so it lives in
        # `ground_truth.batch_scorer.make_oracle_prefilter` and nowhere in a
        # scoring path. This was the last surviving `check_content_length` call
        # inside an `apply_filter` in the repo; #93 removed the others on
        # 2026-08-03 and this package was missed because it is a separate
        # product and not in ACTIVE_FILTERS. Behaviour on the oracle path is
        # UNCHANGED: the wrapper applies the same floor via BasePreFilter.
        # `validate_article` above stays — empty is not short.

        # Get combined text for analysis
        text = self._get_combined_clean_text(article)
        url = article.get('url', '').lower()

        # Check for exceptions first (always allow - these are high-value)
        if self._has_exception(text):
            return (True, "exception_practice_study")

        # Check blocked domains
        for domain in self.BLOCKED_DOMAINS:
            if domain in url:
                return (False, f"blocked_domain_{domain.replace('.', '_')}")

        # Check irrelevant topics
        if self._has_irrelevant_topic(text):
            return (False, "irrelevant_topic")

        # REQUIRE: AI tool mention
        has_ai = self._has_ai_mention(text)
        if not has_ai:
            return (False, "missing_ai_context")

        # REQUIRE: Engineering context
        has_eng = self._has_engineering_context(text)
        if not has_eng:
            return (False, "missing_engineering_context")

        # BLOCK: Pure ML research papers (even if they mention AI+engineering)
        # Exception patterns already checked above, so this only blocks non-exceptions
        if self._is_ml_research(text):
            return (False, "ml_research_paper")

        # Both required signals present, not blocked
        return (True, "passed_ai_engineering")

    def _has_ai_mention(self, text: str) -> bool:
        """Check if text mentions AI tools/technologies"""
        # Check keywords
        if self.has_any_keyword(text, self.AI_TOOL_KEYWORDS):
            return True
        # Check patterns
        if self.has_any_pattern(text, self._ai_patterns):
            return True
        return False

    def _has_engineering_context(self, text: str) -> bool:
        """Check if text has engineering/development context"""
        # Check keywords
        if self.has_any_keyword(text, self.ENGINEERING_KEYWORDS):
            return True
        # Check patterns
        if self.has_any_pattern(text, self._eng_patterns):
            return True
        return False

    def _has_irrelevant_topic(self, text: str) -> bool:
        """Check if text is about obviously irrelevant topics"""
        return self.has_any_pattern(text, self._irrelevant_patterns)

    def _has_exception(self, text: str) -> bool:
        """Check if text matches exception patterns (always allow)"""
        return self.has_any_pattern(text, self._exception_patterns)

    def _is_ml_research(self, text: str) -> bool:
        """Check if text is a pure ML research paper (not about tool usage)"""
        return self.has_any_pattern(text, self._ml_research_patterns)


# For backwards compatibility and dynamic loading
PreFilter = AIEngineeringPracticePreFilterV1
