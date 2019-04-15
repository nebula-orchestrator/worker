from croniter import croniter
from datetime import datetime


class CronJobs:

    def __init__(self):
        self.cron_jobs = {}

    def add_cron_job(self, cron_job_name, cron_schedule):
        self.cron_jobs[cron_job_name] = cron_schedule
        return self.return_cron_job_next_runtime(cron_job_name)

    def update_cron_job(self, cron_job_name, cron_schedule):
        return self.add_cron_job(cron_job_name, cron_schedule)

    def remove_cron_job(self, cron_job_name):
        return self.cron_jobs.pop(cron_job_name, None)

    def return_cron_job_next_runtime(self, cron_job_name):
        next_run_dict = croniter(self.cron_jobs[cron_job_name], datetime.now())
        return next_run_dict.get_next(datetime)
