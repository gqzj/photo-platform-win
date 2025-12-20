# -*- coding: utf-8 -*-
"""重置任务状态"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.database import db
from app.models.crawler_task import CrawlerTask

app = create_app()

with app.app_context():
    # 重置所有running状态的任务为pending
    running_tasks = CrawlerTask.query.filter_by(status='running').all()
    
    print(f"Found {len(running_tasks)} running tasks")
    
    for task in running_tasks:
        print(f"\nResetting task {task.id}:")
        print(f"  Old status: {task.status}")
        task.status = 'pending'
        task.started_at = None
        task.finished_at = None
        task.last_error = None
        db.session.add(task)
        print(f"  New status: pending")
    
    db.session.commit()
    print(f"\nReset completed! {len(running_tasks)} tasks reset to pending")

