from apscheduler.schedulers.background import BackgroundScheduler
from ..services.rankings import CompositeRankings

def register_jobs(app):
    scheduler = BackgroundScheduler(daemon=True)

    @scheduler.scheduled_job("interval", hours=1)
    def refresh_rankings():
        with app.app_context():
            svc = CompositeRankings()
            svc.weekly_rankings("RB", week=1)
            app.logger.info("Refreshed rankings cache")

    scheduler.start()
    return scheduler
