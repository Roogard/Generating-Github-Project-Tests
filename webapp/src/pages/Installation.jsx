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
const SECRETS = [
  { key: 'DEEPSEEK_API_KEY', note: 'Recommended — cheap, fast, used for the showcased benchmark', accent: true },
  { key: 'ANTHROPIC_API_KEY', note: 'For Claude models' },
  { key: 'OPENAI_API_KEY', note: 'For GPT models' },
];
 
const ACTIONS = [
  {
    group: 'Allow Permissions',
    items: [
      { cmd: 'Settings → Actions → General → Workflow permissions' },
      { cmd: 'Allow GitHub Actions to create and approve pull requests.', desc: '<- Check!' },
    ],
  },
];

const TRIGGERS = [
  {
    group: 'Apply a label',
    items: [
      { cmd: 'ggpt / ggpt-test', desc: 'Write a regression test that reproduces the bug' },
      { cmd: 'ggpt-fix', desc: 'Write the test and propose a fix in the same PR' },
    ],
  },
  {
    group: 'Or comment on the issue',
    items: [
      { cmd: '/ggpt', desc: 'Same as the test label' },
      { cmd: '/ggpt fix', desc: 'Same as the fix label' },
    ],
  },
];
 
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
    <div style={styles.outer}>
 
      <motion.div
        style={styles.header}
        initial="hidden"
        animate="show"
        variants={{ show: { transition: { staggerChildren: 0.1 } } }}
      >
        <motion.p variants={fadeUp} style={styles.eyebrow}>
          Setup Guide &nbsp;·&nbsp; GitHub Actions
        </motion.p>
 
        <div style={styles.titleRow}>
          <motion.h1 variants={fadeUp} className="home-title" style={styles.title}>
            Installation
          </motion.h1>
          </div>
          <motion.p variants={fadeUp} style={styles.subtitle}>
            Wire GGPT into any GitHub repo. The agent reads issues and opens pull
            requests with regression tests — and optionally a fix.
          </motion.p>
      </motion.div>
 
      <div style={styles.grid}>
        {STEPS.map((step, i) => (
          <motion.div
            key={step.id}
            custom={i}
            initial="hidden"
            animate="show"
            variants={fadeUp}
            style={{ ...styles.card, ...(step.accent ? styles.cardAccent : {}) }}
          >
            {/* Card top */}
            <div style={styles.cardTop}>
              <span style={styles.cardId}>{step.id}</span>
              <span style={{ ...styles.badge, ...(step.accent ? styles.badgeAccent : {}) }}>
                {step.label}
              </span>
            </div>
 
            <h2 style={{ ...styles.cardHeading, ...(step.accent ? styles.cardHeadingAccent : {}) }}>
              {step.heading}
            </h2>
 
            <p style={styles.cardBody}>{step.body}</p>
 
            {step.content === 'yaml' && (
              <pre style={styles.codeBlock}>
                <code style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 10.5 }}>
                  {WORKFLOW_YAML}
                </code>
              </pre>
            )}
 
            {step.content === 'secrets' && (
              <div style={styles.infoBox}>
                {SECRETS.map(({ key, note, accent }) => (
                  <div key={key} style={styles.infoRow}>
                    <code style={{ ...styles.cmdPill, ...(accent ? styles.cmdPillAccent : {}) }}>
                      {key}
                    </code>
                    <span style={styles.infoNote}>{note}</span>
                  </div>
                ))}
                <div style={styles.infoFooter}>
                  <code style={styles.ic}>GITHUB_TOKEN</code>
                  <span style={{ color: '#444', fontSize: 11, marginLeft: 8 }}>
                    — provided automatically by Actions.
                  </span>
                </div>
              </div>
            )}
 
            {step.content === 'actions' && (
              <div style={styles.infoBox}>
                {ACTIONS.map(({ group, items }, gi) => (
                  <div key={group}>
                    {gi > 0 && <div style={styles.infoDivider} />}
                    <div style={styles.triggerGroup}>
                      <p style={styles.triggerGroupLabel}>{group}</p>
                      {items.map(({ cmd, desc }) => (
                        <div key={cmd} style={styles.infoRow}>
                          <code style={styles.cmdPill}>{cmd}</code>
                          {desc && <span style={styles.infoNote}>{desc}</span>}
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            )}

            {step.content === 'triggers' && (
              <div style={styles.infoBox}>
                {TRIGGERS.map(({ group, items }, gi) => (
                  <div key={group}>
                    {gi > 0 && <div style={styles.infoDivider} />}
                    <div style={styles.triggerGroup}>
                      <p style={styles.triggerGroupLabel}>{group}</p>
                      {items.map(({ cmd, desc }) => (
                        <div key={cmd} style={styles.infoRow}>
                          <code style={styles.cmdPill}>{cmd}</code>
                          <span style={styles.infoNote}>{desc}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            )}
 
            {/* Bottom bar */}
            <div style={styles.cardBar}>
              <div style={{ ...styles.cardBarFill, ...(step.accent ? styles.cardBarFillAccent : {}) }} />
            </div>
          </motion.div>
        ))}
      </div>
 
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.4 }}
        style={styles.footer}
      >
        <span style={styles.footerText}>GGPT &nbsp;·&nbsp; Build #2041</span>
        <a href="https://github.com/Roogard/Generating-Github-Project-Tests" style={styles.footerLink}>
          View on GitHub ↗
        </a>
      </motion.div>
 
    </div>
  );
}
 
const styles = {
  outer: {
    background: '#0A0A0A',
    fontFamily: "'DM Mono', monospace",
    color: '#FAFAF8',
    minHeight: '100vh',
    maxWidth: 900,
    margin: '0 auto',
    padding: '3rem 2rem 4rem',
  },
  header: {
    marginBottom: '3rem',
    borderBottom: '0.5px solid #8B6914',
    paddingBottom: '2.5rem',
  },
  eyebrow: {
    fontSize: 11,
    letterSpacing: '0.28em',
    color: '#C9A84C',
    textTransform: 'uppercase',
    marginBottom: '1.25rem',
  },
  titleRow: {
    display: 'flex',
    alignItems: 'flex-end',
    justifyContent: 'space-between',
    gap: 32,
  },
  title: {
    fontStyle: 'italic',
    flexShrink: 0,
  },
  subtitle: {
    fontSize: 14,
    color: '#666',
    lineHeight: 1.7,
    maxWidth: 800,
    marginTop: '1rem',
  },
  grid: {
    display: 'flex',
    flexDirection: 'column',
    gap: 1,
    background: '#8B6914',
    border: '1px solid #8B6914',
    borderRadius: 4,
    overflow: 'hidden',
    marginBottom: '1.5rem',
  },
  card: {
    background: '#111',
    padding: '1.75rem 1.5rem 1.25rem',
    display: 'flex',
    flexDirection: 'column',
    gap: '1rem',
    transition: 'background 0.15s',
  },
  cardAccent: {
    background: '#141008',
  },
  cardTop: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  cardId: {
    fontSize: 13,
    letterSpacing: '0.15em',
    color: '#333',
  },
  badge: {
    fontSize: 14,
    letterSpacing: '0.12em',
    padding: '3px 8px',
    borderRadius: 2,
    textTransform: 'uppercase',
    background: '#1A1A1A',
    color: '#666',
    border: '0.5px solid #2a2a2a',
  },
  badgeAccent: {
    background: '#2a2310',
    color: '#C9A84C',
    border: '0.5px solid #8B6914',
  },
  cardHeading: {
    fontFamily: "'Cormorant Garamond', serif",
    fontSize: '1.2rem',
    fontWeight: 500,
    color: '#FAFAF8',
    lineHeight: 1.3,
  },
  cardHeadingAccent: {
    color: '#E8C97A',
  },
  cardBody: {
    fontSize: 13,
    color: '#777',
    lineHeight: 1.7,
  },
  cardBar: {
    height: 1,
    background: '#1a1a1a',
    borderRadius: 1,
    overflow: 'hidden',
    marginTop: 'auto',
  },
  cardBarFill: {
    height: '100%',
    width: '100%',
    background: '#2a2a2a',
  },
  cardBarFillAccent: {
    background: 'linear-gradient(90deg, #8B6914, #C9A84C)',
  },
  codeBlock: {
    background: '#0d0d0f',
    border: '1px solid #1e1e22',
    borderRadius: 6,
    padding: '1.1rem 1.25rem',
    overflowX: 'auto',
    fontSize: 13,
    lineHeight: 1.7,
    color: '#a0a0b0',
    whiteSpace: 'pre',
    margin: 0,
  },
  ic: {
    fontFamily: "'JetBrains Mono', monospace",
    fontSize: 13,
    color: '#C9A84C',
    background: '#1a1408',
    padding: '1px 5px',
    borderRadius: 3,
  },
  infoBox: {
    border: '1px solid #1e1e22',
    borderRadius: 6,
    overflow: 'hidden',
  },
  infoRow: {
    display: 'flex',
    alignItems: 'baseline',
    gap: 14,
    padding: '10px 14px',
    borderBottom: '1px solid #1a1a1a',
  },
  infoNote: {
    fontSize: 13,
    color: '#555',
    lineHeight: 1.5,
  },
  infoFooter: {
    padding: '9px 14px',
    background: '#0d0d0f',
    display: 'flex',
    alignItems: 'center',
  },
  infoDivider: {
    height: 1,
    background: '#1e1e22',
    margin: '0 14px',
  },
  cmdPill: {
    fontFamily: "'JetBrains Mono', monospace",
    fontSize: 13,
    color: '#888',
    background: '#1a1a1a',
    border: '0.5px solid #2a2a2a',
    padding: '2px 7px',
    borderRadius: 3,
    whiteSpace: 'nowrap',
    flexShrink: 0,
    minWidth: 160,
  },
  cmdPillAccent: {
    color: '#C9A84C',
    background: '#1a1408',
    border: '0.5px solid #8B6914',
  },
  triggerGroup: {
    padding: '12px 14px',
    display: 'flex',
    flexDirection: 'column',
    gap: 8,
  },
  triggerGroupLabel: {
    fontSize: 12,
    letterSpacing: '0.2em',
    color: '#8B6914',
    textTransform: 'uppercase',
    marginBottom: 4,
  },
  footer: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingTop: '0.5rem',
  },
  footerText: {
    fontSize: 12,
    letterSpacing: '0.1em',
    color: '#333',
  },
  footerLink: {
    fontSize: 12,
    letterSpacing: '0.15em',
    color: '#C9A84C',
    textDecoration: 'none',
    border: '0.5px solid #8B6914',
    padding: '5px 14px',
    borderRadius: 2,
    textTransform: 'uppercase',
  },
};

/// specifically here for modularity

const STEPS = [
  {
    id: '01',
    label: 'Add the workflow',
    heading: 'ADD TO ANY REPOSITORY.',
    body: (
      <>
        Copy this into your repo at{' '}
        <code style={styles.ic}>.github/workflows/ggpt-issue.yml</code>:
      </>
    ),
    accent: true,
    content: 'yaml',
  },
  {
    id: '02',
    label: 'Add an API key',
    heading: 'CONNECT YOUR LLM VIA KEY.',
    body: <>Settings → Secrets and variables → Actions → <span style={{ color: '#C9A84C' }}>New repository secret</span>. Add at least one:</>,
    content: 'secrets',
  },
  {
    id: '03',
    label: 'Give Permissions',
    heading: 'ALLOW ACTIONS IN WORKFLOW PERMISSIONS.',
    body: 'Make sure to save all settings!',
    content: 'actions',
  },
  {
    id: '04',
    label: 'Trigger a Run',
    heading: 'BEGIN A RUN.',
    body: 'Two ways to invoke the agent on any open issue:',
    content: 'triggers',
  },
];