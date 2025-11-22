import unittest
import uuid
from pyoco.core.models import TaskState, RunStatus, RunContext
from pyoco.core.context import Context

class TestStateModels(unittest.TestCase):
    def test_enums(self):
        self.assertEqual(TaskState.PENDING.value, "PENDING")
        self.assertEqual(TaskState.RUNNING.value, "RUNNING")
        self.assertEqual(TaskState.SUCCEEDED.value, "SUCCEEDED")
        self.assertEqual(TaskState.FAILED.value, "FAILED")
        self.assertEqual(TaskState.CANCELLED.value, "CANCELLED")

        self.assertEqual(RunStatus.RUNNING.value, "RUNNING")
        self.assertEqual(RunStatus.COMPLETED.value, "COMPLETED")
        self.assertEqual(RunStatus.FAILED.value, "FAILED")
        self.assertEqual(RunStatus.CANCELLING.value, "CANCELLING")
        self.assertEqual(RunStatus.CANCELLED.value, "CANCELLED")

    def test_run_context_initialization(self):
        run_ctx = RunContext()
        self.assertIsInstance(run_ctx.run_id, str)
        # Verify it looks like a UUID
        try:
            uuid.UUID(run_ctx.run_id)
        except ValueError:
            self.fail("run_id is not a valid UUID")
            
        self.assertEqual(run_ctx.status, RunStatus.RUNNING)
        self.assertEqual(run_ctx.tasks, {})
        self.assertIsNotNone(run_ctx.start_time)
        self.assertIsNone(run_ctx.end_time)

    def test_context_with_run_context(self):
        run_ctx = RunContext()
        ctx = Context(run_context=run_ctx)
        
        self.assertIsNotNone(ctx.run_context)
        self.assertEqual(ctx.run_context.run_id, run_ctx.run_id)
        self.assertEqual(ctx.run_context.status, RunStatus.RUNNING)

if __name__ == '__main__':
    unittest.main()
