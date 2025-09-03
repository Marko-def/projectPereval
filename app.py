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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

