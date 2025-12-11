"""Repository for async job queue operations."""
from datetime import datetime, timedelta
from typing import Any, Optional, Sequence

from sqlalchemy import and_, func, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job import AsyncJob, JobStatus


class JobRepository:
    """
    Repository for AsyncJob queue operations.

    Provides methods for enqueueing, dequeueing, and managing
    background jobs stored in PostgreSQL.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def enqueue(
        self,
        queue_name: str,
        payload: dict[str, Any],
        priority: int = 0,
        scheduled_at: Optional[datetime] = None,
        max_attempts: int = 3,
    ) -> AsyncJob:
        """
        Add a new job to the queue.

        Args:
            queue_name: Name of the queue (e.g., 'risk_evaluation', 'audit')
            payload: Job data
            priority: Higher priority jobs are processed first
            scheduled_at: When to process (None = now)
            max_attempts: Maximum retry attempts

        Returns:
            Created AsyncJob instance
        """
        job = AsyncJob(
            queue_name=queue_name,
            payload=payload,
            priority=priority,
            scheduled_at=scheduled_at or datetime.utcnow(),
            max_attempts=max_attempts,
            status=JobStatus.PENDING,
        )
        self.session.add(job)
        await self.session.flush()
        await self.session.refresh(job)
        return job

    async def dequeue(
        self,
        queue_name: str,
        worker_id: str,
        lock_timeout_seconds: int = 300,
    ) -> Optional[AsyncJob]:
        """
        Get and lock the next available job from a queue.

        Uses SELECT FOR UPDATE SKIP LOCKED for safe concurrent access.

        Args:
            queue_name: Name of the queue to pull from
            worker_id: Identifier of the worker claiming the job
            lock_timeout_seconds: How long to hold the lock

        Returns:
            AsyncJob if available, None otherwise
        """
        now = datetime.utcnow()

        # Find next pending job that is ready to be processed
        # Use FOR UPDATE SKIP LOCKED for concurrent safety
        query = (
            select(AsyncJob)
            .where(
                and_(
                    AsyncJob.queue_name == queue_name,
                    AsyncJob.status == JobStatus.PENDING,
                    AsyncJob.scheduled_at <= now,
                )
            )
            .order_by(AsyncJob.priority.desc(), AsyncJob.scheduled_at.asc())
            .limit(1)
            .with_for_update(skip_locked=True)
        )

        result = await self.session.execute(query)
        job = result.scalar_one_or_none()

        if job:
            # Lock the job
            job.status = JobStatus.RUNNING
            job.locked_by = worker_id
            job.locked_at = now
            job.started_at = now
            job.attempts += 1

            self.session.add(job)
            await self.session.flush()
            await self.session.refresh(job)

        return job

    async def complete(
        self,
        job_id: int,
        result_data: Optional[dict[str, Any]] = None,
    ) -> Optional[AsyncJob]:
        """
        Mark a job as successfully completed.

        Args:
            job_id: The job ID
            result_data: Optional result data to store

        Returns:
            Updated AsyncJob or None if not found
        """
        result = await self.session.execute(
            select(AsyncJob).where(AsyncJob.id == job_id)
        )
        job = result.scalar_one_or_none()

        if not job:
            return None

        job.status = JobStatus.COMPLETED
        job.completed_at = datetime.utcnow()
        job.locked_by = None
        job.locked_at = None

        if result_data:
            job.payload = {**job.payload, "result": result_data}

        self.session.add(job)
        await self.session.flush()
        await self.session.refresh(job)

        return job

    async def fail(
        self,
        job_id: int,
        error: str,
        retry: bool = True,
        retry_delay_seconds: int = 60,
    ) -> Optional[AsyncJob]:
        """
        Mark a job as failed.

        Args:
            job_id: The job ID
            error: Error message
            retry: Whether to retry the job
            retry_delay_seconds: Delay before retry

        Returns:
            Updated AsyncJob or None if not found
        """
        result = await self.session.execute(
            select(AsyncJob).where(AsyncJob.id == job_id)
        )
        job = result.scalar_one_or_none()

        if not job:
            return None

        job.error = error
        job.locked_by = None
        job.locked_at = None

        # Check if we should retry
        if retry and job.attempts < job.max_attempts:
            job.status = JobStatus.PENDING
            job.scheduled_at = datetime.utcnow() + timedelta(seconds=retry_delay_seconds)
        else:
            job.status = JobStatus.FAILED
            job.completed_at = datetime.utcnow()

        self.session.add(job)
        await self.session.flush()
        await self.session.refresh(job)

        return job

    async def cancel(self, job_id: int) -> Optional[AsyncJob]:
        """
        Cancel a pending job.

        Args:
            job_id: The job ID

        Returns:
            Updated AsyncJob or None if not found
        """
        result = await self.session.execute(
            select(AsyncJob).where(
                and_(
                    AsyncJob.id == job_id,
                    AsyncJob.status == JobStatus.PENDING,
                )
            )
        )
        job = result.scalar_one_or_none()

        if not job:
            return None

        job.status = JobStatus.CANCELLED
        job.completed_at = datetime.utcnow()

        self.session.add(job)
        await self.session.flush()
        await self.session.refresh(job)

        return job

    async def release_stale_locks(
        self,
        lock_timeout_seconds: int = 300,
    ) -> int:
        """
        Release jobs that have been locked for too long.

        This handles cases where a worker crashed without completing.

        Args:
            lock_timeout_seconds: Consider stale after this many seconds

        Returns:
            Number of jobs released
        """
        stale_cutoff = datetime.utcnow() - timedelta(seconds=lock_timeout_seconds)

        result = await self.session.execute(
            update(AsyncJob)
            .where(
                and_(
                    AsyncJob.status == JobStatus.RUNNING,
                    AsyncJob.locked_at < stale_cutoff,
                )
            )
            .values(
                status=JobStatus.PENDING,
                locked_by=None,
                locked_at=None,
                error="Released due to stale lock",
            )
            .returning(AsyncJob.id)
        )

        released_ids = result.scalars().all()
        await self.session.flush()

        return len(released_ids)

    async def get_queue_stats(
        self,
        queue_name: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Get statistics for the job queue.

        Args:
            queue_name: Optional queue name filter

        Returns:
            Dictionary with queue statistics
        """
        base_condition = AsyncJob.queue_name == queue_name if queue_name else True

        # Count by status
        status_counts = {}
        for status in JobStatus:
            query = select(func.count()).select_from(AsyncJob).where(
                and_(base_condition, AsyncJob.status == status)
            )
            result = await self.session.execute(query)
            status_counts[status.value] = result.scalar_one()

        # Get oldest pending job
        oldest_query = (
            select(AsyncJob.scheduled_at)
            .where(and_(base_condition, AsyncJob.status == JobStatus.PENDING))
            .order_by(AsyncJob.scheduled_at.asc())
            .limit(1)
        )
        oldest_result = await self.session.execute(oldest_query)
        oldest_pending = oldest_result.scalar_one_or_none()

        return {
            "queue_name": queue_name or "all",
            "by_status": status_counts,
            "total_pending": status_counts.get(JobStatus.PENDING.value, 0),
            "total_running": status_counts.get(JobStatus.RUNNING.value, 0),
            "total_failed": status_counts.get(JobStatus.FAILED.value, 0),
            "oldest_pending_at": oldest_pending.isoformat() if oldest_pending else None,
        }

    async def get_jobs_by_status(
        self,
        status: JobStatus,
        queue_name: Optional[str] = None,
        limit: int = 100,
    ) -> Sequence[AsyncJob]:
        """
        Get jobs by status.

        Args:
            status: Job status to filter by
            queue_name: Optional queue name filter
            limit: Maximum results

        Returns:
            List of matching jobs
        """
        conditions = [AsyncJob.status == status]
        if queue_name:
            conditions.append(AsyncJob.queue_name == queue_name)

        query = (
            select(AsyncJob)
            .where(and_(*conditions))
            .order_by(AsyncJob.created_at.desc())
            .limit(limit)
        )

        result = await self.session.execute(query)
        return result.scalars().all()

    async def cleanup_old_jobs(
        self,
        days_to_keep: int = 30,
        statuses: Optional[list[JobStatus]] = None,
    ) -> int:
        """
        Delete old completed/failed jobs.

        Args:
            days_to_keep: Keep jobs newer than this
            statuses: Statuses to clean up (default: COMPLETED, FAILED, CANCELLED)

        Returns:
            Number of jobs deleted
        """
        if statuses is None:
            statuses = [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]

        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)

        # Count before delete
        count_query = select(func.count()).select_from(AsyncJob).where(
            and_(
                AsyncJob.status.in_(statuses),
                AsyncJob.completed_at < cutoff_date,
            )
        )
        result = await self.session.execute(count_query)
        count = result.scalar_one()

        # Delete old jobs
        if count > 0:
            await self.session.execute(
                text("""
                    DELETE FROM async_jobs
                    WHERE status = ANY(:statuses)
                    AND completed_at < :cutoff_date
                """),
                {
                    "statuses": [s.value for s in statuses],
                    "cutoff_date": cutoff_date,
                },
            )
            await self.session.flush()

        return count
