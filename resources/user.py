import os 
import uuid
from flask import request, url_for, current_app
from flask_restful import Resource 
from flask_jwt_extended import get_jwt_identity, jwt_required
from werkzeug.utils import secure_filename
from marshmallow import ValidationError
from http import HTTPStatus 

from webargs import fields 
from webargs.flaskparser import use_kwargs

from models.user import User
from models.recipe import Recipe 

from mailgun import MailgunApi
from utils import generate_token, verify_token, allowed_file, compress_image

from schemas.user import UserSchema 
from schemas.recipe import RecipeSchema 

user_schema = UserSchema()
user_public_schema = UserSchema(exclude=('email',))
user_avatar_schema = UserSchema(only=('avatar_url',))
recipe_list_schema = RecipeSchema(many=True)

mailgun = MailgunApi(domain='sandbox2d9b7c287df94e25b2eca7aa0afddae1.mailgun.org',
                     api_key='53f31d1dda35940d2006a9efa71f81a6-15b35dee-c0fbbb20')

class UserListResource(Resource):
    def post(self):
        json_data = request.get_json()

        try:
            data = user_schema.load(data=json_data)
        except ValidationError as err:
            return {"messages": "Validation errors", "errors": err.messages}, HTTPStatus.BAD_REQUEST

        if User.get_by_username(data.get('username')):
            return {"message": "username already used"}, HTTPStatus.BAD_REQUEST
        
        if User.get_by_email(data.get('email')):
            return {"message": "email already used"}, HTTPStatus.BAD_REQUEST
        
        user = User(**data)
        token = generate_token(user.email, salt='activate')
        subject = 'Please confirm your registration.'
        link = url_for('useractivateresource',
                       token=token, 
                       _external=True)
        text = f'Hi, Thanks for using SmileCook! Please confirm your\
            registration by clicking on the link: {link}'
        mailgun.send_email(to=user.email, subject=subject, text=text)
        user.save() 

        return user_schema.dump(user), HTTPStatus.CREATED
    

class UserResource(Resource):
    @jwt_required(optional=True)
    def get(self, username):
        user = User.get_by_username(username=username)

        if user is None:
            return {"message": "user not found"}, HTTPStatus.NOT_FOUND
        
        current_user = get_jwt_identity()

        if current_user == user.id:
            data = user_schema.dump(user)
        else: 
            data = user_public_schema.dump(user)
        
        return data, HTTPStatus.OK
    

class MeResource(Resource):
    @jwt_required()
    def get(self):
        user = User.get_by_id(id=get_jwt_identity())
        return user_schema.dump(user), HTTPStatus.OK
    

class UserRecipeListResource(Resource):
    @jwt_required(optional=True)
    @use_kwargs({'visibility': fields.Str(missing='public')})
    def get(self, username, visibility):
        user = User.get_by_username(username=username)

        if user is None:
            return {"message": "User not found"}, HTTPStatus.NOT_FOUND 
        
        current_user = get_jwt_identity()

        if current_user != user.id and visibility in ['all', 'private']:
            visibility = 'public'

        recipes = Recipe.get_all_by_user(user_id=user.id, visibility=visibility)

        return recipe_list_schema.dump(recipes), HTTPStatus.OK
    
class UserActivateResource(Resource):
    def get(self, token):
        email = verify_token(token, salt='activate')

        if email is False:
            return {"message": "Invalid token or token expired"}, HTTPStatus.BAD_REQUEST
        
        user = User.get_by_email(email=email)
        
        if not user:
            return {"message": "User not found."}, HTTPStatus.NOT_FOUND
        
        if user.is_active is True:
            return {"message": "The user account is already activated."}, HTTPStatus.BAD_REQUEST
        
        user.is_active = True 
        user.save()
        return {}, HTTPStatus.NO_CONTENT
    

class UserAvatarUploadResource(Resource):
    @jwt_required()
    def put(self):
        file = request.files.get('avatar')
        if not file:
            return {"message": "Not a valid iamge"}, HTTPStatus.BAD_REQUEST
        
        if not allowed_file(filename=file.filename):
            return {"message": "File type not allowed"}, HTTPStatus.BAD_REQUEST
        
        user = User.get_by_id(id=get_jwt_identity())

        if user.avatar_image:
            avatar_path = os.path.join(
                current_app.config['UPLOADED_IMAGES_DEST'], 
                f"avatars/{user.avatar_image}")
            if os.path.exists(avatar_path):
                os.remove(avatar_path)
                
        filename = secure_filename(file.filename)
        extension = filename.rsplit('.', 1)[1].lower()
        filename = f'{uuid.uuid4()}.{extension}'
        
        file.save(os.path.join(
            current_app.config['UPLOADED_IMAGES_DEST'], 
            f"avatars/{filename}"))
        
        filename = compress_image(filename, 
            current_app.config['UPLOADED_IMAGES_DEST'] + "/avatars")
        
        user.avatar_image = filename 
        user.save() 
        
        return user_avatar_schema.dump(user), HTTPStatus.OK