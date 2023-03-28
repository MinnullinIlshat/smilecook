import os, uuid

from flask import request, current_app
from flask_restful import Resource
from flask_jwt_extended import get_jwt_identity, jwt_required
from marshmallow import ValidationError
from werkzeug.utils import secure_filename
from http import HTTPStatus

from models.recipe import Recipe
from schemas.recipe import RecipeSchema, RecipePaginationSchema
from utils import allowed_file, compress_image, clear_cache
from extensions import cache, limiter

recipe_schema = RecipeSchema()
recipe_list_schema = RecipeSchema(many=True)
recipe_cover_schema = RecipeSchema(only=("cover_url",))
recipe_pagination_schema = RecipePaginationSchema()


class RecipeListResource(Resource):
    decorators = [limiter.limit('2 per minute', methods=['GET'], error_message="Too Many Requests")]
    
    @cache.cached(timeout=60, query_string=True)
    def get(self):
        print('Querying database ...')
        args = request.args.to_dict()
        
        per_page = int(args.get('per_page') or 20)
        page = int(args.get('page') or 1)
        q = args.get('q') or ''
        
        paginated_recipes = Recipe.get_all_published(q, page, per_page)
        return recipe_pagination_schema.dump(paginated_recipes), HTTPStatus.OK

    @jwt_required()
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

    @jwt_required()
    def patch(self, recipe_id):
        json_data = request.get_json()

        try:
            data = recipe_schema.load(data=json_data, partial=('name',))
        except ValidationError as err:
            return {"message": "Validation error", "errors": err.messages}, HTTPStatus.BAD_REQUEST 
        
        recipe = Recipe.get_by_id(recipe_id=recipe_id)

        if recipe is None:
            return {"message": "Recipe not found"}, HTTPStatus.NOT_FOUND
        
        current_user = get_jwt_identity()

        if current_user != recipe.user_id:
            return {"message": "Access is not allowed"}, HTTPStatus.FORBIDDEN
        
        recipe.name = data.get('name') or recipe.name 
        recipe.description = data.get('description') or recipe.description
        recipe.num_of_servings = data.get('num_of_servings') or recipe.num_of_servings
        recipe.cook_time = data.get('cook_time') or recipe.cook_time
        recipe.directions = data.get('directions') or recipe.directions
        recipe.ingredients = data.get('ingredients') or recipe.ingredients

        recipe.save()
        
        clear_cache('/recipes')
        
        return recipe_schema.dump(recipe), HTTPStatus.OK


    @jwt_required()
    def delete(self, recipe_id):
        recipe = Recipe.get_by_id(recipe_id=recipe_id)

        if not recipe:
            return {"message": "recipe not found"}, HTTPStatus.NOT_FOUND

        current_user = get_jwt_identity()

        if current_user != recipe.user_id:
            return {"message": "Access is not allowed"}, HTTPStatus.FORBIDDEN
        
        recipe.delete()
        
        clear_cache('/recipes')

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
        
        clear_cache('/recipes')

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
        
        clear_cache("/recipes")

        return {}, HTTPStatus.NO_CONTENT
    
    
class RecipeCoverUploadResource(Resource):
    @jwt_required() 
    def put(self, recipe_id):
        file = request.files.get('cover')
        if not file:
            return {"message": "File not found"}, HTTPStatus.BAD_REQUEST
        if not allowed_file(file.filename):
            return {"message": "Incorrect file type."}, HTTPStatus.BAD_REQUEST 
        
        folder = current_app.config["UPLOADED_IMAGES_DEST"] + '/recipes'
        recipe = Recipe.get_by_id(recipe_id=recipe_id)
        
        if recipe is None:
            return {"message": "Recipe is not found"}, HTTPStatus.BAD_REQUEST
        
        current_user = get_jwt_identity()
        
        if current_user != recipe.user_id:
            return {"message": "Access is not allowed"}, HTTPStatus.BAD_REQUEST
        
        if recipe.cover_image:
            cover_path = os.path.join(folder, recipe.cover_image)
            if os.path.exists(cover_path):
                os.remove(cover_path)
        
        extension = secure_filename(file.filename).rsplit('.', 1)[1]
        filename = f"{uuid.uuid4()}.{extension}"
    
        file.save(os.path.join(folder, filename))
        filename = compress_image(filename, folder)
        
        recipe.cover_image = filename
        recipe.save() 
        
        clear_cache("/recipes")
        
        return recipe_cover_schema.dump(recipe), HTTPStatus.OK