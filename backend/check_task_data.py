# -*- coding: utf-8 -*-
"""检查任务数据"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.database import db
from app.models.crawler_task import CrawlerTask

app = create_app()

with app.app_context():
    tasks = CrawlerTask.query.all()
    print(f"Total tasks: {len(tasks)}")
    print("\nTask details:")
    print("-" * 60)
    
    for task in tasks:
        print(f"\nTask ID: {task.id}")
        print(f"  Name: {task.name}")
        print(f"  Task Type: {task.task_type}")
        print(f"  Status: {task.status}")
        print(f"  Platform: {task.platform}")
        print(f"  Keywords JSON: {task.keywords_json}")
        
        # Check button display condition
        show_button = task.task_type == 'keyword' and task.status != 'running'
        print(f"  Should show crawl button: {show_button}")

