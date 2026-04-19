from datetime import datetime
from sqlalchemy import Integer, String, Float, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.db import Base
from api.constants import RunStatus, FixStatus


class Run(Base):
    __tablename__ = "runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    repo_url: Mapped[str] = mapped_column(String, nullable=False)
    function_name: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, default=RunStatus.PENDING)
    config_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    output_dir: Mapped[str | None] = mapped_column(String, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    progress_current: Mapped[int] = mapped_column(Integer, default=0)
    progress_total: Mapped[int] = mapped_column(Integer, default=0)

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
    fix_attempts: Mapped[list["FixAttempt"]] = relationship("FixAttempt", back_populates="function", cascade="all, delete-orphan")


class GeneratedTest(Base):
    __tablename__ = "generated_tests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    function_id: Mapped[int] = mapped_column(Integer, ForeignKey("functions.id"), nullable=False)
    test_type: Mapped[str] = mapped_column(String, nullable=False)
    code: Mapped[str | None] = mapped_column(Text, nullable=True)
    iteration: Mapped[int] = mapped_column(Integer, default=0)
    coverage_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    passed: Mapped[int] = mapped_column(Integer, default=0)
    failed: Mapped[int] = mapped_column(Integer, default=0)

    function: Mapped["Function"] = relationship("Function", back_populates="generated_tests")
    test_failures: Mapped[list["TestFailure"]] = relationship("TestFailure", back_populates="generated_test", cascade="all, delete-orphan")


class ProposedFix(Base):
    __tablename__ = "proposed_fixes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    function_id: Mapped[int] = mapped_column(Integer, ForeignKey("functions.id"), nullable=False)
    fixed_code: Mapped[str | None] = mapped_column(Text, nullable=True)
    diagnosis: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String, default=FixStatus.PROPOSED)

    function: Mapped["Function"] = relationship("Function", back_populates="proposed_fixes")


class TestFailure(Base):
    __tablename__ = "test_failures"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    generated_test_id: Mapped[int] = mapped_column(Integer, ForeignKey("generated_tests.id"), nullable=False)
    test_name: Mapped[str] = mapped_column(String, nullable=False)
    kind: Mapped[str] = mapped_column(String, nullable=False)  # "failure" | "error"
    longrepr: Mapped[str | None] = mapped_column(Text, nullable=True)
    assertion: Mapped[str | None] = mapped_column(String, nullable=True)
    expected: Mapped[str | None] = mapped_column(String, nullable=True)
    actual: Mapped[str | None] = mapped_column(String, nullable=True)

    generated_test: Mapped["GeneratedTest"] = relationship("GeneratedTest", back_populates="test_failures")


class FixAttempt(Base):
    __tablename__ = "fix_attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    function_id: Mapped[int] = mapped_column(Integer, ForeignKey("functions.id"), nullable=False)
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)
    attempt_type: Mapped[str] = mapped_column(String, nullable=False)  # "structural_repair" | "fix_agent"
    diagnosis: Mapped[str | None] = mapped_column(Text, nullable=True)
    failures_before: Mapped[int] = mapped_column(Integer, default=0)
    failures_after: Mapped[int] = mapped_column(Integer, default=0)
    converged: Mapped[bool] = mapped_column(Boolean, default=False)

    function: Mapped["Function"] = relationship("Function", back_populates="fix_attempts")


