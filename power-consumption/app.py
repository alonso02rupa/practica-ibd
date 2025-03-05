from flask import Flask, jsonify, request
import requests

app = Flask(__name__)

@app.route('/api/books', methods=['GET'])
def get_books():
    try:
        response = requests.get('http://catalog:5000/books')
        return jsonify(response.json())
    except requests.exceptions.RequestException as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/borrow', methods=['POST'])
def borrow_book():
    book_id = request.json.get('book_id')
    user_id = request.json.get('user_id')

    # Verificar usuario
    try:
        user_response = requests.get(f'http://users:5000/users/{user_id}')
        user_response.raise_for_status()
    except requests.exceptions.RequestException:
        return jsonify({'error': 'User service unavailable'}), 503

    # Procesar préstamo
    try:
        loan_response = requests.post(
            'http://borrowing:5000/borrow',
            json={'book_id': book_id, 'user_id': user_id}
        )
        loan_response.raise_for_status()
    except requests.exceptions.RequestException:
        return jsonify({'error': 'Borrowing service unavailable'}), 503

    # Enviar notificación
    try:
        requests.post(
            'http://notifications:5000/notify',
            json={'user_id': user_id, 'message': f'Book {book_id} borrowed successfully'}
        )
    except requests.exceptions.RequestException:
        # Log error but don't fail the request
        print('Notification service unavailable')

    return jsonify({'message': 'Book borrowed successfully'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
