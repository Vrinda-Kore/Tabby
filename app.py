from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enables CORS for all routes

# (in-memory, for demo only)
users = {
    1: {"id": 1, "name": "Alice"},
    2: {"id": 2, "name": "Bob"},
}
groups = {}
expenses = {}
group_members = {}

next_group_id = 1
next_expense_id = 1

@app.route("/")
def home():
    return "Split Expense Tracker API is running!"

@app.route("/groups", methods=["POST"])
def create_group():
    global next_group_id
    data = request.json
    group_name = data.get("name")
    if not group_name:
        return jsonify({"error": "Group name required"}), 400
    group_id = next_group_id
    next_group_id += 1
    groups[group_id] = {"id": group_id, "name": group_name}
    group_members[group_id] = set()
    return jsonify(groups[group_id]), 201

@app.route("/groups", methods=["GET"])
def list_groups():
    return jsonify(list(groups.values()))


@app.route("/users", methods=["GET"])
def list_users():
    return jsonify(list(users.values()))

@app.route("/groups/<int:group_id>/members", methods=["POST"])
def add_member(group_id):
    data = request.json
    user_id = data.get("user_id")
    if group_id not in groups:
        return jsonify({"error": "Group not found"}), 404
    if user_id not in users:
        return jsonify({"error": "User not found"}), 404
    group_members[group_id].add(user_id)
    return jsonify({"group_id": group_id, "members": list(group_members[group_id])})


next_user_id = max(users.keys()) + 1  # start from next available id

@app.route("/users", methods=["POST"])
def create_user():
    global next_user_id
    data = request.json
    name = data.get("name")
    if not name:
        return jsonify({"error": "User name required"}), 400

    # Simple check for duplicate names (optional)
    if any(user['name'].lower() == name.lower() for user in users.values()):
        return jsonify({"error": "User name already exists"}), 400

    user_id = next_user_id
    next_user_id += 1
    users[user_id] = {"id": user_id, "name": name}
    return jsonify(users[user_id]), 201


@app.route("/groups/<int:group_id>/expenses", methods=["POST"])
def add_expense(group_id):
    global next_expense_id
    data = request.json
    amount = data.get("amount")
    paid_by = data.get("paid_by")
    split_with = data.get("split_with")  # list of user_ids
    description = data.get("description", "")
    if group_id not in groups:
        return jsonify({"error": "Group not found"}), 404
    if not amount or not paid_by or not split_with:
        return jsonify({"error": "amount, paid_by, and split_with required"}), 400
    if paid_by not in users:
        return jsonify({"error": "Paid_by user not found"}), 404
    for u in split_with:
        if u not in users:
            return jsonify({"error": f"User {u} in split_with not found"}), 404

    expense_id = next_expense_id
    next_expense_id += 1
    expenses[expense_id] = {
        "id": expense_id,
        "group_id": group_id,
        "amount": amount,
        "paid_by": paid_by,
        "split_with": split_with,
        "description": description,
    }
    return jsonify(expenses[expense_id]), 201

@app.route("/groups/<int:group_id>/balances", methods=["GET"])
def get_balances(group_id):
    if group_id not in groups:
        return jsonify({"error": "Group not found"}), 404
    # Calculate net balance per user in group
    balances = {user_id: 0 for user_id in group_members[group_id]}
    for exp in expenses.values():
        if exp["group_id"] != group_id:
            continue
        split_amount = exp["amount"] / len(exp["split_with"])
        for u in exp["split_with"]:
            balances[u] -= split_amount
        balances[exp["paid_by"]] += exp["amount"]
    return jsonify(balances)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
