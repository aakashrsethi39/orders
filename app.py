from flask import Flask, jsonify

app = Flask(__name__)

orders = [
    {
        "id": 1,
        "user_id": 101,
        "product": "Cloud Platform",
        "status": "completed"
    },
    {
        "id": 2,
        "user_id": 102,
        "product": "DevOps Pipeline",
        "status": "processing"
    },
    {
        "id": 3,
        "user_id": 101,
        "product": "Kubernetes",
        "status": "shipped"
    }
]


@app.get("/")
def home():
    return jsonify({
        "service": "orders",
        "status": "running"
    })


@app.get("/health")
def health():
    return jsonify({
        "status": "healthy"
    })


@app.get("/orders")
@app.get("/api/orders")
def get_orders():
    return jsonify(orders)


@app.get("/orders/<int:order_id>")
def get_order(order_id):
    order = next(
        (order for order in orders if order["id"] == order_id),
        None
    )

    if not order:
        return jsonify({"error": "Order not found"}), 404

    return jsonify(order)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)