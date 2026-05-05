import { motion } from 'framer-motion';
 
const fadeUp = {
  hidden: { opacity: 0, y: 24 },
  show: (i = 0) => ({
    opacity: 1,
    y: 0,
    transition: { duration: 0.6, delay: i * 0.12, ease: [0.22, 1, 0.36, 1] },
  }),
};

/// Main repo entry
const WORKFLOW_YAML = `name: GGPT
# Triggers:
#   Label  ggpt       — generate a regression test (alias of ggpt-test)
#   Label  ggpt-test  — generate a regression test
#   Label  ggpt-fix   — generate the test AND propose a source-code fix;
#                       both ship in one PR (fix is verified — if the test
#                       still fails after the proposed edits, the fix is
#                       reverted and the PR ships test-only).
#   Comment /ggpt          — same as ggpt-test
#   Comment /ggpt fix      — same as ggpt-fix
on:
  issues:
    types: [labeled]
  issue_comment:
    types: [created]

jobs:
  ggpt:
    if: |
      (github.event_name == 'issues' &&
       startsWith(github.event.label.name, 'ggpt')) ||
      (github.event_name == 'issue_comment' &&
       startsWith(github.event.comment.body, '/ggpt'))
    uses: Roogard/Generating-Github-Project-Tests/.github/workflows/ggpt.yml@main
    permissions:
      contents: write
      pull-requests: write
      issues: write
    secrets: inherit
`

/// Wrapper for YAML
function CodeBlock({ children }) {
  return (
    <pre className="code-block" style={{ whiteSpace: 'pre' }}>
      <code>{children}</code>
    </pre>
  )
}

export default function Installation() {
  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1 className="page-title">Installation</h1>
          <div className="page-sub">
            Wire GGPT into any GitHub repo. The agent reads issues and opens pull requests
            with regression tests (and optionally a fix).
          </div>
        </div>
      </div>

      <div className="card" style={{ marginBottom: 16 }}>
        <div className="section-label">1. Add the workflow</div>
        <p style={{ marginBottom: 12, color: 'var(--text-2)' }}>
          Drop this file into your repo at{' '}
          <code style={{ fontFamily: 'var(--mono)', fontSize: 12, color: 'var(--text)' }}>
            .github/workflows/ggpt-issue.yml
          </code>
          :
        </p>
        <CodeBlock>{WORKFLOW_YAML}</CodeBlock>
      </div>

      <div className="card" style={{ marginBottom: 16 }}>
        <div className="section-label">2. Add an API key as a repo secret</div>
        <p style={{ marginBottom: 10, color: 'var(--text-2)' }}>
          Settings → Secrets and variables → Actions → <em>New repository secret</em>.
          Add at least one of the following — whichever provider you want the agent to use:
        </p>
        <ul style={{ marginLeft: 20, color: 'var(--text-2)', fontSize: 13, lineHeight: 1.8 }}>
          <li><code style={{ fontFamily: 'var(--mono)', color: 'var(--text)' }}>DEEPSEEK_API_KEY</code> — recommended (cheap, fast, the model used for the showcased benchmark)</li>
          <li><code style={{ fontFamily: 'var(--mono)', color: 'var(--text)' }}>ANTHROPIC_API_KEY</code> — for Claude models</li>
          <li><code style={{ fontFamily: 'var(--mono)', color: 'var(--text)' }}>OPENAI_API_KEY</code> — for GPT models</li>
        </ul>
        <p style={{ marginTop: 10, color: 'var(--text-3)', fontSize: 12 }}>
          <code style={{ fontFamily: 'var(--mono)' }}>GITHUB_TOKEN</code> is provided automatically by Actions — you don't add it.
        </p>
      </div>

      <div className="card">
        <div className="section-label">3. Trigger a run on any issue</div>
        <p style={{ marginBottom: 12, color: 'var(--text-2)' }}>Two ways:</p>

        <p style={{ marginBottom: 6, color: 'var(--text)', fontWeight: 600, fontSize: 13 }}>Apply a label</p>
        <ul style={{ marginLeft: 20, marginBottom: 14, color: 'var(--text-2)', fontSize: 13, lineHeight: 1.8 }}>
          <li><code style={{ fontFamily: 'var(--mono)', color: 'var(--text)' }}>ggpt</code> or <code style={{ fontFamily: 'var(--mono)', color: 'var(--text)' }}>ggpt-test</code> — write a regression test that reproduces the bug</li>
          <li><code style={{ fontFamily: 'var(--mono)', color: 'var(--text)' }}>ggpt-fix</code> — write the test <em>and</em> propose a fix in the same PR (fix is reverted if it doesn't make the test pass)</li>
        </ul>

        <p style={{ marginBottom: 6, color: 'var(--text)', fontWeight: 600, fontSize: 13 }}>Or comment on the issue</p>
        <ul style={{ marginLeft: 20, color: 'var(--text-2)', fontSize: 13, lineHeight: 1.8 }}>
          <li><code style={{ fontFamily: 'var(--mono)', color: 'var(--text)' }}>/ggpt</code> — same as the test label</li>
          <li><code style={{ fontFamily: 'var(--mono)', color: 'var(--text)' }}>/ggpt fix</code> — same as the fix label</li>
        </ul>
      </div>
    </div>
  )
}
