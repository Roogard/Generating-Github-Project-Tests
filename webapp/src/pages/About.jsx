
import { useEffect, useRef, useState } from 'react' ;
import { motion, useScroll, useTransform } from 'framer-motion';

const fadeUp = {
  hidden: { opacity: 0, y: 24 },
  show: (i = 0) => ({
    opacity: 1,
    y: 0,
    transition: { duration: 0.6, delay: i * 0.12, ease: [0.22, 1, 0.36, 1] },
  }),
};

const CARDS = [
  {
    id: '01',
    label: 'Introduction',
    heading: '',
    body: 'An AI agent that reads GitHub bug reports and writes regression tests that reproduce them — installed as a GitHub Action, triggered by a label.',
    accent: true,
  },
  {
    id: '02',
    label: 'Modern Problem',
    heading: '',
    body: 'Recently, there has been a large demand for code and Github Repo creation due to code generation via AI. This leads to an increased amount of issues in many code bases. Additionally, if you want to try to use AI to fix these issues, you often have to pass in your entire codebase and GitHub issue into an LLM, which takes a lot of steps and exposes your code to third parties..',
  },
  {
    id: '03',
    label: 'Modern Solution',
    heading: ' ',
    body: 'GGPT lives inside a GitHub Actions workflow. Point it at an issue, and it recreates the bug as a test case — then suggests a targeted fix..',
    tag: 'Simple & Accessible',
  },
];

export default function About() {
  /// For motioned hero card
  const heroRef = useRef(null) ;
  const cardsRef = useRef(null) ;
  const { scrollY } = useScroll() ;

  const heroOpacity = useTransform(scrollY, [0, 380], [1, 0]) ;
  const heroY = useTransform(scrollY, [0, 380], [0, -60]) ;
  const scrollToCards = () => {
    cardsRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

   return (
    <div className="page">
      <motion.section
        ref={heroRef}
        style={{ ...styles.hero, opacity: heroOpacity, y: heroY }}
      >
        <motion.div
          style={styles.heroInner}
          initial="hidden"
          animate="show"
          variants={{ show: { transition: { staggerChildren: 0.1 } } }}
        >
          <motion.p variants={fadeUp} style={styles.eyebrow}>
            GitHub Action &nbsp;·&nbsp; AI-Powered Testing
          </motion.p>
 
          <motion.div variants={fadeUp} style={styles.titleRow}>
          <h1 className="home-title">
            Generating<br />
            <span style={styles.titleAccent}>GitHub&nbsp;Project</span><br />
            Tests
          </h1>
 
          <div style={styles.tagline}>
            {['Recreate', 'Reason', 'Repair'].map((word, i) => (
              <span key={word} style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <span style={styles.taglineWord}>{word}</span>
                {i < 2 && <span style={styles.taglineDot} />}
              </span>
            ))}
            </div>
          </motion.div>
 
          <motion.button
            variants={fadeUp}
            onClick={scrollToCards}
            style={styles.scrollBtn}
            whileHover={{ opacity: 0.75 }}
            whileTap={{ scale: 0.97 }}
          >
            <span>Meet GGPT!</span>
            <motion.span
              style={styles.scrollArrow}
              animate={{ y: [0, 5, 0] }}
              transition={{ repeat: Infinity, duration: 1.6, ease: 'easeInOut' }}
            >
              ↓
            </motion.span>
          </motion.button>
        </motion.div>
        <div style={styles.heroBorder} />
      </motion.section>

      <div style={styles.grid}>
        {CARDS.map((card, i) => (
          <motion.div
          key={card.id}
            custom={i}
          initial="hidden"
            animate="show"
            variants={fadeUp}
            style={{
              ...styles.card,
              ...(card.accent ? styles.cardAccent : {}),
            }}
          >
            <div style={styles.cardTop}>
              <span style={styles.cardId}>{card.id}</span>
              <span style={{
                ...styles.badge,
                ...(card.accent ? styles.badgeAccent : {}),
              }}>
                {card.label}
              </span>
            </div>
 
            <h2 style={{
              ...styles.cardHeading,
              ...(card.accent ? styles.cardHeadingAccent : {}),
            }}>
              {card.heading}
            </h2>
            <br />
            <p style={styles.cardBody}>{card.body}</p>
 
            {card.tag && (
              <div style={styles.cardTag}>{card.tag}</div>
            )}
 
            <div style={styles.cardBar}>
              <div style={{
                ...styles.cardBarFill,
                ...(card.accent ? styles.cardBarFillAccent : {}),
              }} />
            </div>
          </motion.div>
        ))}

      </div>
       <motion.div
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5, delay: 0.3 }}
          style={styles.footer} >
          <span style={styles.footerText}>GGPT &nbsp;·&nbsp; Build #2041</span>
          <a href="https://github.com/Roogard/Generating-Github-Project-Tests" style={styles.footerLink}>
            &nbsp; &nbsp; View on GitHub ↗
          </a>
        </motion.div>
    </div>
   );
}


