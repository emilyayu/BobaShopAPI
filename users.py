from flask import Blueprint, request, make_response
from google.cloud import datastore
import json
import constants
# from main import verify_jwt


client = datastore.Client()

users_bp = Blueprint('users', __name__)

# DRINKS GET/POST/PATCH/DELETE 
@users_bp.route('', methods=['GET'])
def users_get():
    # print("bp", request.accept_mimetypes)
    if 'application/json' not in request.accept_mimetypes:
        error_msg = {
            "Error": "Unsupported Media Type. Please submit 'application/json' MIME type."
        }
        res = make_response(error_msg)
        res.mimetype = 'application/json'
        res.status_code = 415
        return res

    if request.method == 'GET' and 'application/json' in request.accept_mimetypes:
        user_query = client.query(kind=constants.users)
        results = list(user_query.fetch())
        q_limit = int(request.args.get('limit', '5'))
        q_offset = int(request.args.get('offset', '0'))
        l_iterator = user_query.fetch(limit= q_limit, offset=q_offset)
        pages = l_iterator.pages
        results = list(next(pages))
        if l_iterator.next_page_token:
            next_offset = q_offset + q_limit
            next_url = request.base_url + "?limit=" + str(q_limit) + "&offset=" + str(next_offset)
        else:
            next_url = None
        for e in results:
            e["id"] = e.key.id
        output = {"users": results}
        if next_url:
            output["next"] = next_url
        if 'application/json' in request.accept_mimetypes:
            res = make_response(json.dumps(output))
            res.mimetype = 'application/json'
            res.status_code = 200
            return res
        
    elif request.method == 'GET' and 'application/json' not in request.accept_mimetypes:
        error_msg = {
            "Error": "Unsupported Media Type. Please submit 'application/json' MIME type."
        }
        res = make_response(error_msg)
        res.mimetype = 'application/json'
        res.status_code = 415
        return res

    else:
            error_msg={
                "Error": "Method Not Allowed. Allowed Methods: GET."
            }
            res = make_response(error_msg)
            res.mimetype = 'application/json'
            res.status_code = 405
            return res