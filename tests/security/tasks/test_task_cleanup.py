import time
from api.services.background_tasks import tasks_db, cleanup_tasks
import api.services.background_tasks as bg_services

def test_task_ttl_eviction():
    tasks_db.clear()
    
    # 1. Insert two tasks, one old (expired) and one new
    tasks_db["old_task"] = {
        "status": "completed",
        "filename": "old.log",
        "result": None,
        "error": None,
        "created_at": time.time() - 5000  # > 3600 TTL
    }
    
    tasks_db["new_task"] = {
        "status": "completed",
        "filename": "new.log",
        "result": None,
        "error": None,
        "created_at": time.time() - 100
    }
    
    # Trigger cleanup
    cleanup_tasks()
    
    assert "old_task" not in tasks_db
    assert "new_task" in tasks_db

def test_task_max_queue_eviction():
    tasks_db.clear()
    
    # Configure low max limit
    orig_max = bg_services.UNILOG_MAX_TASKS
    bg_services.UNILOG_MAX_TASKS = 3
    
    try:
        # Create 4 tasks with sequential created_at timestamps
        for i in range(4):
            tid = f"task_{i}"
            tasks_db[tid] = {
                "status": "completed",
                "filename": f"log_{i}.log",
                "result": None,
                "error": None,
                "created_at": time.time() - (10 - i)  # task_0 is oldest, task_3 is newest
            }
            
        cleanup_tasks()
        
        # Max limit is 3, task_0 (oldest) should be evicted
        assert "task_0" not in tasks_db
        assert "task_1" in tasks_db
        assert "task_2" in tasks_db
        assert "task_3" in tasks_db
    finally:
        bg_services.UNILOG_MAX_TASKS = orig_max