/// CSS Locals
const styles = {
  page: {
    background: '#0A0A0A',
    fontFamily: "'DM Mono', monospace",
    color: '#FAFAF8',
    minHeight: '100vh',
  },
  hero: {
    position: 'sticky',
    top: 0,
    height: '65vh',
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'flex-end',
    pointerEvents: 'none',
    zIndex: 0,
  },
  heroInner: {
    maxWidth: 1100,
    width: '100%',
    margin: '0 auto',
    padding: '0 2rem 4rem',
    pointerEvents: 'auto',
  },

  grid: {
    display: 'grid',
    gap: 1,
    background: '#8B6914',
    border: '1px solid #8B6914',
    borderRadius: 4,
    overflow: 'hidden',
    marginBottom: '1.5rem',
  },
  card: {
    background: '#111',
    padding: '1.5rem 1.25rem 1.25rem',
    transition: 'background 0.15s',
    display: 'flex',
    flexDirection: 'column',
  },
  cardAccent: {
    background: '#141008',
  },
  cardTop: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '1rem',
  },
  cardsSection: {
     position: 'relative',
    zIndex: 1,
    background: '#0A0A0A',
    width: '100%',
  },
  cardsInner: {
    maxWidth: 900,
    margin: '0 auto',
    padding: '3rem 2rem 4rem'
  },
  cardId: {
    fontSize: 9,
    letterSpacing: '0.15em',
    color: '#333',
  },
  titleRow: {
  display: 'flex',
  alignItems: 'flex-end',  // aligns tagline to bottom of title
  justifyContent: 'space-between',
  gap: 32,
  marginBottom: '2.5rem',
},
tagline: {
  display: 'flex',
  flexDirection: 'column', // stack words vertically on the right
  alignItems: 'flex-start',
  gap: 10,
  paddingBottom: '0.5rem', // nudges it up from the baseline
  flexShrink: 0,
},
  taglineWord: {
    fontSize: 12,
    letterSpacing: '0.25em',
    color: '#555',
    textTransform: 'uppercase',
  },
  taglineDot: {
    width: 3,
    height: 3,
    borderRadius: '50%',
    background: '#8B6914',
    display: 'inline-block',
  },
  scrollBtn: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: 10,
    background: 'transparent',
    border: '0.5px solid #8B6914',
    color: '#C9A84C',
    fontSize: 16,
    letterSpacing: '0.2em',
    textTransform: 'uppercase',
    padding: '8px 20px',
    borderRadius: 2,
    cursor: 'pointer',
    fontFamily: "'DM Mono', monospace",
  },
  footer: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingTop: '0.5rem',
  },
  footerText: {
    fontSize: 9,
    letterSpacing: '0.1em',
    color: '#333',
  },
  footerLink: {
    fontSize: 9,
    letterSpacing: '0.15em',
    color: '#C9A84C',
    textDecoration: 'none',
    border: '0.5px solid #8B6914',
    padding: '5px 14px',
    borderRadius: 2,
    textTransform: 'uppercase',
  },
}
