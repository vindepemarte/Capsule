// ===========================
// Capsule Site — Main JS
// ===========================

// ===========================
// 1. SCROLL REVEAL
// ===========================
(function () {
    const revealObserver = new IntersectionObserver(
        (entries) => {
            entries.forEach((entry) => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('visible');
                    revealObserver.unobserve(entry.target);
                }
            });
        },
        { threshold: 0.12, rootMargin: '0px 0px -40px 0px' }
    );

    document.querySelectorAll('.reveal').forEach((el) => revealObserver.observe(el));
})();

// ===========================
// 2. COMPILER SIMULATOR — TARGET ROTATION
// ===========================
(function () {
    const targets = document.querySelectorAll('.target-node');
    const codePreview = document.getElementById('sim-code-preview');

    const states = [
        {
            key: 'scan',
            label: 'capsule scan output',
            code: `<code>$ capsule scan
<span style="color:#10b981">✓</span> Manifest loaded: my_agent/capsule.yaml
<span style="color:#10b981">✓</span> Schema valid
<span style="color:#10b981">✓</span> Models declared: gemini-1.5-pro
<span style="color:#10b981">✓</span> Tools scanned: 3 found, 0 unsafe
<span style="color:#fbbf24">⚠</span> No input_schema defined — optional
<span style="color:#10b981">✓</span> PASSED (1 warning, 0 errors)</code>`,
        },
        {
            key: 'run',
            label: 'capsule run output',
            code: `<code>$ capsule run --input '{"order_id":"ORD-42"}'
<span style="color:#60a5fa">→</span> Loading capsule.yaml
<span style="color:#60a5fa">→</span> Resolving model: gemini-2.0-flash
<span style="color:#60a5fa">→</span> Executing agent: main
<span style="color:#10b981">✓</span> Tool call: check_order_status → OK
<span style="color:#10b981">✓</span> Tool call: process_refund → OK
<span style="color:#10b981">✓</span> Done — refund approved</code>`,
        },
        {
            key: 'test',
            label: 'capsule test output',
            code: `<code>$ capsule test
<span style="color:#60a5fa">→</span> Running 3 test cases...
<span style="color:#10b981">✓</span> [1/3] order_found.yaml → PASS
<span style="color:#10b981">✓</span> [2/3] order_not_found.yaml → PASS
<span style="color:#10b981">✓</span> [3/3] refund_denied.yaml → PASS
<span style="color:#10b981">✓</span> All tests passed in 0.42s</code>`,
        },
    ];

    let current = 0;

    if (!targets.length || !codePreview) return;

    function activate(idx) {
        targets.forEach((t, i) => {
            t.classList.toggle('active', i === idx);
        });

        const state = states[idx];
        const previewLang = document.querySelector('.preview-lang');
        if (previewLang) previewLang.textContent = state.label;

        codePreview.style.animation = 'none';
        void codePreview.offsetHeight; // reflow
        codePreview.style.animation = '';
        codePreview.innerHTML = state.code;
    }

    setInterval(() => {
        current = (current + 1) % states.length;
        activate(current);
    }, 2800);
})();

// ===========================
// 3. ANIMATED TERMINAL
// ===========================
(function () {
    const terminalBody = document.getElementById('terminal-body');
    if (!terminalBody) return;

    const lines = [
        { text: '$ capsule scan ./agents/refund-support-agent', type: 'prompt', delay: 400 },
        { text: '', type: 'info', delay: 700 },
        { text: '  Loading capsule.yaml...', type: 'info', delay: 900 },
        { text: '  ✓  Schema: valid', type: 'success', delay: 1200 },
        { text: '  ✓  name: refund-support-agent', type: 'success', delay: 1500 },
        { text: '  ✓  version: 1.0.0', type: 'success', delay: 1700 },
        { text: '  ✓  Models declared: gemini-2.0-flash', type: 'success', delay: 2000 },
        { text: '  ✓  Agents: 1 valid', type: 'success', delay: 2300 },
        { text: '  ✓  Tools: 3 found — scanning...', type: 'success', delay: 2600 },
        { text: '  ✓  check_order_status — SAFE', type: 'success', delay: 3000 },
        { text: '  ✓  process_refund — SAFE', type: 'success', delay: 3300 },
        { text: '  ✓  notify_customer — SAFE', type: 'success', delay: 3600 },
        { text: '  ⚠  input_schema not declared — optional field', type: 'warn', delay: 4000 },
        { text: '', type: 'info', delay: 4200 },
        { text: '  RESULT: PASSED  ✓  (1 warning, 0 errors)', type: 'output', delay: 4500 },
    ];

    let started = false;

    const observer = new IntersectionObserver(
        (entries) => {
            if (entries[0].isIntersecting && !started) {
                started = true;
                observer.disconnect();

                lines.forEach(({ text, type, delay }) => {
                    setTimeout(() => {
                        const el = document.createElement('div');
                        el.className = `line ${type}`;
                        el.innerHTML =
                            type === 'prompt'
                                ? `<span class="cmd-prompt">$</span>${text.replace(/^\$\s*/, '')}`
                                : text || '&nbsp;';

                        // Always append — flex-direction:column + justify-content:flex-end
                        // means new lines appear at bottom, old ones disappear off the top
                        terminalBody.appendChild(el);

                        // Trigger slide-in
                        requestAnimationFrame(() => {
                            requestAnimationFrame(() => el.classList.add('typed'));
                        });
                    }, delay);
                });
            }
        },
        { threshold: 0.3 }
    );

    observer.observe(terminalBody);
})();

