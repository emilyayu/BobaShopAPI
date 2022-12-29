from flask import Blueprint, request, make_response
from google.cloud import datastore
import json
import constants
client = datastore.Client()
from auth import verify_jwt

orders_bp = Blueprint('orders', __name__, url_prefix='/orders')

# from main import verify_jwt
# ORDERS GET/POST/PATCH/DELETE 
@orders_bp.route('', methods=['POST','GET'])
def orders_get_post():
    try:
        payload = verify_jwt(request)
    except Exception:
        error_msg = {
                "Error": "Unauthorized. JWT not verified."
            }            
        res = make_response(json.dumps(error_msg))
        res.mimetype = 'application/json'
        res.status_code = 401
        return res
    if request.method =='POST' and 'application/json' not in request.accept_mimetypes:
        error_msg = {
            "Error": "Not Acceptable. MIME type is not supported."
        }
        res = make_response(json.dumps(error_msg))
        res.mimetype = 'application/json'
        res.status_code = 406
        return res
    if request.method == 'POST' and 'application/json' in request.accept_mimetypes:
        # create a new drink request must be JSON, Response must be JSON:
        
        try:
            content = request.get_json()
            drink_key = client.key (constants.drinks, int(content["drink_id"]))
            drink = client.get(key=drink_key)
            
            if drink_key is None or drink is None:
                error_msg = {
                    "Error": "Not Found. No drink with this drink_id exists."
                }            
                res = make_response(json.dumps(error_msg))
                res.mimetype = 'application/json'
                res.status_code = 404
                return res

            if drink["order_id"] != None:
                error_msg = {
                    "Error": "Order already exists."
                }            
                res = make_response(json.dumps(error_msg))
                res.mimetype = 'application/json'
                res.status_code = 400
                return res

            new_order = datastore.entity.Entity(key=client.key(constants.orders))
            
            order_query = client.query(kind=constants.orders)
            results = list(order_query.fetch())

            # CHECK input types
            if len(content) != 3 or "date" not in content or "drink_id" not in content or "size" not in content:
                error_msg = {
                        "Error" : "Bad Request. The request object is missing at least one of the required attributes."
                    }
                res = make_response(json.dumps(error_msg))
                res.mimetype = 'application/json'
                res.status_code = 400
                return res
        
            elif type(content["drink_id"]) != int or type(content["size"]) != str or type(content["date"]) != str:
                error_msg = {
                        "Error" : "Forbidden. The request object has invalid data type."
                    }
                res = make_response(json.dumps(error_msg))
                res.mimetype = 'application/json'
                res.status_code = 403
                return res
                      
            # Create New Drink
            new_order.update({
                "order_id": None,
                "date": content["date"],
                "customer_information": None,
                "size": content["size"],
                "drink": drink["id"],
                "self": None
            })
            client.put(new_order)
            unique_id = new_order.key.id
            print(unique_id)
            url = request.url + "/" + str(unique_id)
            owner = payload["sub"]

            user_query = client.query(kind=constants.users)
            results = list(user_query.fetch())
            print("LINE99",  results)

            for e in results:
                print(e["user_sub"], owner)
                if e["user_sub"]==owner:
                    user_key = client.key (constants.users, e["user_id"])
                    user = client.get(key=user_key)
                    print("LINE106",user)
                    break
            user.update({
                "order":(unique_id)
            })

            print("LINE106 - owner info", user)

            new_order.update({
                "order_id": unique_id,
                "customer_information": owner,
                "self": url
            })
            print(new_order, unique_id)
            drink.update({
                "order_id": new_order["order_id"]
            })
            client.put(new_order)
            client.put(user)

            client.put(drink)
            res = make_response(new_order)
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
       

