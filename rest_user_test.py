import requests
import getpass
import json

username = input("email: ")
password = getpass.getpass()

base_uri = 'https://weitblicker.org'
photo = '/home/spuetz/Pictures/puetz.jpeg'
#base_uri = 'http://localhost:8000'

login_uri = '/rest/auth/login/'
logout_uri = '/rest/auth/logout/'
user_data_uri = '/rest/auth/user/'
user_pw_change_uri = '/rest/auth/password/change/'
cycle_tours_uri = '/rest/cycle/tours/'
cycle_ranking_uri = '/rest/cycle/ranking/'
cycle_add_segment_uri = '/rest/cycle/segment/'
reset_password_uri = '/rest/auth/password/reset/'

def login(username, password):
    login_request_header = {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }

    login_request_body = {
        'email': username,
        'password': password
    }

    print("login...")
    response = requests.post(
        base_uri+login_uri,
        data=json.dumps(login_request_body),
        headers=login_request_header
    )

    print(response.content)
    return json.loads(response.content)['key']


def logout(token):
    print("logout...")
    header = {'Authorization': 'Token ' + token}
    response = requests.post(base_uri+logout_uri, headers=header)
    print(response.content)


def user_data(token):
    print("user data...")
    header = {'Authorization': 'Token ' + token}
    response = requests.get(base_uri+user_data_uri, headers=header)
    print(response.content)
    return response.content


def upload_user_photo(data, token, photo):
    print("upload user photo...")
    header = {
        'Authorization': 'Token ' + token,
        'Accept': 'application/json',
    }
    response = requests.post(
        base_uri+user_data_uri,
        headers=header,
        files={'image': open(photo, 'rb')},
        data=json.loads(data)
    )
    print(response.content)


def change_password(token):
    print("change password...")

    header = {
        'Authorization': 'Token ' + token,
        'Accept': 'application/json',
    }

    new_password1 = input("New Password: ")
    new_password2 = input("Password repeat: ")
    pw_data = {
        'new_password1': new_password1,
        'new_password2': new_password2
    }

    response = requests.post(
        base_uri + user_pw_change_uri,
        headers=header,
        data=pw_data)

    print("response: ", response.content)


def cycle_user_tours(token):
    print("user tours...")
    header = {
        'Authorization': 'Token ' + token,
        'Accept': 'application/json',
    }
    response = requests.get(base_uri + cycle_tours_uri, headers=header)
    print("response: ", response.content)


def cycle_ranking(token=None):
    print("cycle ranking...")
    header = {'Accept': 'application/json'}
    if token:
        header['Authorization'] = 'Token ' + token

    response = requests.get(base_uri + cycle_ranking_uri, headers=header)
    print("response: ", response.content)


def cycle_add_segment(token, ):
    print("cycle add segment...")
    header = {
        'Authorization': 'Token ' + token,
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }

    segment = {
        "start": "2019-10-01T07:08:04Z",
        "end": "2019-10-01T07:08:14Z",
        "distance": 0.16,
        "project": 1,
        "tour": 0,
    }

    response = requests.post(base_uri + cycle_add_segment_uri, headers=header, data=json.dumps(segment))
    print("response: ", response.content)


def reset_password(email):
    print("reset password...")
    header = {'Accept': 'application/json',
              'Content-Type': 'application/json'}
    data = {'email': email}
    response = requests.post(base_uri + reset_password_uri,  headers=header, data=json.dumps(data))
    print("response: ", response.content)


token = login(username, password)
data = user_data(token)
reset_password(username)
#cycle_user_tours(token)
#cycle_ranking(token)
#cycle_add_segment(token)
#logout(token)
#cycle_ranking()
#logout(token)
#token = login(username, password)
#upload_user_photo(data, token, photo)
#change_password(token)