// ===========================
// 4. QUICKSTART TABS
// ===========================
function switchTab(event, tabId) {
    if (event) event.preventDefault();

    document.querySelectorAll('.tab-btn').forEach((btn) => {
        btn.classList.remove('active');
        btn.setAttribute('aria-selected', 'false');
    });
    document.querySelectorAll('.tab-pane').forEach((pane) => {
        pane.classList.remove('active');
    });

    const targetBtn = document.getElementById(`tab-${tabId}`);
    const targetPane = document.getElementById(`pane-${tabId}`);

    if (targetBtn) {
        targetBtn.classList.add('active');
        targetBtn.setAttribute('aria-selected', 'true');
    }
    if (targetPane) targetPane.classList.add('active');
}

// ===========================
// 5. COPY CODE BUTTON
// ===========================
function copyCode(btn) {
    const pane = btn.closest('.tab-pane') || btn.closest('.qs-content');
    const pre = pane ? pane.querySelector('pre') : null;
    if (!pre) return;

    const text = pre.innerText;
    navigator.clipboard.writeText(text).then(() => {
        const original = btn.textContent;
        btn.textContent = 'Copied!';
        btn.style.color = '#10b981';
        setTimeout(() => {
            btn.textContent = original;
            btn.style.color = '';
        }, 2000);
    });
}

