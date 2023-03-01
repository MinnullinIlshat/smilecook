from flask import request 
from flask_restful import Resource
from flask_jwt_extended import get_jwt_identity, jwt_required
from marshmallow import ValidationError
from http import HTTPStatus 

from models.recipe import Recipe
from schemas.recipe import RecipeSchema

recipe_schema = RecipeSchema()
recipe_list_schema = RecipeSchema(many=True)


class RecipeListResource(Resource):
    def get(self):
        
        recipes = Recipe.get_all_published()

        return recipe_list_schema.dump(recipes), HTTPStatus.OK

    @jwt_required(optional=False)
    def post(self):
        json_data = request.get_json()
        current_user = get_jwt_identity()

        try:
            data = recipe_schema.load(data=json_data)
        except ValidationError as err:
            return {"message": "Validation errors", 'errors': err.messages}, HTTPStatus.BAD_REQUEST
        
        recipe = Recipe(**data)
        recipe.user_id = current_user
        recipe.save()

        return recipe_schema.dump(recipe), HTTPStatus.CREATED


class RecipeResource(Resource):
    @jwt_required(optional=True)
    def get(self, recipe_id):
        recipe = Recipe.get_by_id(recipe_id=recipe_id)

        if recipe is None:
            return {'message': 'recipe not found'}, HTTPStatus.NOT_FOUND
        
        current_user = get_jwt_identity()

        if not recipe.is_publish and recipe.user_id != current_user:
            return {"message": 'Access is not allowed'}, HTTPStatus.FORBIDDEN
        
        return recipe_schema.dump(recipe), HTTPStatus.OK 

    @jwt_required(optional=False)
    def put(self, recipe_id):
        json_data = request.get_json()

        recipe = Recipe.get_by_id(recipe_id=recipe_id)
        
        if recipe is None:
            return {'message': 'recipe not found'}, HTTPStatus.NOT_FOUND

        current_user = get_jwt_identity()

        if current_user != recipe.user_id:
            return {"message": "Access is not allowed"}, HTTPStatus.FORBIDDEN

        recipe.name = json_data['name']
        recipe.description = json_data['description']
        recipe.num_of_servings = json_data['num_of_servings']
        recipe.cook_time = json_data['cook_time']
        recipe.directions = json_data['directions']

        recipe.save()

        return recipe.data(), HTTPStatus.OK

    @jwt_required(optional=False)
    def delete(self, recipe_id):
        recipe = Recipe.get_by_id(recipe_id=recipe_id)

        if not recipe:
            return {"message": "recipe not found"}, HTTPStatus.NOT_FOUND

        current_user = get_jwt_identity()

        if current_user != recipe.user_id:
            return {"message": "Access is not allowed"}, HTTPStatus.FORBIDDEN
        
        recipe.delete()

        return {}, HTTPStatus.NO_CONTENT


class RecipePublishResource(Resource):
    @jwt_required()
    def put(self, recipe_id):
        recipe = Recipe.get_by_id(recipe_id)

        if recipe is None:
            return {"message": "recipe not found"}, HTTPStatus.NOT_FOUND

        if get_jwt_identity() != recipe.user_id:
            return {"message": "Access is not allowed"}, HTTPStatus.FORBIDDEN

        recipe.is_publish = True
        recipe.save()

        return {}, HTTPStatus.NO_CONTENT
    
    @jwt_required()
    def delete(self, recipe_id):
        recipe = Recipe.get_by_id(recipe_id)

        if recipe is None:
            return {"message": "recipe not found"}, HTTPStatus.NOT_FOUND

        if get_jwt_identity() != recipe.user_id:
            return {"message": "Access is not allowed"}, HTTPStatus.FORBIDDEN

        recipe.is_publish = False
        recipe.save()

        return {}, HTTPStatus.NO_CONTENT