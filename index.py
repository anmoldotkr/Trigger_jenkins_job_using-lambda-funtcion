import json
import urllib.request
import urllib.parse
import base64

# Jenkins Configuration
JENKINS_URL = "https://example.com"
# JOB_PATH = "<enter_job_path>"
USERNAME = "<Enter_jenkins_username>"
API_TOKEN = "<enter_jenkins_api_token>"  # Use a secret manager in production

def get_jenkins_crumb():
    crumb_url = f"{JENKINS_URL}/crumbIssuer/api/json"
    request = urllib.request.Request(crumb_url)
    auth = f"{USERNAME}:{API_TOKEN}"
    encoded_auth = base64.b64encode(auth.encode("utf-8")).decode("utf-8")
    request.add_header("Authorization", f"Basic {encoded_auth}")

    with urllib.request.urlopen(request) as response:
        data = json.loads(response.read())
        return {data['crumbRequestField']: data['crumb']}

def lambda_handler(event, context):
    try:
        # Log headers and body
        headers = event.get("headers", {})
        body = json.loads(event.get("body", "{}"))

        print(f"Event Key: {headers.get('x-event-key', 'unknown')}")
        print("Payload Body:", json.dumps(body, indent=2))

        # Allow only pull request events
        event_key = headers.get("x-event-key", "")
        if event_key not in ["pullrequest:created", "pullrequest:updated"]:
            return {
                "statusCode": 200,
                "body": json.dumps(f"Ignored event: {event_key}")
            }

        # Get PR source and destination branches
        pr = body.get("pullrequest", {})
        target_branch = pr.get("destination", {}).get("branch", {}).get("name", "")
        source_branch = pr.get("source", {}).get("branch", {}).get("name", "")

        print(f"Source Branch: {source_branch}")
        print(f"Target Branch: {target_branch}")

        # Only trigger if the target branch is 'Automation'
        if target_branch != "Automation":
            return {
                "statusCode": 200,
                "body": json.dumps(f"Ignored: Target branch is not 'Automation'")
            }

        # Jenkins crumb for CSRF
        crumb_header = get_jenkins_crumb()

        # Build parameters passed to Jenkins
        build_params = {
            "environment": "testing",
            "faker": "true",
            "tag": "example",
            "filename": "example.robot",
            "branch": source_branch
        }
        encoded_data = urllib.parse.urlencode(build_params).encode("utf-8")

        # Build request to Jenkins
        build_url = f"{JENKINS_URL}{JOB_PATH}/buildWithParameters"
        request = urllib.request.Request(build_url, data=encoded_data, method="POST")
        auth = f"{USERNAME}:{API_TOKEN}"
        encoded_auth = base64.b64encode(auth.encode("utf-8")).decode("utf-8")
        request.add_header("Authorization", f"Basic {encoded_auth}")

        # Add crumb header
        for k, v in crumb_header.items():
            request.add_header(k, v)

        # Trigger the Jenkins job
        with urllib.request.urlopen(request) as response:
            status_code = response.getcode()
            if status_code in [200, 201, 202]:
                return {
                    "statusCode": 200,
                    "body": json.dumps("Jenkins job triggered successfully.")
                }
            else:
                return {
                    "statusCode": status_code,
                    "body": json.dumps("Jenkins job trigger failed.")
                }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps(f"Error: {str(e)}")
        }