// ===========================
// 6. SPEC EXPLORER
// ===========================
const SPEC_DATA = {
    name: {
        tag: 'Identity',
        req: 'Required',
        reqClass: '',
        title: 'name',
        desc: 'A unique slug identifier for this agent capsule. Used in CLI output, logs, and when referencing this agent as a sub-agent from another capsule.',
        validations: [
            'Must be a non-empty string',
            'No spaces — use hyphens or underscores',
            'Must be unique within your project',
        ],
        impact: 'Shown in all CLI output, scan reports, and used as the registry key when agents reference sub-agents. A bad name causes routing failures in pipelines.',
        tip: 'Match the name to your directory name for maximum clarity. E.g., folder <code style="font-family:monospace;font-size:12px">refund-agent/</code> → name: <code style="font-family:monospace;font-size:12px">refund-agent</code>.',
    },
    version: {
        tag: 'Identity',
        req: 'Required',
        reqClass: '',
        title: 'version',
        desc: 'Semantic version string for this capsule. Enables changelogs, rollback references, and version-locked sub-agent dependencies.',
        validations: [
            'Must follow semver format: MAJOR.MINOR.PATCH',
            'Should be a quoted string in YAML: "1.0.0"',
            'Increment MAJOR for breaking agent contract changes',
        ],
        impact: 'Version mismatches between parent and sub-agent capsules are flagged during scan. Critical for reproducible deployments.',
        tip: 'Start at <code style="font-family:monospace;font-size:12px">"0.1.0"</code> during development and bump to <code style="font-family:monospace;font-size:12px">"1.0.0"</code> when the agent\'s I/O contract is stable.',
    },
    description: {
        tag: 'Metadata',
        req: 'Optional',
        reqClass: 'optional',
        title: 'description',
        desc: 'A human-readable explanation of what this agent does. Used in registry listings, team documentation, and security review reports.',
        validations: [
            'Free-form string or multi-line YAML block (> syntax)',
            'No validation constraints beyond non-empty if present',
        ],
        impact: 'Improves team discoverability and appears in automated security audits. Agents without descriptions fail documentation completeness checks.',
        tip: 'Write this like a one-line pitch: "Processes customer refund requests and determines eligibility based on order status."',
    },
    models: {
        tag: 'Runtime',
        req: 'Required',
        reqClass: '',
        title: 'models',
        desc: 'The allowlist of LLM model identifiers permitted for use in this capsule. Any model not declared here is blocked at runtime — even if coded into an agent.',
        validations: [
            'Must be a non-empty list of strings',
            'At least one model identifier required',
            'Model IDs must match provider format (e.g. gemini-2.0-flash)',
        ],
        impact: 'Prevents unauthorized model usage. If a model not in this list is called at runtime, Capsule raises a SecurityError before any token is spent.',
        tip: 'List every model your agents use — including fallback models. Undeclared models will always fail, even in dev mode.',
    },
    agents: {
        tag: 'Runtime',
        req: 'Required',
        reqClass: '',
        title: 'agents',
        desc: 'Defines one or more agent configurations. Each agent has a name, a system prompt file, a model, and a list of tool references it may call.',
        validations: [
            'At least one agent entry required',
            'Each agent must have: name, prompt (file path), model',
            'Model must be declared in the top-level models list',
            'All tool references must exist in the top-level tools list',
        ],
        impact: 'The agent list is the core routing map. Misconfigured agents cause silent tool-call failures at runtime. Capsule validates all cross-references at scan time.',
        tip: 'Use separate agents for distinct reasoning roles (e.g., "planner" and "executor") rather than one monolithic agent.',
    },
    tools: {
        tag: 'Runtime',
        req: 'Optional',
        reqClass: 'optional',
        title: 'tools',
        desc: 'Declares Python functions as tools available to agents. Each entry points to a source file and function name that Capsule will load and wrap.',
        validations: [
            'Each tool must have: name, source (file path), function (name)',
            'Source file must exist and be importable',
            'Function must accept typed arguments for schema inference',
        ],
        impact: 'Tools not declared here cannot be used by agents, even if coded directly. This is the enforcement boundary for capability control.',
        tip: 'Annotate tool functions with Python type hints — Capsule uses them to auto-generate JSON schema for the LLM.',
    },
    input_schema: {
        tag: 'Contract',
        req: 'Optional',
        reqClass: 'optional',
        title: 'input_schema',
        desc: 'A JSON Schema definition for the input your agent accepts. When present, Capsule validates every invocation against this schema before the agent runs.',
        validations: [
            'Must be a valid JSON Schema object (type: object)',
            'Properties and required fields follow JSON Schema spec',
            'Nested schemas supported',
        ],
        impact: 'Prevents invalid inputs from reaching the LLM, reducing wasted tokens and obscure failures. Required for agents exposed as APIs.',
        tip: 'Even a minimal schema (just defining the top-level type) is enough to catch most bad inputs early.',
    },
    secrets: {
        tag: 'Security',
        req: 'Optional',
        reqClass: 'optional',
        title: 'secrets',
        desc: 'Declares the names of environment variables this agent requires at runtime. Capsule validates that all listed secrets are present before agent execution begins.',
        validations: [
            'List of non-empty strings (env var names)',
            'Values are never stored in the capsule — only names',
            'All declared secrets must be set in environment at runtime',
        ],
        impact: 'Agents fail fast with a clear error if a secret is missing, rather than crashing mid-execution with a cryptic API error.',
        tip: 'Never put actual secret values in capsule.yaml. Use a .env file locally and inject via CI/CD in production.',
    },
};

(function initSpecExplorer() {
    const keys = document.querySelectorAll('.yaml-key.clickable');
    if (!keys.length) return;

    function updatePanel(key) {
        const data = SPEC_DATA[key];
        if (!data) return;

        document.getElementById('info-tag').textContent = data.tag;

        const req = document.getElementById('info-req');
        req.textContent = data.req;
        req.className = 'info-requirement' + (data.reqClass ? ` ${data.reqClass}` : '');

        document.getElementById('info-key-title').textContent = data.title;
        document.getElementById('info-desc').textContent = data.desc;

        const valList = document.getElementById('info-validation');
        valList.innerHTML = data.validations.map((v) => `<li>${v}</li>`).join('');

        document.getElementById('info-impact').textContent = data.impact;
        document.getElementById('spec-tip').innerHTML = data.tip;
    }

    keys.forEach((el) => {
        el.addEventListener('click', () => {
            keys.forEach((k) => k.classList.remove('active'));
            el.classList.add('active');
            updatePanel(el.dataset.key);
        });
    });
})();
