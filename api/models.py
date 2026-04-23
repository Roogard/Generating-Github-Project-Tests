from datetime import datetime
from sqlalchemy import Integer, String, Float, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.db import Base
from api.constants import RunStatus


class Run(Base):
    __tablename__ = "runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Identity
    repo_url: Mapped[str] = mapped_column(String, nullable=False)
    function_name: Mapped[str] = mapped_column(String, default="")
    mode: Mapped[str] = mapped_column(String, default="single")  # single | project | quixbugs
    benchmark_id: Mapped[str | None] = mapped_column(String, nullable=True)

    # Lifecycle
    status: Mapped[str] = mapped_column(String, default=RunStatus.PENDING)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    output_dir: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    elapsed_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    progress_current: Mapped[int] = mapped_column(Integer, default=0)
    progress_total: Mapped[int] = mapped_column(Integer, default=0)

    # LLM config (flat columns, no JSON blob)
    provider: Mapped[str | None] = mapped_column(String, nullable=True)
    model: Mapped[str | None] = mapped_column(String, nullable=True)
    preset: Mapped[str | None] = mapped_column(String, nullable=True)
    use_rag: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    # Aggregate test outcomes
    tests_run: Mapped[int] = mapped_column(Integer, default=0)
    tests_passed: Mapped[int] = mapped_column(Integer, default=0)
    tests_failed: Mapped[int] = mapped_column(Integer, default=0)
    tests_errored: Mapped[int] = mapped_column(Integer, default=0)
    avg_coverage_pct: Mapped[float | None] = mapped_column(Float, nullable=True)

    # SWT-bench oracle transitions (0 when mode is single/project)
    f2p: Mapped[int] = mapped_column(Integer, default=0)
    f2f: Mapped[int] = mapped_column(Integer, default=0)
    p2f: Mapped[int] = mapped_column(Integer, default=0)
    p2p: Mapped[int] = mapped_column(Integer, default=0)
    patch_applied: Mapped[bool] = mapped_column(Boolean, default=False)
    detected: Mapped[bool] = mapped_column(Boolean, default=False)
    resolved: Mapped[bool] = mapped_column(Boolean, default=False)
    golden: Mapped[bool] = mapped_column(Boolean, default=False)

    # Promotion to vector memory
    promoted_to_memory_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    functions: Mapped[list["Function"]] = relationship(
        "Function", back_populates="run", cascade="all, delete-orphan"
    )


class Function(Base):
    __tablename__ = "functions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    run_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("runs.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    file_path: Mapped[str] = mapped_column(String, nullable=False)
    source: Mapped[str | None] = mapped_column(Text, nullable=True)

    # The agent-produced test file
    test_code: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Aggregate outcomes
    tests_passed: Mapped[int] = mapped_column(Integer, default=0)
    tests_failed: Mapped[int] = mapped_column(Integer, default=0)
    coverage_pct: Mapped[float | None] = mapped_column(Float, nullable=True)

    run: Mapped["Run"] = relationship("Run", back_populates="functions")
