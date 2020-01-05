from appdirs import AppDirs
import requests
import os, json, getpass, time
from .exceptions import *

directories = AppDirs("Astrocyte", "Alexandria")
__repo_url__ = "https://pi.glia-pkg.org/"
__url__ = "https://api.glia-pkg.org/"

def upload_meta(pkg):
    token = get_valid_token()
    response = requests.post(__url__ + '/packages',
        headers={'Accept': 'application/json', 'Authorization': 'Bearer ' + token},
        json={'name': pkg.name, 'title': pkg.package_name}
    )
    content = json.loads(response.content)
    if response.status_code == 201:
        print("Succesfully uploaded package metadata")
        return True
    else:
        raise GliaApiError("Package API responded with code {}: {}".format(response.status_code, content["errors"][0]["error_description"]))

def _mkdir():
    try:
        os.makedirs(directories.user_data_dir)
    except Exception as e:
        pass

def read_storage():
    _mkdir()
    try:
        with open(os.path.join(directories.user_data_dir, ".astro"), "r") as f:
            data = json.load(f)
        return data
    except Exception as e:
        return None

def write_storage(data):
    _mkdir()
    with open(os.path.join(directories.user_data_dir, ".astro"), "w") as f:
        json.dump(data, f)

def init_storage():
    return {"tokens": {}}

def _store_tokens(body):
    access_token = body["access_token"]
    expires_in = body["expires_in"]
    data = read_storage() or init_storage()
    data["tokens"] = {
        "access_token": access_token,
        "expires_at": time.time() + expires_in - 10
    }
    if "refresh_token" in body:
        data["tokens"]["refresh_token"] = body["refresh_token"]
    write_storage(data)
    return access_token

def _authenticate():
    body = _prompt_authentication()
    return _store_tokens(body)

def _refresh_token(refresh_token):
    response = requests.get(
        __url__ + '/refresh_token',
        params={"token": refresh_token}
    )
    if response.status_code == 200:
        content = json.loads(response.content)
        _store_tokens(content)
        return content["access_token"]
    else:
        return _authenticate()

def get_valid_token():
    data = read_storage()
    if data:
        if "tokens" in data:
            if data["tokens"]["expires_at"] < time.time():
                if "refresh_token" in data["tokens"]:
                    return _refresh_token(data["tokens"]["refresh_token"])
                else:
                    return _authenticate()
            return data["tokens"]["access_token"]
    return _authenticate()

def _prompt_authentication():
    username = input('Username: ')
    password = getpass.getpass()
    remember_me = input('Stay logged in (y/n)? ').lower() == 'y'
    response = requests.get(
        __url__ + '/token',
        auth=(username, password),
        params={'remember_me': remember_me}
    )
    if response.status_code == 200:
        content = json.loads(response.content)
        token = content["access_token"]
        return content
    else:
        if response.status_code >= 500:
            raise GliaApiError("Package API unavailable.")
        else:
            content = json.loads(response.content)
            raise GliaApiError("Package API responded with code {}: {}".format(response.status_code, content["errors"][0]["error_description"]))

def check_token():
    token = get_valid_token()
    response = requests.get(
        __url__ + '/verify_token',
        params={'token': token}
    )
    return json.loads(response.content)["active"]
