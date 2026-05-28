from app.models.task_model import Task

def prepare_user_reports():
    return Task.get_user_task_summary_with_pending()