from flask import Flask, render_template, request
from twilio.rest import Client

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    action = None
    result = None
    error_message = None

    if request.method == "POST":
        account_sid = request.form.get("account_sid")
        auth_token = request.form.get("auth_token")
        action = request.form.get("action")
        client = Client(account_sid, auth_token)

        try:
            if action == "spam_check":
                phone_number = request.form.get("phone_number")
                # Twilio Lookup API: Check spam status
                lookup_result = client.lookups.v1.phone_numbers(phone_number).fetch(type="carrier")
                spam_status = lookup_result.carrier.get("spam", "No spam info available")
                result = f"Spam Status for {phone_number}: {spam_status}"

            elif action == "close_subaccount":
                subaccount_sid = request.form.get("subaccount_sid")
                # Check subaccount status before closing
                subaccount = client.api.v2010.accounts(subaccount_sid).fetch()
                if subaccount.status == "closed":
                    error_message = f"Subaccount {subaccount_sid} is already closed and cannot be updated."
                else:
                    # Close the subaccount
                    client.api.v2010.accounts(subaccount_sid).update(status="closed")
                    result = f"Subaccount {subaccount_sid} has been closed successfully."

        except Exception as e:
            error_message = str(e)

    return render_template(
        "index.html",
        action=action,
        result=result,
        error_message=error_message,
    )

if __name__ == "__main__":
    app.run(debug=True)
