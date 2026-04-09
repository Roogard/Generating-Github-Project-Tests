from datetime import datetime
from sqlalchemy import Integer, String, Float, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.db import Base


class Run(Base):
    __tablename__ = "runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    repo_url: Mapped[str] = mapped_column(String, nullable=False)
    function_name: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, default="pending")  # pending | running | done | error
    config_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    output_dir: Mapped[str | None] = mapped_column(String, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    functions: Mapped[list["Function"]] = relationship("Function", back_populates="run", cascade="all, delete-orphan")


class Function(Base):
    __tablename__ = "functions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    run_id: Mapped[int] = mapped_column(Integer, ForeignKey("runs.id"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    file_path: Mapped[str] = mapped_column(String, nullable=False)
    source: Mapped[str | None] = mapped_column(Text, nullable=True)

    run: Mapped["Run"] = relationship("Run", back_populates="functions")
    generated_tests: Mapped[list["GeneratedTest"]] = relationship("GeneratedTest", back_populates="function", cascade="all, delete-orphan")
    proposed_fixes: Mapped[list["ProposedFix"]] = relationship("ProposedFix", back_populates="function", cascade="all, delete-orphan")


class GeneratedTest(Base):
    __tablename__ = "generated_tests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    function_id: Mapped[int] = mapped_column(Integer, ForeignKey("functions.id"), nullable=False)
    test_type: Mapped[str] = mapped_column(String, nullable=False)   # whitebox | blackbox
    code: Mapped[str | None] = mapped_column(Text, nullable=True)
    iteration: Mapped[int] = mapped_column(Integer, default=0)
    coverage_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    passed: Mapped[int] = mapped_column(Integer, default=0)
    failed: Mapped[int] = mapped_column(Integer, default=0)

    function: Mapped["Function"] = relationship("Function", back_populates="generated_tests")


class ProposedFix(Base):
    __tablename__ = "proposed_fixes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    function_id: Mapped[int] = mapped_column(Integer, ForeignKey("functions.id"), nullable=False)
    fixed_code: Mapped[str | None] = mapped_column(Text, nullable=True)
    diagnosis: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String, default="proposed")  # proposed | accepted | rejected

    function: Mapped["Function"] = relationship("Function", back_populates="proposed_fixes")


class BenchmarkRun(Base):
    __tablename__ = "benchmark_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    benchmark_name: Mapped[str] = mapped_column(String, nullable=False, index=True)
    model: Mapped[str] = mapped_column(String, nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String, nullable=False)
    project: Mapped[str] = mapped_column(String, nullable=False)
    bug_id: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)  # detected | missed | error
    tests_passed: Mapped[int] = mapped_column(Integer, default=0)
    tests_failed: Mapped[int] = mapped_column(Integer, default=0)
    fix_attempted: Mapped[bool] = mapped_column(Boolean, default=False)
    fix_converged: Mapped[bool] = mapped_column(Boolean, default=False)
    elapsed_seconds: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
