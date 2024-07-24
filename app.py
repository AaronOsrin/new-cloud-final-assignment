import logging
from flask import Flask, request, jsonify
import requests
import uuid
from pymongo import MongoClient, errors

app = Flask(__name__)

# Basic logging setup
logging.basicConfig(level=logging.DEBUG)

# MongoDB setup
try:
    client = MongoClient('mongodb://db:27017/', serverSelectionTimeoutMS=5000)
    db = client.booksdb
    books_collection = db.books
    client.server_info()  # Trigger exception if cannot connect to DB
    app.logger.info("MongoDB connection established.")
except errors.ServerSelectionTimeoutError as err:
    app.logger.error("MongoDB connection failed: " + str(err))
    db = None

VALID_GENRES = {'Fiction', 'Non-Fiction', 'Romance', 'Science Fiction', 'Fantasy'}

@app.route('/books', methods=['POST'])
def create_book():
    if db is None:
        return jsonify({'error': 'Database connection failed'}), 500

    data = request.get_json()
    required_fields = ['title', 'ISBN', 'genre']
    if not data or not all(field in data for field in required_fields) or any(data[field] == '' for field in required_fields):
        app.logger.error('Missing or empty required fields')
        return jsonify({'error': 'Missing or empty required fields'}), 400

    if data['genre'] not in VALID_GENRES:
        app.logger.error('Invalid genre provided')
        return jsonify({'error': 'Invalid genre provided'}), 422

    try:
        book_id = str(uuid.uuid4())
        books_collection.insert_one({
            'ID': book_id,
            'title': data['title'],
            'ISBN': data['ISBN'],
            'genre': data['genre'],
            'authors': '',
            'publisher': '',
            'publishedDate': ''
        })
        app.logger.info('Book created with id: ' + book_id)

        # External API call to Google Books API
        google_books_url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{data['ISBN']}"
        google_response = requests.get(google_books_url)
        google_books_data = google_response.json().get('items', [])

        if not google_books_data:
            books_collection.delete_one({'ID': book_id})
            app.logger.warning('No data found for provided ISBN, book entry deleted')
            return jsonify({'error': 'No data found for provided ISBN'}), 404

        google_books_info = google_books_data[0].get('volumeInfo', {})
        books_collection.update_one(
            {'ID': book_id},
            {'$set': {
                'authors': ' and '.join(google_books_info.get('authors', ['missing'])),
                'publisher': google_books_info.get('publisher', 'missing'),
                'publishedDate': google_books_info.get('publishedDate', 'missing')
            }}
        )

        book = books_collection.find_one({'ID': book_id}, {'_id': False})
        app.logger.info('Book details updated from Google Books: ' + str(book))
        return jsonify({'ID': book_id, **book}), 201
    except Exception as e:
        app.logger.error('Error creating book: ' + str(e))
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/books', methods=['GET'])
def list_books():
    if db is None:
        return jsonify({'error': 'Database connection failed'}), 500

    books = list(books_collection.find({}, {'_id': False}))
    app.logger.info('Listing all books')
    return jsonify(books)

@app.route('/books/<book_id>', methods=['GET', 'PUT', 'DELETE'])
def book_details(book_id):
    if db is None:
        return jsonify({'error': 'Database connection failed'}), 500

    book = books_collection.find_one({'ID': book_id}, {'_id': False})
    if not book:
        app.logger.error('Book not found')
        return jsonify({'error': 'Book not found'}), 404

    if request.method == 'GET':
        return jsonify(book)
    elif request.method == 'PUT':
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid request'}), 400
        update_fields = {key: data[key] for key in ['title', 'ISBN', 'genre', 'authors', 'publisher', 'publishedDate'] if key in data}
        if not update_fields:
            return jsonify({'error': 'Invalid request'}), 400
        books_collection.update_one({'ID': book_id}, {'$set': update_fields})
        app.logger.info('Book details updated for id: ' + book_id)
        return jsonify({'ID': book_id}), 200
    elif request.method == 'DELETE':
        books_collection.delete_one({'ID': book_id})
        app.logger.info('Book deleted with id: ' + book_id)
        return jsonify({'ID': book_id}), 200

@app.route('/books/isbn/<isbn>', methods=['GET'])
def get_book_by_isbn(isbn):
    if db is None:
        return jsonify({'error': 'Database connection failed'}), 500

    book = books_collection.find_one({'ISBN': isbn}, {'_id': False})
    if not book:
        app.logger.error('Book not found by ISBN')
        return jsonify({'error': 'Book not found by ISBN'}), 404

    app.logger.info(f"Book found by ISBN: {book}")
    return jsonify(book)

@app.errorhandler(400)
def bad_request(error):
    return jsonify({'error': 'Invalid request'}), 400

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
