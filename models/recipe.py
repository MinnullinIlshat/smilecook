from extensions import db
from sqlalchemy import asc, desc, or_



class Recipe(db.Model):
    __tablename__ = 'recipe'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100),  nullable=False) 
    description = db.Column(db.String(200))
    num_of_servings = db.Column(db.Integer)
    cook_time = db.Column(db.Integer)
    directions = db.Column(db.String(1000))
    is_publish = db.Column(db.Boolean(), default=False)
    created_at = db.Column(db.DateTime(), nullable=False,
        server_default=db.func.now())
    updated_at = db.Column(db.DateTime(), nullable=False, 
        server_default=db.func.now(), onupdate=db.func.now())

    user_id = db.Column(db.Integer(), db.ForeignKey("user.id"))
    cover_image = db.Column(db.String(100), default=None)
    ingredients = db.Column(db.String(600))    
    
    @classmethod 
    def get_all_published(cls, q, page, per_page):
        
        keyword = f'%{q}%'
        
        return cls.query.filter(or_(
            cls.name.ilike(keyword),
            cls.description.ilike(keyword),
            cls.ingredients.ilike(keyword)),
            cls.is_publish.is_(True)).\
            order_by(desc(cls.created_at)).\
            paginate(page=page, per_page=per_page)
    
    @classmethod 
    def get_by_id(cls, recipe_id):
        return cls.query.filter_by(id=recipe_id).first()
    
    @classmethod 
    def get_all_by_user(cls, user_id, visibility='public', page=1, per_page=20):
        if visibility == 'public': 
            query = cls.query.filter_by(user_id=user_id, is_publish=True)
        elif visibility == 'private': 
            query = cls.query.filter_by(user_id=user_id, is_publish=False)
        else:
            query = cls.query.filter_by(user_id=user_id)
        return query.order_by(desc(cls.created_at)).paginate(page=page, per_page=per_page)
                
    def save(self):
        db.session.add(self)
        db.session.commit()
    
    def delete(self):
        db.session.delete(self)
        db.session.commit()