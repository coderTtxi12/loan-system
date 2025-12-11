"""CLI for running background workers."""
import argparse
import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.core.config import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# Worker registry
WORKERS = {
    "risk_evaluation": "app.workers.risk_worker:RiskEvaluationWorker",
    "audit": "app.workers.audit_worker:AuditWorker",
    "webhook": "app.workers.webhook_worker:WebhookWorker",
    "notifications": "app.workers.webhook_worker:WebhookWorker",  # Alias
}


def get_worker_class(queue_name: str):
    """
    Get the worker class for a queue.

    Args:
        queue_name: Queue name

    Returns:
        Worker class
    """
    if queue_name not in WORKERS:
        raise ValueError(
            f"Unknown queue: {queue_name}. "
            f"Available: {', '.join(WORKERS.keys())}"
        )

    module_path, class_name = WORKERS[queue_name].rsplit(":", 1)
    module = __import__(module_path, fromlist=[class_name])
    return getattr(module, class_name)


async def run_worker(queue_name: str, worker_id: str = None) -> None:
    """
    Run a worker for a specific queue.

    Args:
        queue_name: Queue to process
        worker_id: Optional worker identifier
    """
    logger.info(f"Starting worker for queue: {queue_name}")

    try:
        worker_class = get_worker_class(queue_name)
        worker = worker_class(worker_id=worker_id)

        # Clean up stale jobs on startup
        released = await worker.cleanup_stale_jobs()
        if released > 0:
            logger.info(f"Released {released} stale jobs on startup")

        # Run the worker
        await worker.run_forever()

    except KeyboardInterrupt:
        logger.info("Worker stopped by user")
    except Exception as e:
        logger.error(f"Worker error: {e}")
        raise


async def run_all_workers() -> None:
    """Run all workers concurrently."""
    logger.info("Starting all workers...")

    tasks = []
    for queue_name in ["risk_evaluation", "audit", "webhook"]:
        worker_class = get_worker_class(queue_name)
        worker = worker_class()
        tasks.append(asyncio.create_task(worker.run_forever()))

    try:
        await asyncio.gather(*tasks)
    except KeyboardInterrupt:
        logger.info("All workers stopped by user")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run background workers for the loan system.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m app.workers.run --queue risk_evaluation
  python -m app.workers.run --queue audit
  python -m app.workers.run --queue webhook
  python -m app.workers.run --all

Available queues:
  risk_evaluation  - Process risk evaluation jobs
  audit           - Process audit logging jobs
  webhook         - Process outgoing webhook jobs
  notifications   - Alias for webhook queue
        """,
    )

    parser.add_argument(
        "--queue",
        "-q",
        type=str,
        help="Queue name to process",
    )
    parser.add_argument(
        "--worker-id",
        "-w",
        type=str,
        default=None,
        help="Unique worker identifier",
    )
    parser.add_argument(
        "--all",
        "-a",
        action="store_true",
        help="Run all workers",
    )

    args = parser.parse_args()

    if args.all:
        asyncio.run(run_all_workers())
    elif args.queue:
        asyncio.run(run_worker(args.queue, args.worker_id))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
