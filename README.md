
This is an **AWS Lambda function** written in Python that listens to **Bitbucket webhook events** and triggers a **Jenkins job** when certain conditions are met.

### Key Points:

1. **Jenkins Configuration**

   ```python
   JENKINS_URL = "https://example.com"
   USERNAME = "<Enter_jenkins_username>"
   API_TOKEN = "<enter_jenkins_api_token>"
   ```

   * Replace these with your Jenkins URL, username, and API token.
   * API token should ideally come from AWS Secrets Manager instead of hardcoding.

---

2. **Fetching Jenkins Crumb (CSRF protection)**

   ```python
   def get_jenkins_crumb():
       crumb_url = f"{JENKINS_URL}/crumbIssuer/api/json"
       ...
   ```

   * Jenkins requires a **crumb** (anti-CSRF token) to allow POST requests.
   * This function fetches the crumb from Jenkins and returns it as a header.

---

3. **Lambda Handler**

   ```python
   def lambda_handler(event, context):
   ```

   * The entry point for AWS Lambda.
   * `event` contains the Bitbucket webhook request.

---

4. **Log Incoming Event**

   ```python
   headers = event.get("headers", {})
   body = json.loads(event.get("body", "{}"))
   print(f"Event Key: {headers.get('x-event-key', 'unknown')}")
   ```

   * Logs which event was received (`pullrequest:created`, `pullrequest:updated`, etc.).
   * Logs the full webhook body for debugging.

---

5. **Filter Events**

   ```python
   if event_key not in ["pullrequest:created", "pullrequest:updated"]:
       return {"statusCode": 200, "body": json.dumps(f"Ignored event: {event_key}")}
   ```

   * Only process pull request events.
   * Ignore others (like push, branch delete, etc.).

---

6. **Extract Source & Target Branch**

   ```python
   target_branch = pr.get("destination", {}).get("branch", {}).get("name", "")
   source_branch = pr.get("source", {}).get("branch", {}).get("name", "")
   ```

   * Gets the PR source branch and target branch.

---

7. **Trigger only if Target Branch = "Automation"**

   ```python
   if target_branch != "Automation":
       return {"statusCode": 200, "body": json.dumps("Ignored: Target branch is not 'Automation'")}
   ```

   * Ensures only PRs targeting the `Automation` branch trigger Jenkins.

---

8. **Trigger Jenkins Job**

   ```python
   build_params = {
       "environment": "testing",
       "faker": "true",
       "tag": "example",
       "filename": "example.robot",
       "branch": source_branch
   }
   build_url = f"{JENKINS_URL}{JOB_PATH}/buildWithParameters"
   ```

   * Prepares job parameters.
   * Calls Jenkins API `buildWithParameters` to trigger the job with those params.
   * Adds Basic Auth + crumb header.
   * Returns success or failure.

---

9. **Error Handling**

   ```python
   except Exception as e:
       return {"statusCode": 500, "body": json.dumps(f"Error: {str(e)}")}
   ```

   * Any exception (auth failure, networking, etc.) is caught and returned.

---

## 📘 README.md

Here’s a well-structured `README.md` for your project:

````markdown
# Jenkins Bitbucket PR Trigger (AWS Lambda)

This project provides an **AWS Lambda function** that listens to **Bitbucket webhook events** and triggers a **Jenkins job** when a Pull Request is created or updated and targets the `Automation` branch.

---

## 🚀 Features
- Listens to **Bitbucket PR events** (`pullrequest:created`, `pullrequest:updated`).
- Triggers a Jenkins job with **custom build parameters**.
- Supports Jenkins **crumb issuer** (CSRF protection).
- Filters by **target branch** (`Automation` only).
- Secure authentication via Jenkins **API token**.

---

## 🛠 Prerequisites
- **Jenkins** with:
  - Job configured to accept build parameters.
  - API Token for the Jenkins user.
  - CSRF protection enabled with CrumbIssuer.

- **AWS Lambda** setup with:
  - Python 3.x runtime.
  - Bitbucket webhook pointing to API Gateway → Lambda.

---

## ⚙️ Configuration

Update the following in `lambda_function.py`:

```python
JENKINS_URL = "https://your-jenkins-url"
JOB_PATH = "/job/your-job-name"
USERNAME = "your-jenkins-username"
API_TOKEN = "your-jenkins-api-token"
````

> 💡 **Best Practice:** Store `API_TOKEN` in **AWS Secrets Manager** or **SSM Parameter Store**, not in plain code.

---

## 📦 Deployment

1. Zip and deploy Lambda:

   ```bash
   zip function.zip lambda_function.py
   aws lambda update-function-code --function-name myLambda --zip-file fileb://function.zip
   ```

2. Configure API Gateway to forward Bitbucket webhook requests to Lambda.

3. In Bitbucket repository settings → Webhooks:

   * Add a webhook pointing to your API Gateway endpoint.
   * Select **Pull Request: Created** and **Pull Request: Updated** events.

---

## 🔄 Workflow

1. Developer opens or updates a PR → Bitbucket sends a webhook to Lambda.
2. Lambda receives the event and extracts:

   * **Source branch**
   * **Target branch**
3. If target branch = `Automation`, Lambda:

   * Gets Jenkins crumb.
   * Triggers Jenkins job with parameters:

     * `environment=testing`
     * `faker=true`
     * `tag=example`
     * `filename=example.robot`
     * `branch=<source_branch>`
4. Jenkins executes the job.

---

## 📝 Example Response

* **Ignored event:**

  ```json
  {"statusCode": 200, "body": "\"Ignored event: repo:push\""}
  ```

* **Triggered successfully:**

  ```json
  {"statusCode": 200, "body": "\"Jenkins job triggered successfully.\""}
  ```

* **Error:**

  ```json
  {"statusCode": 500, "body": "\"Error: Unauthorized\""}
  ```

---

## 🔐 Security Notes

* Use **HTTPS** for Jenkins.
* Store **API\_TOKEN** securely (Secrets Manager/SSM).
* Apply **least privilege** IAM policy for Lambda.
* Validate incoming webhook signatures if possible.


Do you want me to also **add webhook signature validation** (HMAC check) for Bitbucket? That would make your Lambda more secure instead of relying only on event keys.
```
