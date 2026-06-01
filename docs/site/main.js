// Capsule Documentation Interactive Logic

// 1. Quickstart Tab Switcher
function switchTab(event, tabId) {
    // Prevent default click
    if (event) event.preventDefault();

    // Get all tab buttons and panes
    const buttons = document.querySelectorAll('.tab-btn');
    const panes = document.querySelectorAll('.tab-pane');

    // Remove active class from all buttons and panes
    buttons.forEach(btn => btn.classList.remove('active'));
    panes.forEach(pane => pane.classList.remove('active'));

    // Add active class to selected elements
    if (event) {
        event.currentTarget.classList.add('active');
    } else {
        // Fallback if called programmatically
        const targetBtn = Array.from(buttons).find(btn => btn.getAttribute('onclick').includes(tabId));
        if (targetBtn) targetBtn.classList.add('active');
    }
    
    const activePane = document.getElementById(tabId);
    if (activePane) activePane.classList.add('active');
}

// 2. Copy Text Helper
function copyText(text) {
    navigator.clipboard.writeText(text).then(() => {
        // Find copy button and show feedback
        const btn = event ? event.currentTarget : null;
        if (btn) {
            const originalText = btn.textContent;
            btn.textContent = 'Copied!';
            btn.style.borderColor = 'var(--color-success)';
            btn.style.color = 'var(--color-success)';
            setTimeout(() => {
                btn.textContent = originalText;
                btn.style.borderColor = '';
                btn.style.color = '';
            }, 1500);
        }
    }).catch(err => {
        console.error('Failed to copy text: ', err);
    });
}

