import logging

def configure_logging(app):
    app.logger.setLevel(logging.INFO)
