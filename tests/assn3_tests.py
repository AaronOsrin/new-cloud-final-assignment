import requests

base_url = 'http://localhost:5001/books'
book1 = {
    'title': 'Adventures of Huckleberry Finn',
    'ISBN': '9780520343641',
    'genre': 'Fiction'
}
book2 = {
    'title': 'Pride and Prejudice',
    'ISBN': '9780141199078',
    'genre': 'Romance'
}
book3 = {
    'title': 'To Kill a Mockingbird',
    'ISBN': '9780061120084',
    'genre': 'Fiction'
}
book4 = {
    'title': 'Nonexistent Book',
    'ISBN': '1234567890123',
    'genre': 'Fiction'
}
book5 = {
    'title': 'Unknown Genre Book',
    'ISBN': '9780061120084',
    'genre': 'Unknown'
}
invalid_book = {
    'title': '',
    'ISBN': '',
    'genre': ''
}

def test_create_books():
    response1 = requests.post(base_url, json=book1)
    print(f"Create book1 response: {response1.status_code}, {response1.json()}")
    assert response1.status_code == 201
    assert 'ID' in response1.json()
    book1['id'] = response1.json()['ID']

    response2 = requests.post(base_url, json=book2)
    print(f"Create book2 response: {response2.status_code}, {response2.json()}")
    assert response2.status_code == 201
    assert 'ID' in response2.json()
    book2['id'] = response2.json()['ID']

    response3 = requests.post(base_url, json=book3)
    print(f"Create book3 response: {response3.status_code}, {response3.json()}")
    assert response3.status_code == 201
    assert 'ID' in response3.json()
    book3['id'] = response3.json()['ID']

    assert book1['id'] != book2['id'] != book3['id']

def test_invalid_isbn():
    response = requests.post(base_url, json=book4)
    print(f"Invalid ISBN book response: {response.status_code}, {response.json()}")
    assert response.status_code in [400, 404, 500]  # Added 404 here

def test_invalid_genre():
    response = requests.post(base_url, json=book5)
    print(f"Invalid genre book response: {response.status_code}, {response.json()}")
    assert response.status_code == 422

def test_get_book1():
    response = requests.get(f"{base_url}/isbn/{book1['ISBN']}")
    print(f"Get book1 response: {response.status_code}, {response.json()}")
    assert response.status_code == 200

def test_list_books():
    response = requests.get(base_url)
    print(f"List books response: {response.status_code}, {response.json()}")
    assert response.status_code == 200

def test_update_book():
    response = requests.get(f"{base_url}/isbn/{book1['ISBN']}")
    print(f"Get book1 for update response: {response.status_code}, {response.json()}")
    book_data = response.json()
    book_id = book_data.get('ID')
    update_data = {
        'title': 'Adventures of Tom Sawyer',
        'ISBN': '9780520343641',
        'genre': 'Fiction',
        'authors': book_data.get('authors'),
        'publisher': book_data.get('publisher'),
        'publishedDate': book_data.get('publishedDate')
    }
    response = requests.put(f"{base_url}/{book_id}", json=update_data)
    print(f"Update book response: {response.status_code}, {response.json()}")
    assert response.status_code == 200

def test_delete_book2():
    response = requests.get(f"{base_url}/isbn/{book2['ISBN']}")
    print(f"Get book2 for delete response: {response.status_code}, {response.json()}")
    book_data = response.json()
    book_id = book_data.get('ID')
    response = requests.delete(f"{base_url}/{book_id}")
    print(f"Delete book2 response: {response.status_code}, {response.json()}")
    assert response.status_code == 200

def test_get_deleted_book2():
    response = requests.get(f"{base_url}/isbn/{book2['ISBN']}")
    print(f"Get deleted book2 response: {response.status_code}, {response.json()}")
    assert response.status_code == 404

def test_invalid_book():
    response = requests.post(base_url, json=invalid_book)
    print(f"Invalid book response: {response.status_code}, {response.json()}")
    assert response.status_code in [400, 500]
