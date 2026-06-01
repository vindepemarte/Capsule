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
<span style="color:#10b981">✓</span> Manifest loaded: capsule.yaml
<span style="color:#10b981">✓</span> Schema valid
<span style="color:#10b981">✓</span> Tools scanned: 2 found
<span style="color:#fbbf24">⚠</span> draft_reply declares write_draft
<span style="color:#10b981">✓</span> Scan completed</code>`,
        },
        {
            key: 'run',
            label: 'capsule run output',
            code: `<code>$ capsule run --input examples/refund-request.json --allow-all
<span style="color:#60a5fa">→</span> Loading capsule.yaml
<span style="color:#60a5fa">→</span> Executing agent: triage
<span style="color:#10b981">✓</span> Tool call: policy_search
<span style="color:#60a5fa">→</span> Executing agent: responder
<span style="color:#10b981">✓</span> final_reply created</code>`,
        },
        {
            key: 'test',
            label: 'capsule test output',
            code: `<code>$ capsule test
<span style="color:#60a5fa">→</span> Running refund_request.yaml
<span style="color:#10b981">✓</span> refund request routes to responder
<span style="color:#10b981">✓</span> All tests passed.</code>`,
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
        { text: '$ capsule scan ./refund-support-agent', type: 'prompt', delay: 400 },
        { text: '', type: 'info', delay: 700 },
        { text: '  Loading capsule.yaml...', type: 'info', delay: 900 },
        { text: '  ✓  Schema: valid', type: 'success', delay: 1200 },
        { text: '  ✓  name: refund-support-agent', type: 'success', delay: 1500 },
        { text: '  ✓  version: 0.1.0', type: 'success', delay: 1700 },
        { text: '  ✓  Agents: triage, responder', type: 'success', delay: 2000 },
        { text: '  ✓  Tools: policy_search, draft_reply', type: 'success', delay: 2300 },
        { text: '  ✓  policy_search — read', type: 'success', delay: 2600 },
        { text: '  ⚠  draft_reply — write_draft can modify workflow state', type: 'warn', delay: 3000 },
        { text: '  ✓  MCP declarations supported for mocked tests', type: 'success', delay: 3300 },
        { text: '  ⚠  Live MCP orchestration is still planned', type: 'warn', delay: 3600 },
        { text: '', type: 'info', delay: 4200 },
        { text: '  RESULT: COMPLETED  ✓  (1 warning, 0 errors)', type: 'output', delay: 4500 },
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
            'Can be written as a YAML string or scalar such as 0.1.0',
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
        desc: 'A named map of model configurations. Agents reference these keys through their model field so runtimes and adapters can resolve provider settings consistently.',
        validations: [
            'Must be a non-empty object',
            'Each model entry should declare provider and model',
            'Agent model references must point to one of these keys',
        ],
        impact: 'Keeps model configuration out of prompt code and makes generated adapters easier to inspect. The starter uses provider: local and model: deterministic-dev for no-key tests.',
        tip: 'Use a local deterministic model entry for fixtures and tests. Add real provider entries only when the generated runtime should call an LLM.',
    },
    agents: {
        tag: 'Runtime',
        req: 'Required',
        reqClass: '',
        title: 'agents',
        desc: 'Defines one or more named agent configurations. Each agent points to a prompt file, a model key, and the tools it may call.',
        validations: [
            'At least one agent entry required',
            'Each agent should have prompt and model',
            'Model must be declared in the top-level models object',
            'All tool references must exist in the top-level tools object',
        ],
        impact: 'Agents are the reusable execution roles used by workflow steps. Capsule validates prompt paths, model references, and tool cross-references.',
        tip: 'Use separate agents for distinct reasoning roles (e.g., "planner" and "executor") rather than one monolithic agent.',
    },
    tools: {
        tag: 'Runtime',
        req: 'Optional',
        reqClass: 'optional',
        title: 'tools',
        desc: 'Declares Python or MCP tools available to agents. Python tools use an entrypoint in the form path/to/file.py:function_name plus a permission label.',
        validations: [
            'Each Python tool must declare type: python and entrypoint',
            'Source file must exist and expose the named callable',
            'Permission labels are scanned and enforced by the local runtime',
        ],
        impact: 'Tools are Capsule\'s capability boundary. Risky permissions such as write_draft are surfaced by capsule scan before execution.',
        tip: 'Keep tool permissions small and explicit. Use mocked tool responses in tests for deterministic routing checks.',
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
    workflow: {
        tag: 'Runtime',
        req: 'Required',
        reqClass: '',
        title: 'workflow',
        desc: 'Defines the executable graph: the start step, each step id, step type, agent binding, branching rules, human gates, and final output step.',
        validations: [
            'Must declare a start step',
            'Every referenced next step must exist',
            'Agent steps must reference declared agents',
            'Branch labels route to valid step ids',
        ],
        impact: 'The workflow becomes the framework-neutral Capsule Graph. Local runs, tests, bundles, and compiler adapters all derive behavior from this graph.',
        tip: 'Use capsule graph to inspect the normalized graph before compiling to LangGraph, CrewAI, or OpenAI Agents.',
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
