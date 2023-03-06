import redis
from http import HTTPStatus 
from flask import request 
from flask_restful import Resource 
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required, 
    get_jwt_identity,
    get_jwt,
)

from utils import check_password 
from models.user import User
from config import ACCESS_EXPIRES

jwt_redis_blocklist = redis.StrictRedis(
    host="localhost", port=6379, db=0, decode_responses=True
)

class TokenResource(Resource):
    def post(self):
        json_data = request.get_json()
        email = json_data.get('email')
        password = json_data.get('password')
        user = User.get_by_email(email=email)
        if not user or not check_password(password, user.password):
            return {"message": "email or password is incorrect"}, HTTPStatus.UNAUTHORIZED
        if not user.is_active:
            return {"message": "The user account is not activated yet"}, HTTPStatus.FORBIDDEN
        
        access_token = create_access_token(identity=user.id, fresh=True)
        refresh_token = create_refresh_token(identity=user.id)

        return {"access_token": access_token,
                "refresh_token": refresh_token}, HTTPStatus.OK
    

class RefreshResource(Resource):
    @jwt_required(refresh=True)
    def post(self):
        current_user = get_jwt_identity() 

        access_token = create_access_token(identity=current_user, fresh=False)

        return {"access_token": access_token}, HTTPStatus.OK
    

class RevokeResource(Resource):
    @jwt_required(verify_type=False)
    def post(self):
        token = get_jwt()
        jti = token['jti']
        ttype = token["type"]
        jwt_redis_blocklist.set(jti, "", ex=ACCESS_EXPIRES)
        return {"message": f"{ttype.capitalize()} token successfully revoked"}, HTTPStatus.OK