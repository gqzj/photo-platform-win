"""测试任务API"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.database import db
from app.models.crawler_task import CrawlerTask

app = create_app()

with app.app_context():
    try:
        print("开始测试查询任务列表...")
        tasks = CrawlerTask.query.limit(5).all()
        print(f"查询成功，找到 {len(tasks)} 条任务")
        
        if tasks:
            print("\n第一条任务:")
            task_dict = tasks[0].to_dict()
            for key, value in task_dict.items():
                print(f"  {key}: {value}")
        
        print("\n测试完成！")
    except Exception as e:
        print(f"错误: {str(e)}")
        import traceback
        traceback.print_exc()

