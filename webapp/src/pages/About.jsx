import { motion } from 'framer-motion' ;

export default function About() {
   return (
    <div className="page">
      <div className="page-header">
         <motion.h1  className="home-title">Generating Project<br /> Tests (GGPT)</motion.h1>
      <div>
       <div className="section-header"><i>Recreate<br />Reason<br />Repair</i></div>
        </div>
      </div>

      <div className="card" style={{ marginBottom: 16 }}>
        <div className="section-label">Intro</div>
        <div className="card">
         <p className="">An issue-driven AI agent that reads GitHub bug reports and writes regression tests that reproduce them — installed as a GitHub Action, triggered by a label.</p>
        </div>
      </div>

      <div className="card" style={{ marginBottom: 16 }}>
        <div className="section-label">Project</div>
        {/* TODO: write copy */}
      </div>

      <div className="card">
        <div className="section-label">Contact</div>
        {/* TODO: write copy */}
      </div>
    </div>
  )
}