# GET
    if request.method == 'GET':
        order_query = client.query(kind=constants.orders)
        order_query = order_query.add_filter("customer_information", "=", payload["sub"])
        # print(order_query.fetch())
        # if order_query.fetch()["customer_information"]!=payload["sub"]:
        #     error_msg = {
        #         "Error": "Unauthorized. JWT not verified."
        #     }            
        #     res = make_response(json.dumps(error_msg))
        #     res.mimetype = 'application/json'
        #     res.status_code = 401
        #     return res
        q_limit = int(request.args.get('limit', '5'))
        q_offset = int(request.args.get('offset', '0'))
        l_iterator = order_query.fetch(limit= q_limit, offset=q_offset)
        pages = l_iterator.pages
        results = list(next(pages))
        if l_iterator.next_page_token:
            next_offset = q_offset + q_limit
            next_url = request.base_url + "?limit=" + str(q_limit) + "&offset=" + str(next_offset)
        else:
            next_url = None    
        output = {"orders": results}
        if next_url:
            output["next"] = next_url
        if 'application/json' in request.accept_mimetypes:
            res = make_response(json.dumps(output))
            res.mimetype = 'application/json'
            res.status_code = 200
            return res
        # elif 'text/html' in request.accept_mimetypes:
        #     results = list(order_query.fetch())
        #     res1 = """<html>
        #             <head></head>
        #             <body>
        #             <ul>
        #             """
        #     res_str = ""
        #     for e in results:
        #         # e["id"] = e.key.id
        #         res_str += "<li>Order ID: " + str(e['order_id']) + "</li>"
        #         res_str += "<ul><li>Date: " + e['date'] + "</li>"
        #         res_str += "<li>Size: " + (e["size"]) + "</li>"
        #         res_str += "<li>Drink: " + str(e['drink']) + "</li>"
        #         res_str += "<li>Owner: " + (e['owner']) + "</li>"
        #         res_str += "<li>Self: " + (e['self']) + "</li></ul>"
        #     res2 = """ 
        #             </ul>
        #             </body> 
        #             </html>
        #             """
        #     res = make_response(res1 + res_str + res2)
        #     res.mimetype = 'text/html'
        #     res.status_code = 200
        #     return res
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

