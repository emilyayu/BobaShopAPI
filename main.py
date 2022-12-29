# Name: Emily Yu
# Course: CS 493 - Cloud Application Development
# Code adapted from Module 7 code and tutorial for auth0

from flask import Blueprint,render_template, Flask, request, jsonify
from flask import Flask, make_response, redirect, render_template, session, url_for

app = Flask(__name__)
app.secret_key = 'SECRET_KEY'

from drinks import drinks_bp
from orders import orders_bp
from users import users_bp
from auth import auth_bp
app.register_blueprint(auth_bp)
app.register_blueprint(drinks_bp, url_prefix='/drinks')
app.register_blueprint(orders_bp, url_prefix='/orders')
app.register_blueprint(users_bp, url_prefix='/users')

if __name__ == '__main__':
    app.run(host='localhost', port=8080, debug=True)
