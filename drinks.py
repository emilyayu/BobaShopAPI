from flask import Blueprint, request, make_response
from google.cloud import datastore
import json
import constants
# from main import verify_jwt


client = datastore.Client()

drinks_bp = Blueprint('drinks', __name__)

# DRINKS GET/POST/PATCH/DELETE 
@drinks_bp.route('', methods=['POST','GET'])
def drinks_get_post():
    if request.method == 'POST' and 'application/json' in request.accept_mimetypes:
        # create a new drink request must be JSON, Response must be JSON:
        
        # payload = verify_jwt(request)
        try:

            content = request.get_json()
            new_drink = datastore.entity.Entity(key=client.key(constants.drinks))
            
            drink_query = client.query(kind=constants.drinks)
            results = list(drink_query.fetch())

            # CHECK input types
            if len(content) != 3 or "name" not in content or "topping" not in content or "tea" not in content:
                error_msg = {
                        "Error" : "Bad Request. The request object is missing at least one of the required attributes."
                    }
                res = make_response(json.dumps(error_msg))
                res.mimetype = 'application/json'
                res.status_code = 400
                return res
        
            elif type(content["name"]) != str or type(content["topping"]) != str or type(content["tea"]) != str:
                error_msg = {
                        "Error" : "Forbidden. The request object has invalid data type."
                    }
                res = make_response(json.dumps(error_msg))
                res.mimetype = 'application/json'
                res.status_code = 403
                return res
            
            for e in results:
                if content["name"] == e["name"]:
                    error_msg = {
                        "Error" : "Forbidden. The request object ['name'] is not unique."
                    }
                    res = make_response(json.dumps(error_msg))
                    res.mimetype = 'application/json'
                    res.status_code = 403
                    return res
            # Create New Drink
            new_drink.update({
                "id": None,
                "name": content["name"],
                "tea": content["tea"],
                "topping": content["topping"],
                "order_id": None,
                "self": None
            })
            # print("NEW DRINK -", new_drink)
            client.put(new_drink)
            unique_id = new_drink.key.id
            url = request.url + "/" + str(unique_id)
            new_drink.update({
                "id": unique_id,
                "name": content["name"],
                "tea": content["tea"],
                "topping": content["topping"],
                "order_id": None,
                "self": url
            })
            client.put(new_drink)
            res = make_response(new_drink)
            res.mimetype = 'application/json'
            res.status_code = 201
            return res
        except Exception:
            error_msg={
                "Error": "The request object is missing at least one of the required attributes"
            }
            res = make_response(error_msg)
            res.mimetype = 'application/json'
            res.status_code = 400
            return res
    elif request.method == 'POST':
        error_msg = {
            "Error": "Not Acceptable. MIME type is not supported."
        }
        res = make_response(json.dumps(error_msg))
        res.mimetype = 'application/json'
        res.status_code = 406
        return res

# GET
    if request.method == 'GET':
        drink_query = client.query(kind=constants.drinks)
        results = list(drink_query.fetch())
        q_limit = int(request.args.get('limit', '5'))
        q_offset = int(request.args.get('offset', '0'))
        l_iterator = drink_query.fetch(limit= q_limit, offset=q_offset)
        pages = l_iterator.pages
        results = list(next(pages))
        if l_iterator.next_page_token:
            next_offset = q_offset + q_limit
            next_url = request.base_url + "?limit=" + str(q_limit) + "&offset=" + str(next_offset)
        else:
            next_url = None
        for e in results:
            e["id"] = e.key.id
        output = {"drinks": results}
        if next_url:
            output["next"] = next_url
        if 'application/json' in request.accept_mimetypes:
            res = make_response(json.dumps(output))
            res.mimetype = 'application/json'
            res.status_code = 200
            return res
        elif 'text/html' in request.accept_mimetypes:
            results = list(drink_query.fetch())
            res1 = """<html>
                    <head></head>
                    <body>
                    <ul>
                    """
            res_str = ""
            for e in results:
                e["id"] = e.key.id
                res_str += "<li>Drink ID: " + str(e["id"]) + "</li>"
                res_str += "<ul><li>Name: " + e["name"] + "</li>"
                res_str += "<li>Tea: " + (e["tea"]) + "</li>"
                res_str += "<li>Topping: " + str(e["topping"]) + "</li>"
                res_str += "<li>Order: " + str(e["order_id"]) + "</li>"
                res_str += "<li>Self: " + (e["self"]) + "</li></ul>"
            res2 = """ 
                    </ul>
                    </body> 
                    </html>
                    """
            res = make_response(res1 + res_str + res2)
            res.mimetype = 'text/html'
            res.status_code = 200
            return res
        else:
            error_msg = {
                "Error": "Unsupported Media Type. Please submit 'application/json' or 'text/html' MIME type."
            }
            res = make_response(error_msg)
            res.mimetype = 'application/json'
            res.status_code = 415
            return res

    else:
            error_msg={
                "Error": "Method Not Allowed. Allowed Methods: GET, POST."
            }
            res = make_response(error_msg)
            res.mimetype = 'application/json'
            res.status_code = 405
            return res

