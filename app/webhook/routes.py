import datetime
from flask import Blueprint, request, jsonify, render_template
from app.extensions import collection

webhook = Blueprint('Webhook', __name__, url_prefix='/webhook')
PER_PAGE = 10  # Set the default items per page


def create_event(author, action, from_branch=None, to_branch=None):
    """
    This function is helper function to create event data. which are stored in the database

    """
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    event = {
        'author': author,
        'action': action,
        'timestamp': timestamp
    }
    if from_branch:
        event['from_branch'] = from_branch
    if to_branch:
        event['to_branch'] = to_branch
    return event


@webhook.route('Wb/', methods=["GET"])
def receiver():
    return jsonify({'message': 'Webhook Checking'}), 200


@webhook.route('/', methods=['POST'])
def webhook_actions():
    """
    This function is used to handle Webhooks

    """
    data = request.json
    event_type = request.headers.get('X-GitHub-Event')

    if not data:
        return jsonify({'message': 'Invalid payload'}), 400

    if event_type == 'ping':
        return jsonify({'message': 'Webhook ping received'}), 200

    elif event_type == 'push':
        handle_push_event(data)
        return jsonify({'message': 'Push event received'}), 200

    elif event_type == 'pull_request':
        handle_pull_request_event(data)
        return jsonify({'message': 'Pull request event received'}), 200

    else:
        return jsonify({'message': 'Unsupported event type'}), 400


def handle_push_event(data):
    """
    This function handles the GitHub push event.

    """
    author = data['pusher']['name']
    to_branch = data['ref'].split('/')[-1]
    event = create_event(author, action='pushed to', to_branch=to_branch)
    collection.insert_one(event)


def handle_pull_request_event(data):
    """
    This function handles the GitHub pull request event.
    If the action is closed and merged is True then this event is merge request event
    else It is Pull request events (Action should be Opened)

    """
    action = data['action']
    author = data['pull_request']['user']['login']
    from_branch = data['pull_request']['head']['ref']
    to_branch = data['pull_request']['base']['ref']

    if action == 'closed':
        if data['pull_request']['merged']:
            event = create_event(author, 'merged branch', from_branch, to_branch)
        else:
            event = create_event(author, 'Closed Pull Request (not merged)', from_branch, to_branch)
        collection.insert_one(event)
    else:
        event = create_event(author, 'submitted a pull request from', from_branch, to_branch)
        collection.insert_one(event)


@webhook.route('/index', methods=["GET"])
def index():
    """
    This Function is used to render the events on UI with Pulling the events every 15 seconds
    """
    # Fetch the current page and per_page values from the query string
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', PER_PAGE))

    # Calculate the offset for MongoDB query
    offset = (page - 1) * per_page

    # Fetch the events from MongoDB with pagination, sorted by timestamp (descending)
    events_cursor = collection.find({}, {'_id': 0}).sort("timestamp", -1).skip(offset).limit(per_page)
    events = list(events_cursor)

    # Get total document count to calculate total pages
    total_count = collection.count_documents({})
    total_pages = (total_count + per_page - 1) // per_page

    # Check if the request is for JSON (polling)
    if request.headers.get('Accept') == 'application/json':
        return jsonify({
            'events': events,
            'page': page,
            'total_pages': total_pages
        })

    # Render the HTML page
    return render_template('index.html', events=events, page=page, per_page=per_page, total_pages=total_pages)