// 3. Spec Explorer Data
const specData = {
    name: {
        title: "name",
        type: "string",
        requirement: "Required",
        desc: "The unique identifier of the Capsule project. Used for compiled package name generation and bundle file writing.",
        validations: [
            "Must be a non-empty string.",
            "Alphanumeric characters, hyphens, and underscores only.",
            "Must not contain spaces or special symbols."
        ],
        impact: "Determines the compiled package and directory name in adapters, as well as the output bundle file prefix (e.g. <code>my-agent-0.1.0.capsule</code>).",
        tip: "Keep the name short, lowercase, and matching your GitHub repository identifier."
    },
    version: {
        title: "version",
        type: "string",
        requirement: "Required",
        desc: "The semantic version string specifying the release version of the Capsule package config.",
        validations: [
            "Must match standard SemVer syntax (e.g., major.minor.patch).",
            "Example values: <code>0.1.0</code>, <code>1.0.2-beta</code>."
        ],
        impact: "Enforced in output .capsule bundle names and written to lockfiles. Ensures that components maintain predictable version offsets.",
        tip: "Always increment the version string when you update tool python files or prompt files to maintain correct caching."
    },
    description: {
        title: "description",
        type: "string",
        requirement: "Optional",
        desc: "A brief explanation of what the Capsule agent project accomplishes and its overall workflow target.",
        validations: [
            "Must be a string.",
            "Should be less than 500 characters."
        ],
        impact: "Written into the framework-neutral graph metadata and compiled project readmes to explain the workflow to developer teams.",
        tip: "Explain the input data shape and output deliverables so other developers can reuse your bundle easily."
    },
    input_schema: {
        title: "input_schema",
        type: "object",
        requirement: "Optional",
        desc: "A standard JSON Schema outlining the required properties and data types of inputs passed to trigger the workflow execution.",
        validations: [
            "Must be a valid draft JSON Schema.",
            "Typically includes a <code>required</code> list and a <code>properties</code> object map."
        ],
        impact: "Enforced by the Capsule runner prior to workflow execution. Target framework adapter compilers construct input dataclasses or models from this schema.",
        tip: "Add minLength, pattern, or minimum checks to catch bad input payloads before calling LLM steps."
    },
    models: {
        title: "models",
        type: "object",
        requirement: "Required",
        desc: "Lists the LLM providers and models used in the workflow. Agents reference these configurations by name.",
        validations: [
            "Must map unique string keys to provider and model declarations.",
            "Required keys in models: <code>provider</code>, <code>model</code>."
        ],
        impact: "Used by compilers to structure model parameters, client setups, and routing variables in Crews, Graphs, or OpenAI SDK projects.",
        tip: "Use <code>provider: local</code> for offline testing or deterministic pytest mocks."
    },
    agents: {
        title: "agents",
        type: "object",
        requirement: "Required",
        desc: "Specifies the AI agents in the project, mapping prompts, model references, and tool permissions.",
        validations: [
            "Each agent requires a <code>prompt</code> (pointing to a markdown template) and a <code>model</code> name.",
            "Agent <code>tools</code> list elements must reference keys in the tools config block."
        ],
        impact: "Generates code structures and prompts for each agent step. Static scan checks prompts are clean and exist on disk.",
        tip: "Place prompts in separate markdown files under an <code>agents/</code> folder to benefit from editor Markdown syntax highlighting."
    },
    tools: {
        title: "tools",
        type: "object",
        requirement: "Optional",
        desc: "Configures python tool scripts or Model Context Protocol (MCP) server tool calls available to agents.",
        validations: [
            "Python tools must specify <code>type: python</code> and an <code>entrypoint</code> path (e.g. <code>tools/write.py:write</code>).",
            "MCP declarations must declare <code>type: mcp</code>, <code>server</code>, and <code>tool</code> keys.",
            "Every tool requires a <code>permission</code> string label."
        ],
        impact: "Python code tools are loaded dynamically during runs. Static scanner checks scripts for dangerous imports or file access.",
        tip: "Use MCP declarations during layout mockups, then write custom Python scripts when finalizing local utilities."
    },
    workflow: {
        title: "workflow",
        type: "object",
        requirement: "Required",
        desc: "Defines the execution graph, starting node, and transition paths between steps and gates.",
        validations: [
            "Must specify a valid <code>start</code> key corresponding to a workflow step ID.",
            "Edges must connect existing steps. Infinite cycles with no endpoints are blocked.",
            "Workflow step types must be <code>agent</code> or <code>human_gate</code>."
        ],
        impact: "Controls executor state routing. Compilers compile step transitions to LangGraph nodes or CrewAI flow handoffs.",
        tip: "Introduce a <code>human_gate</code> step to enforce visual check gates before tools run write/database queries."
    },
    permissions: {
        title: "permissions",
        type: "object",
        requirement: "Optional",
        desc: "Registers authorized permissions mapped to specific tools, establishing runtime sandbox rules.",
        validations: [
            "Keys must map to defined tools.",
            "Values must be strings specifying permission scopes."
        ],
        impact: "The runtime permissions engine intercepts tool executions, checking if the tool's required permission label is in this allowed list.",
        tip: "Keep permissions granular. Use distinct names like <code>write_draft</code> or <code>query_policy</code> instead of wildcard permissions."
    },
    tests: {
        title: "tests",
        type: "array",
        requirement: "Optional",
        desc: "List of test files containing input payloads, tool output mocks, and return value assertion rules.",
        validations: [
            "Must be an array of YAML file paths.",
            "Corresponding YAML files must comply with Capsule test schema rules."
        ],
        impact: "Enables <code>capsule test</code> runner to run isolated execution tests, skipping LLM costs by using tool mocking rules.",
        tip: "Add a test configuration for every branching edge in your workflow layout to protect against regressions."
    }
};

// 4. Setup Event Listeners
document.addEventListener("DOMContentLoaded", () => {
    const clickableKeys = document.querySelectorAll(".yaml-key.clickable");
    
    clickableKeys.forEach(key => {
        key.addEventListener("click", (e) => {
            // Remove active classes
            clickableKeys.forEach(k => k.classList.remove("active"));
            
            // Add active class to clicked
            const element = e.currentTarget;
            element.classList.add("active");
            
            // Get data key
            const specKey = element.getAttribute("data-spec");
            const data = specData[specKey];
            
            if (data) {
                // Update Info Panel
                document.getElementById("spec-title").textContent = data.title;
                document.getElementById("spec-type").textContent = data.type;
                
                const reqEl = document.getElementById("spec-req");
                reqEl.textContent = data.requirement;
                if (data.requirement.toLowerCase() === "optional") {
                    reqEl.classList.add("optional");
                } else {
                    reqEl.classList.remove("optional");
                }
                
                document.getElementById("spec-desc").innerHTML = data.desc;
                document.getElementById("spec-impact").innerHTML = data.impact;
                document.getElementById("spec-tip").innerHTML = data.tip;
                
                // Update validation list
                const valList = document.getElementById("spec-validations");
                valList.innerHTML = "";
                data.validations.forEach(val => {
                    const li = document.createElement("li");
                    li.innerHTML = val;
                    valList.appendChild(li);
                });
            }
        });
    });
});
