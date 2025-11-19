import pytest
from pyoco import task, Flow
from pyoco.core.models import Task
from pyoco.dsl.syntax import TaskWrapper

def test_dsl_task_decorator():
    @task
    def my_task():
        pass
    
    assert isinstance(my_task, TaskWrapper)
    assert isinstance(my_task.task, Task)

def test_dsl_flow_chaining():
    @task
    def t1(): pass
    
    @task
    def t2(): pass
    
    flow = Flow("dsl_test")
    flow >> t1 >> t2
    
    assert len(flow.tasks) == 2
    # Check dependencies
    # t1 and t2 are TaskWrappers.
    # flow.tasks contains Task objects.
    
    task1 = t1.task
    task2 = t2.task
    
    assert task1 in flow.tasks
    assert task2 in flow.tasks
    assert task1 in task2.dependencies
