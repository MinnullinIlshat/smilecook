from flask import Flask
from flask_restful import Api
from flask_migrate import Migrate

from config import Config
from extensions import db, jwt
from resources.user import UserListResource, UserResource, MeResource
from resources.recipe import RecipeListResource, RecipeResource, RecipePublishResource
from resources.token_res import TokenResource, RefreshResource, RevokeResource, black_list


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    register_extensions(app)
    register_resources(app)

    return app 

def register_extensions(app):
    db.app = app
    db.init_app(app)
    migrate = Migrate(app, db)
    jwt.init_app(app)

    @jwt.token_in_blocklist_loader
    def check_if_token_is_revoked(jwt_header, jwt_payload: dict):
        jti = jwt_payload['jti']
        return jti in black_list

def register_resources(app):
    api = Api(app)

    api.add_resource(MeResource, '/me')
    api.add_resource(UserListResource, '/users')
    api.add_resource(UserResource, '/users/<string:username>')

    api.add_resource(TokenResource, '/token')
    api.add_resource(RefreshResource, '/refresh')
    api.add_resource(RevokeResource, '/revoke')

    api.add_resource(RecipeListResource, '/recipes')
    api.add_resource(RecipeResource, '/recipes/<int:recipe_id>')
    api.add_resource(RecipePublishResource, '/recipes/<int:recipe_id>/publish')


if __name__ == '__main__':
    app = create_app()
    app.run()