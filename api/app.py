from flask import Flask, abort, request, jsonify, g, url_for
from flask.ext.restful import Api, Resource, reqparse, fields, marshal
from flask.ext.httpauth import HTTPBasicAuth
from sqlalchemy.orm.exc import NoResultFound

from . import validate_email, validate_name_or_fullname, validate_nickname

from .models import User, Publicity, db, app

api = Api(app)
auth = HTTPBasicAuth()


def get_user_or_abort_400(nickname):
    try:
        user = User.query.filter_by(nickname=nickname).one()

    except NoResultFound:
        abort(400)

    return user


@auth.verify_password
def verify_password(nickname_or_token, password):
    # first try to authenticate by token
    user = User.verify_auth_token(nickname_or_token)
    if not user:
        # try to authenticate with username/password
        user = User.query.filter_by(nickname=nickname_or_token).first()
        if not user or not user.verify_password(password):
            return False
    g.user = user
    return True


@app.route('/api/token')
@auth.login_required
def get_auth_token():
    token = g.user.generate_auth_token(600)
    return jsonify({'token': token.decode('ascii'), 'duration': 600})


class UserAPI(Resource):
    """ Comsumiendo el recurso Usuaio"""

    decorators = [auth.login_required]

    def __init__(self):
        self.reqparse = reqparse.RequestParser()

        self.reqparse.add_argument('email', type=str,
                                    location='json')
        self.reqparse.add_argument('password', type=str,
                                    location='json')
        self.reqparse.add_argument('name', type=str,
                                    location='json')
        self.reqparse.add_argument('fullname', type=str,
                                    location='json')

        super(UserAPI, self).__init__()

    def get(self, nickname):
        if not nickname is g.user.nickname:
            abort(400)

        return {
            'user':{
                'id': g.user.id,
                'name': g.user.name, 'fullname': g.user.fullname,
                'nickname': g.user.nickname, 'email': g.user.email
            }
        }

    def put(self, nickname):
        if not nickname is g.user.nickname:
            abort(400)

        args = self.reqparse.parse_args()

        if args.name and validate_name_or_fullname(args.name):
            # Actualiza el name del usuario
            user.name = args.name

        if args.fullname and validate_name_or_fullname(args.fullname):
            # Actualiza el fullname del usuario
            user.fullname = args.fullname

        if args.email and validate_email(args.email):
            if not g.user.email is args.email:
                try:
                    User.query.filter_by(email=args.email).one()
                    abort(400)

                except NoResultFound:
                    # Actualiza el email del usuario
                    user.email = args.email

        if args.password :
            user.hash_password(args.password)

        db.session.add(user)
        db.session.commit()

        return {'result': True}

    def delete(self, nickname):
        if not nickname is g.user.nickname:
            abort(400)

        db.session.delete(g.user)
        db.session.commit()

        return {'result': True}


class UserCreateAPI(Resource):
    """ Creando un Usuario """

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('email', type=str, required=True, location='json')
        self.reqparse.add_argument('nickname', type=str, required=True, location='json')
        self.reqparse.add_argument('name', type=str, required=True, location='json')
        self.reqparse.add_argument('fullname', type=str, required=True, location='json')
        self.reqparse.add_argument('password', type=str, required=True, location='json')
        super(UserCreateAPI, self).__init__()

    def post(self):
        args = self.reqparse.parse_args()

        #validar con expreciones regulares
        if not validate_nickname(args.nickname):
            # nickname invalido
            abort(400)

        if not validate_name_or_fullname(args.name):
            # Nombres invalidos
            abort(400)

        if not validate_name_or_fullname(args.fullname):
            # Apellidos invalidos
            abort(400)

        if not validate_email(args.email):
            # Email invalido
            abort(400)

        #confirmar que no exista el nickname y el email
        try:
            User.query.filter_by(nickname=args.nickname).one()
            abort(400)

        except NoResultFound:
            try:
                User.query.filter_by(email=args.email).one()
                abort(400)

            except NoResultFound:
                pass

        user = User(args.name, args.fullname, args.nickname,
                    args.email, args.password)

        db.session.add(user)
        db.session.commit()

        return {
            'user':{
                'id': user.id,
                'name': user.name, 'fullname': user.fullname,
                'nickname': user.nickname, 'email': user.email,
            }
        }


class PublicityAPI(Resource):
    """ Comsumiendo el recurso Publicidad"""

    def __init__(self):
        self.reqparse = reqparse.RequestParser()

        self.reqparse.add_argument('publication', type=str, required=True,
                                    location='json')
        self.reqparse.add_argument('company_name', type=str, location='json')
        self.reqparse.add_argument('contact', type=str, location='json')

        super(PublicityAPI, self).__init__()

    def get(self, id):
        query = Publicity.query.get(id)

        if query is None:
            abort(400)

        return {
            'publicity':{
                'id': query.id, 'publication': query.publication,
                'contact': query.contact, 'company_name': query.company_name
            }
        }

    @auth.login_required
    def put(self, id):
        query = Publicity.query.get(id)

        if query is None:
        # Esta intentando actualizar una publicidad invalida
            abort(400)

        if g.user.id is not query.user.id:
        # Se esta intentando actualizar una Publicación que no le pertenece
            abort(400)

        args = self.reqparse.parse_args()

        query.publication = args.publication
        query.company_name = args.company_name
        query.contact = args.contact

        db.session.add(query)
        db.session.commit()

        return {
            'publicity':{
                'id': query.id, 'publication': query.publication,
                'contact': query.contact, 'company_name': query.company_name
            }
        }

    @auth.login_required
    def delete(self, id):
        query = Publicity.query.get(id)

        if query is None:
        # Esta intentando borrar una publicidad invalida
            abort(400)

        if g.user.id is not query.user.id:
        # Se esta intentando borrar una Publicacion que no le pertenece
            abort(400)

        db.session.delete(query)
        db.session.commit()

        return {'result': True}


class PublicityCR(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser()

        self.reqparse.add_argument('publication', type=str, required=True,
                                    location='json')
        self.reqparse.add_argument('company_name', type=str, location='json')
        self.reqparse.add_argument('contact', type=str, location='json')

        super(PublicityCR, self).__init__()

    def get(self):
        query = Publicity.query.all()

        publicities = []

        for item in query:
            publicities.append(
                {
                    'id': item.id, 'publication': item.publication,
                    'contact': item.contact, 'company_name': item.company_name
                }
            )

        return {'publicities': publicities}

    @auth.login_required
    def post(self):
        args = self.reqparse.parse_args()

        publicity = Publicity(g.user, args.publication,
                        args.company_name, args.contact)

        db.session.add(publicity)
        db.session.commit()

        return {
            'publicity':{
                'id': publicity.id, 'publication': publicity.publication,
                'contact': publicity.contact, 'company_name': publicity.company_name,
                'user': g.user.nickname
            }
        }


api.add_resource(UserAPI, '/api/user/<string:nickname>')
api.add_resource(UserCreateAPI, '/api/user')
api.add_resource(PublicityAPI, '/api/publicity/<int:id>')
api.add_resource(PublicityCR, '/api/publicity')
