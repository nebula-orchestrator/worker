from unittest import TestCase
from functions.misc.cron_schedule import CronJobs
from datetime import datetime


class CronTests(TestCase):

    def test_cron_flow(self):

        # initiate the class
        test_cron_object = CronJobs()

        # test adding a cron
        test_add_reply = test_cron_object.add_cron_job("test_cron", "0 * * * *")
        self.assertTrue(isinstance(test_add_reply, datetime))
        self.assertEqual(test_cron_object.cron_jobs, {'test_cron': '0 * * * *'})

        # test update a cron
        test_update_reply = test_cron_object.update_cron_job("test_cron", "* * * * *")
        self.assertTrue(isinstance(test_update_reply, datetime))
        self.assertEqual(test_cron_object.cron_jobs, {'test_cron': '* * * * *'})

        # test returning the next run time
        test_next_run_reply = test_cron_object.return_cron_job_next_runtime("test_cron")
        self.assertTrue(isinstance(test_next_run_reply, datetime))
        self.assertGreaterEqual(test_next_run_reply, test_update_reply)

        # test removing a class
        test_cron_object.remove_cron_job("test_cron")
        self.assertEqual(test_cron_object.cron_jobs, {})
