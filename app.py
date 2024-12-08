from flask import Flask, render_template, request, jsonify
import time
from retrieve import make_query 

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    query = request.form.get('query')
    if not query:
        return jsonify({"error": "No query provided"}), 400

    start_time = time.time()
    results = make_query(query)
    end_time = time.time()
    query_time = round(end_time - start_time, 2)

    return jsonify({"results": results, "time": query_time})

if __name__ == '__main__':
    app.run(debug=True)
