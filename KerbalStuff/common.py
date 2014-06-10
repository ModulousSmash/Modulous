from flask import session, jsonify, redirect, request
from functools import wraps
from KerbalStuff.objects import User

import json
import urllib

def get_user():
    if 'user' in session:
        return User.query.filter_by(username=session['user']).first()
    return None

def loginrequired(f):
    # TODO: Handle users who haven't confirmed
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not get_user():
            return redirect("/login?return_to=" + urllib.parse.quote_plus(request.url))
        else:
            return f(*args, **kwargs)
    return wrapper

def json_output(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        def jsonify_wrap(obj):
            jsonification = json.dumps(obj)
            print(obj)
            print(jsonification)
            return jsonification

        result = f(*args, **kwargs)
        if isinstance(result, tuple):
            return jsonify_wrap(result[0]), result[1]
        if isinstance(result, dict):
            return jsonify_wrap(result)
        if isinstance(result, list):
            return jsonify_wrap(result)

        # This is a fully fleshed out  response, return it immediately
        return result

    return wrapper

def cors(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        res = f(*args, **kwargs)
        if request.headers.get('x-cors-status', False):
            if isinstance(res, tuple):
                json_text = res[0].data
                code = res[1]
            else:
                json_text = res.data
                code = 200

            o = json.loads(json_text)
            o['x-status'] = code

            return jsonify(o)

        return res

    return wrapper


