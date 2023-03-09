from flask import url_for 
from marshmallow import Schema, fields, post_dump, validate, validates, ValidationError

from schemas.user import UserSchema


def validate_num_of_servings(n):
        if n < 1:
            raise ValidationError('Number of servings must be greater than 0.')
        if n > 50:
            raise ValidationError('Number of servings must not be grater than 50.')
        

class RecipeSchema(Schema):
    class Meta: 
        ordered = True 

    id = fields.Integer(dump_only=True)
    name = fields.String(required=True, 
                         validate=[validate.Length(max=100)])
    description = fields.String(validate=[validate.Length(max=200)])
    directions = fields.String(validate=[validate.Length(max=1000)])
    is_publish = fields.Boolean(dump_only=True)

    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
        
    num_of_servings = fields.Integer(validate=validate_num_of_servings)
    cook_time = fields.Integer()

    @validates('cook_time')
    def validate_cook_time(self, value):
        if value < 1:
            raise ValidationError('Cook time must be greater than 0.')
        if value > 300:
            raise ValidationError('Cook time must not be greater than 300.')
        
    author = fields.Nested(UserSchema, attribute='user', dump_only=True,
                           exclude=("email",))
        
    cover_url = fields.Method(serialize='cover_url_dump')
    
    def cover_url_dump(self, recipe):
        if recipe.cover_image:
            return url_for('static', filename=f"images/recipes/{recipe.cover_image}", _external=True)
        else: 
            return url_for('static', filename="images/assets/default_recipe_image.jpg", _external=True)

    @post_dump(pass_many=True)
    def wrap(self, data, many, **kwargs):
        if many:
            return {'data': data}
        return data