@orders_bp.route('/<order_id>', methods=['PUT', 'PATCH', 'DELETE','GET'])
def drinks_put_patch_delete_Get(order_id):
    try:
        payload = verify_jwt(request)
    except Exception:
        error_msg = {
                "Error": "Unauthorized. JWT not verified."
            }            
        res = make_response(json.dumps(error_msg))
        res.mimetype = 'application/json'
        res.status_code = 401
        return res
    if 'application/json' not in request.accept_mimetypes:
        error_msg={
                "Error": "Unsupported Media Type. Please submit 'application/json' or 'text/html' MIME type."
        }
        res = make_response(error_msg)
        res.mimetype = 'application/json'
        res.status_code = 400
        return res
    try:
        payload = verify_jwt(request)
    except Exception:
        error_msg = {
                "Error": "Unauthorized. JWT not verified."
            }            
        res = make_response(json.dumps(error_msg))
        res.mimetype = 'application/json'
        res.status_code = 401
        return res
    order_key = client.key(constants.orders, int(order_id))
    order = client.get(key=order_key)
    if order["customer_information"] != payload["sub"]:
        error_msg = {
            "Error": "Unauthorized."
        }
        res = make_response(json.dumps(error_msg))
        res.mimetype = 'application/json'
        res.status_code = 401
        return res
    
    if order_key is None or order is None:
        error_msg = {
            "Error": "Not Found. No order with this order_id exists."
        }
        res = make_response(json.dumps(error_msg))
        res.mimetype = 'application/json'
        res.status_code = 404
        return res

    if request.method == 'GET' and 'application/json' in request.accept_mimetypes:   
        res = make_response(json.dumps(order))
        res.mimetype = 'application/json'
        res.status_code = 200
        return res
    
    elif request.method == 'PUT' and 'application/json' in request.accept_mimetypes:
        try:
            # Checks to see if drink_id from input is valid
            content = request.get_json()
            drink_key = client.key (constants.drinks, int(content["drink_id"]))
            drink = client.get(key=drink_key)
            if drink_key is None or drink is None:
                error_msg = {
                    "Error": "Not Found. No drink with this drink_id exists."
                }            
                res = make_response(json.dumps(error_msg))
                res.mimetype = 'application/json'
                res.status_code = 404
                return res
            if drink["order_id"] != None:
                error_msg = {
                    "Error": "Order already exists."
                }            
                res = make_response(json.dumps(error_msg))
                res.mimetype = 'application/json'
                res.status_code = 400
                return res


            order_query = client.query(kind=constants.orders)
            results = list(order_query.fetch())
            # CHECK input types
            if len(content) != 3 or "date" not in content or "drink_id" not in content or "size" not in content:
                error_msg = {
                        "Error" : "Bad Request. The request object is missing at least one of the required attributes."
                    }
                res = make_response(json.dumps(error_msg))
                res.mimetype = 'application/json'
                res.status_code = 400
                return res
        
            elif type(content["size"]) != str or type(content["date"]) != str:
                error_msg = {
                        "Error" : "Forbidden. The request object has invalid data type."
                    }
                res = make_response(json.dumps(error_msg))
                res.mimetype = 'application/json'
                res.status_code = 403
                return res
            olddrink_key = client.key (constants.drinks, int(order["drink_id"]))
            old_drink=client.get(key=olddrink_key)
            old_drink.update(
                    {
                        "order_id": None
                    })
            client.put(old_drink)


            owner = payload["sub"]
            order.update({
                "date": content["date"],
                "owner": owner,
                "size": content["size"],
                "drink": drink["id"],
            })
            client.put(order)
            drink.update({
                "order_id": order["order_id"]
            })
            client.put(drink)
            res = make_response(order)
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



    elif request.method == 'PATCH' and 'application/json' in request.accept_mimetypes:
        try:
            content = request.get_json()
            order_query = client.query(kind=constants.orders)
            results = list(order_query.fetch())
            if len(content) == 0:
                error_msg={
                    "Error": "The request object is missing at least one of the required attributes"
                }
                res = make_response(error_msg)
                res.mimetype = 'application/json'
                res.status_code = 400
                return res
            owner = payload["sub"]
            if "drink_id" in content:
                try:
                    olddrink_key = client.key (constants.drinks, int(order["drink_id"]))
                    old_drink=client.get(key=olddrink_key)
                    drink_key = client.key (constants.drinks, int(content["drink_id"]))
                    drink = client.get(key=drink_key)
                    # print(drink_key, drink)
                except Exception:
                    error_msg = {
                        "Error": "Not Found. No drink with this drink_id exists."
                    }            
                    res = make_response(json.dumps(error_msg))
                    res.mimetype = 'application/json'
                    res.status_code = 404
                    return res

                if drink["order_id"] != None:
                    error_msg = {
                        "Error": "Order already exists."
                    }            
                    res = make_response(json.dumps(error_msg))
                    res.mimetype = 'application/json'
                    res.status_code = 400
                    return res

                if drink_key is None or drink is None:
                    error_msg = {
                        "Error": "Not Found. No drink with this drink_id exists."
                    }            
                    res = make_response(json.dumps(error_msg))
                    res.mimetype = 'application/json'
                    res.status_code = 404
                    return res
                old_drink.update(
                    {
                        "order_id": None
                    })
                client.put(old_drink)
                order.update(
                    {
                        "drink": content["drink_id"]
                    }
                    )
                    
                client.put(order)
                print(order)
                drink.update(
                    {
                        "order_id": order["order_id"]
                    })
                client.put(drink)
                print("LINE275",order,drink)

            if "date" in content:
                if type(content["date"]) != str:
                    error_msg = {
                        "Error" : "Forbidden. The request object has invalid data type."
                    }
                    res = make_response(json.dumps(error_msg))
                    res.mimetype = 'application/json'
                    res.status_code = 403
                    return res
               
                order.update(
                    {
                        "owner": owner,
                        "date": content["date"]
                    }
                    )
                client.put(order)
            if "size" in content:
                if type(content["size"]) != str:
                    error_msg = {
                        "Error" : "Forbidden. The request object has invalid data type."
                    }
                    res = make_response(json.dumps(error_msg))
                    res.mimetype = 'application/json'
                    res.status_code = 403
                    return res
               
                order.update(
                    {
                        "owner": owner,
                        "size": content["size"]
                    }
                    )
                client.put(order)
           
            res = make_response(json.dumps(order))
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


    elif request.method == 'DELETE' and 'application/json' in request.accept_mimetypes:
        drink_order = order["drink"]
        drink_query = client.query(kind=constants.drinks)
        drink_key = client.key (constants.drinks, drink_order)
        drink = client.get(key=drink_key)

        results = list(drink_query.fetch())
        for e in results:
            if e["id"]==drink_order:
                drink.update(
                    {
                        "order_id": None
                    })
                client.put(drink)
        client.delete(order)
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