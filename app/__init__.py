from datetime import datetime

from flask import Flask

from app.webhook.routes import webhook


# Creating our flask app
def create_app():
    app = Flask(__name__, template_folder='../templates')

    def format_datetime(dt):
        if isinstance(dt, str):
            # Parse string to datetime object
            dt = datetime.strptime(dt, '%Y-%m-%d %H:%M:%S')

        day = dt.strftime('%d').lstrip('0')
        if 4 <= int(day) <= 20 or 24 <= int(day) <= 30:
            suffix = 'th'
        else:
            suffix = ['st', 'nd', 'rd'][int(day) % 10 - 1]

        # Formatted the date and time as per the requirement
        formatted_date = dt.strftime(f'{day}{suffix} %B %Y - %I:%M %p UTC')
        return formatted_date

    # registering all the blueprints
    app.register_blueprint(webhook)
    # Register the custom filter with the Flask app
    app.jinja_env.filters['format_datetime'] = format_datetime

    return app
