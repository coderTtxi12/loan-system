"""Base worker class for background job processing."""
import asyncio
import logging
import signal
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import async_session_maker
from app.repositories.job_repository import JobRepository

logger = logging.getLogger(__name__)


class BaseWorker(ABC):
    """
    Abstract base class for background workers.

    Workers pull jobs from a PostgreSQL queue and process them.
    Provides:
    - Graceful shutdown handling
    - Error handling with retries
    - Logging
    """

    def __init__(
        self,
        queue_name: str,
        worker_id: Optional[str] = None,
        poll_interval: float = 1.0,
        lock_timeout: int = 300,
    ):
        """
        Initialize the worker.

        Args:
            queue_name: Name of the queue to process
            worker_id: Unique identifier for this worker
            poll_interval: Seconds between queue polls
            lock_timeout: Seconds before a job lock expires
        """
        self.queue_name = queue_name
        self.worker_id = worker_id or f"{queue_name}-{datetime.now().timestamp()}"
        self.poll_interval = poll_interval
        self.lock_timeout = lock_timeout
        self.running = False
        self._shutdown_event = asyncio.Event()

    @abstractmethod
    async def process(self, job_id: int, payload: dict[str, Any]) -> dict[str, Any]:
        """
        Process a job.

        Args:
            job_id: The job ID
            payload: Job payload data

        Returns:
            Result data to store with the job
        """
        ...

    async def _get_session(self) -> AsyncSession:
        """Get a new database session."""
        return async_session_maker()

    async def _process_job(
        self,
        session: AsyncSession,
        job_repo: JobRepository,
        job: Any,
    ) -> None:
        """
        Process a single job with error handling.

        Args:
            session: Database session
            job_repo: Job repository
            job: The job to process
        """
        job_id = job.id
        logger.info(f"[{self.worker_id}] Processing job {job_id}: {job.queue_name}")

        try:
            # Process the job
            result = await self.process(job_id, job.payload)

            # Mark as completed
            await job_repo.complete(job_id, result)
            await session.commit()

            logger.info(f"[{self.worker_id}] Job {job_id} completed successfully")

        except Exception as e:
            await session.rollback()
            logger.error(f"[{self.worker_id}] Job {job_id} failed: {e}")

            # Mark as failed (will retry if attempts < max_attempts)
            try:
                async with async_session_maker() as new_session:
                    new_job_repo = JobRepository(new_session)
                    await new_job_repo.fail(
                        job_id,
                        error=str(e),
                        retry=True,
                        retry_delay_seconds=60 * job.attempts,  # Exponential backoff
                    )
                    await new_session.commit()
            except Exception as fail_error:
                logger.error(f"[{self.worker_id}] Failed to mark job as failed: {fail_error}")

    async def run_once(self) -> bool:
        """
        Run one iteration of the worker loop.

        Returns:
            True if a job was processed
        """
        async with async_session_maker() as session:
            job_repo = JobRepository(session)

            # Try to get a job
            job = await job_repo.dequeue(
                queue_name=self.queue_name,
                worker_id=self.worker_id,
                lock_timeout_seconds=self.lock_timeout,
            )

            if job:
                await self._process_job(session, job_repo, job)
                return True

            return False

    async def run_forever(self) -> None:
        """
        Run the worker loop until shutdown.

        Polls the queue and processes jobs continuously.
        """
        self.running = True
        logger.info(f"[{self.worker_id}] Starting worker for queue '{self.queue_name}'")

        # Setup signal handlers
        loop = asyncio.get_event_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, self._handle_shutdown)

        try:
            while self.running:
                try:
                    processed = await self.run_once()

                    # If no job was processed, wait before polling again
                    if not processed:
                        await asyncio.sleep(self.poll_interval)

                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"[{self.worker_id}] Worker error: {e}")
                    await asyncio.sleep(self.poll_interval)

        finally:
            logger.info(f"[{self.worker_id}] Worker stopped")

    def _handle_shutdown(self) -> None:
        """Handle shutdown signal."""
        logger.info(f"[{self.worker_id}] Shutdown signal received")
        self.running = False
        self._shutdown_event.set()

    async def stop(self) -> None:
        """Stop the worker gracefully."""
        self._handle_shutdown()
        await self._shutdown_event.wait()

    async def cleanup_stale_jobs(self) -> int:
        """
        Clean up stale locked jobs.

        Returns:
            Number of jobs released
        """
        async with async_session_maker() as session:
            job_repo = JobRepository(session)
            released = await job_repo.release_stale_locks(self.lock_timeout)
            await session.commit()

            if released > 0:
                logger.info(f"[{self.worker_id}] Released {released} stale jobs")

            return released
