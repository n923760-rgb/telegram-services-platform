from uuid import uuid4

from arq.connections import RedisSettings, create_pool
from arq.worker import Worker

from app.core.db import sessions
from app.core.models import Order
from app.core.settings import config
from app.orders.engine import submit
from app.wallet.ledger import balance
from app.workers.runner import execute_job
from tests.test_foundation import Delivery, fund, job_for


async def test_real_arq_queue_executes_durable_order():
    await fund()
    oid = await submit(1, "echo", {"text": "عبر Redis"}, 100, "queue")
    jid = await job_for(oid)
    pool = await create_pool(RedisSettings.from_dsn(config().redis_url.get_secret_value()))
    queue = f"test:queue:{uuid4()}"
    delivery = Delivery()
    worker = Worker(
        functions=[execute_job],
        redis_pool=pool,
        queue_name=queue,
        burst=True,
        handle_signals=False,
        keep_result=0,
        poll_delay=0.01,
        ctx={"delivery": delivery},
        log_results=False,
    )
    try:
        await pool.enqueue_job("execute_job", str(jid), _queue_name=queue)
        await worker.async_run()
        assert worker.jobs_complete == 1 and worker.jobs_failed == 0
        async with sessions() as db:
            assert (await db.get(Order, oid)).status == "completed"
            assert (await balance(db, 1)).available == 900
        assert delivery.results[0].text == "عبر Redis"
    finally:
        await worker.close()
