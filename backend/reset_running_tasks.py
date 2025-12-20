# -*- coding: utf-8 -*-
"""重置运行中的任务状态"""
import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.database import db
from app.models.crawler_task import CrawlerTask

app = create_app()

with app.app_context():
    # 查找所有running状态的任务
    running_tasks = CrawlerTask.query.filter_by(status='running').all()
    
    print(f"Found {len(running_tasks)} running tasks")
    
    for task in running_tasks:
        # 如果任务开始时间超过1小时，认为是异常状态，重置为failed
        if task.started_at:
            time_diff = datetime.now() - task.started_at
            if time_diff > timedelta(hours=1):
                print(f"\nResetting task {task.id} (started {time_diff} ago)")
                task.status = 'failed'
                task.last_error = '任务运行超时，已自动重置'
                task.finished_at = datetime.now()
                db.session.add(task)
            else:
                print(f"\nTask {task.id} is still running (started {time_diff} ago)")
        else:
            # 没有开始时间，直接重置
            print(f"\nResetting task {task.id} (no started_at)")
            task.status = 'pending'
            db.session.add(task)
    
    db.session.commit()
    print(f"\nReset completed!")