@drinks_bp.route('/<drink_id>', methods=['PUT', 'PATCH', 'DELETE','GET'])
def drinks_put_patch_delete_Get(drink_id):
    drink_key = client.key(constants.drinks, int(drink_id))
    drink = client.get(key=drink_key)


    if drink_key is None or drink is None:
        error_msg = {
            "Error": "Not Found. No drink with this drink_id exists."
        }
        res = make_response(json.dumps(error_msg))
        res.mimetype = 'application/json'
        res.status_code = 404
        return res
    if request.method == 'GET':   
        res = make_response(json.dumps(drink))
        res.mimetype = 'application/json'
        res.status_code = 200
        return res
    
    if request.method == 'PUT':
        try:
            content = request.get_json()
            drink_query = client.query(kind=constants.drinks)
            results = list(drink_query.fetch())

            # print("line 186:", content)
            # CHECK input types
            if len(content) != 3 or "name" not in content or "topping" not in content or "tea" not in content:
                error_msg = {
                        "Error" : "Bad Request. The request object is missing at least one of the required attributes."
                    }
                res = make_response(json.dumps(error_msg))
                res.mimetype = 'application/json'
                res.status_code = 400
                return res
        
            elif type(content["name"]) != str or type(content["topping"]) != str or type(content["tea"]) != str:
                error_msg = {
                        "Error" : "Forbidden. The request object has invalid data type."
                    }
                res = make_response(json.dumps(error_msg))
                res.mimetype = 'application/json'
                res.status_code = 403
                return res
            
            for e in results:
                if content["name"] == e["name"] and drink["name"]!= content["name"]:
                    error_msg = {
                        "Error" : "Forbidden. The request object ['name'] is not unique."
                    }
                    res = make_response(json.dumps(error_msg))
                    res.mimetype = 'application/json'
                    res.status_code = 403
                    return res
            drink.update(
                {
                    "name": content["name"], 
                    "tea": content["tea"],
                    "topping": content["topping"]
                })
            client.put(drink)
            res = make_response(json.dumps(drink))
            res.mimetype = 'application/json'
            res.status_code = 200
            return res
        except Exception:
            error_msg={
                "Error": "The request object is missing at least one of the required attributes"
            }
            res = make_response(error_msg)
            res.mimetype = 'application/json'
            res.status_code = 400
            return res

    if request.method == 'PATCH':
        try:

            content = request.get_json()
            drink_query = client.query(kind=constants.drinks)
            results = list(drink_query.fetch())
            if len(content) == 0:
                error_msg={
                    "Error": "The request object is missing at least one of the required attributes"
                }
                res = make_response(error_msg)
                res.mimetype = 'application/json'
                res.status_code = 400
                return res
            if "name" in content:
                if type(content["name"]) != str:
                    error_msg = {
                        "Error" : "Forbidden. The request object has invalid data type."
                    }
                    res = make_response(json.dumps(error_msg))
                    res.mimetype = 'application/json'
                    res.status_code = 403
                    return res
                for e in results:
                    if content["name"] == e["name"] and drink["name"]!= content["name"]:
                        error_msg = {
                            "Error" : "Forbidden. The request object ['name'] is not unique."
                        }
                        res = make_response(json.dumps(error_msg))
                        res.mimetype = 'application/json'
                        res.status_code = 403
                        return res
                drink.update(
                    {
                        "name": content["name"]
                    }
                    )
                client.put(drink)
            if "tea" in content:
                if type(content["tea"]) != str:
                    error_msg = {
                        "Error" : "Forbidden. The request object has invalid data type."
                    }
                    res = make_response(json.dumps(error_msg))
                    res.mimetype = 'application/json'
                    res.status_code = 403
                    return res
                
                drink.update(
                    {
                        "tea": content["tea"]
                    }
                    )
                client.put(drink)
            if "topping" in content:
                if type(content["topping"]) != str:
                    error_msg = {
                        "Error" : "Forbidden. The request object has invalid data type."
                    }
                    res = make_response(json.dumps(error_msg))
                    res.mimetype = 'application/json'
                    res.status_code = 403
                    return res
                
                drink.update(
                    {
                        "topping": content["topping"]
                    }
                    )
                client.put(drink)
            
            res = make_response(json.dumps(drink))
            res.mimetype = 'application/json'
            res.status_code = 200
            return res
        except Exception:
            error_msg={
                "Error": "The request object is missing at least one of the required attributes"
            }
            res = make_response(error_msg)
            res.mimetype = 'application/json'
            res.status_code = 400
            return res


    if request.method == 'DELETE':
        if (drink["order_id"]) != None:
            client.delete(drink)
            order_id = drink["order_id"]
            order_key = client.key (constants.order, order_id)
            order = client.get (key=order_key)
            order["drink_id"] = None
            client.put(order)

        client.delete(drink)
        res = make_response('')
        res.mimetype = 'application/json'
        res.status_code = 204
        return res
    else:
        error_msg={
                "Error": "Method Not Allowed. Allowed Methods: GET, PUT, POST."
        }
        res = make_response(error_msg)
        res.mimetype = 'application/json'
        res.status_code = 405
        return res