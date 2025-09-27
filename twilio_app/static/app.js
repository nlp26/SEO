function toggleActionFields() {
    const action = document.getElementById("action").value;

    // Hide all conditional fields by default
    document.getElementById("spam-check-fields").classList.add("hidden");
    document.getElementById("close-subaccount-fields").classList.add("hidden");

    // Show the relevant fields based on the selected action
    if (action === "spam_check") {
        document.getElementById("spam-check-fields").classList.remove("hidden");
        document.getElementById("phone_number").required = true; // Make phone number required
        document.getElementById("subaccount_sid").required = false; // Remove requirement
    } else if (action === "close_subaccount") {
        document.getElementById("close-subaccount-fields").classList.remove("hidden");
        document.getElementById("subaccount_sid").required = true; // Make subaccount SID required
        document.getElementById("phone_number").required = false; // Remove requirement
    }
}
