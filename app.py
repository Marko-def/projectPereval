from flask import Flask, request, jsonify
from database_manager import DatabaseManager

app = Flask(__name__)
db_manager = DatabaseManager()

@app.route('/submitData', methods=['POST'])
def submit_data():
    if not request.is_json:
        return jsonify({"status": 400, "message": "Запрос должен быть в формате JSON", "id": None}), 400

    data = request.get_json()
    result = db_manager.submit_data(data)
    return jsonify(result), result['status']

@app.route('/submitData/<int:id>', methods=['GET'])
def get_pass(id):
    result = db_manager.get_pass_by_id(id)
    return jsonify(result), result['status']

@app.route('/submitData/<int:id>', methods=['PATCH'])
def update_pass(id):
    if not request.is_json:
        return jsonify({"state": 0, "message": "Запрос должен быть в формате JSON"}), 400

    data = request.get_json()
    result = db_manager.update_pass(id, data)
    return jsonify(result), 200 if result['state'] == 1 else 400

@app.route('/submitData/', methods=['GET'])
def get_passes_by_user():
    email = request.args.get('user__email')
    if not email:
        return jsonify({"status": 400, "message": "Параметр user__email обязателен", "data": None}), 400

    result = db_manager.get_passes_by_user_email(email)
    return jsonify(result), result['status']

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

