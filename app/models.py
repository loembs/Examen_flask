from app import db
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), default='user')  # admin, user, staff
    image = db.Column(db.String(100))  # Chemin vers l'image de profil
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @staticmethod
    def insert_test_data():
        users = [
            {
                'username': 'alytall',
                'email': 'aly.tall@example.com',
                'password': 'AlyTall2025!',
                'role': 'admin',
                'image': 'alytall.jpg'
            },
            {
                'username': 'patrick',
                'email': 'patrick.natsi@example.com',
                'password': 'Patrick2025!',
                'role': 'user',
                'image': 'patrick.jpg'
            }
        ]
        
        for user_data in users:
            user = User.query.filter_by(username=user_data['username']).first()
            if user is None:
                user = User(
                    username=user_data['username'],
                    email=user_data['email'],
                    role=user_data['role'],
                    image=user_data.get('image')
                )
                user.set_password(user_data['password'])
                db.session.add(user)
        
        db.session.commit()

class Chambre(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(10), unique=True, nullable=False)
    type_chambre = db.Column(db.String(50), nullable=False)
    prix = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)
    disponible = db.Column(db.Boolean, default=True)
    image = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @staticmethod
    def insert_test_data():
        chambres = [
            {
                'numero': '101',
                'type_chambre': 'Simple',
                'prix': 350.00,
                'description': 'Chambre simple avec lit simple, bureau et salle de bain privée.',
                'disponible': True,
                'image': 'chambre1.jpg'
            },
            {
                'numero': '102',
                'type_chambre': 'Double',
                'prix': 450.00,
                'description': 'Chambre double avec lit double, bureau et salle de bain privée.',
                'disponible': True,
                'image': 'chambre2.jpg'
            },
            {
                'numero': '201',
                'type_chambre': 'Suite',
                'prix': 600.00,
                'description': 'Suite avec salon, chambre séparée et salle de bain privée.',
                'disponible': True,
                'image': 'chambre3.jpg'
            },
            {
                'numero': '202',
                'type_chambre': 'Simple',
                'prix': 350.00,
                'description': 'Chambre simple avec lit simple, bureau et salle de bain privée.',
                'disponible': False,
                'image': 'chambre4.jpg'
            }
        ]
        
        for chambre_data in chambres:
            chambre = Chambre.query.filter_by(numero=chambre_data['numero']).first()
            if chambre is None:
                chambre = Chambre(**chambre_data)
                db.session.add(chambre)
        
        db.session.commit()

class Reservation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    chambre_id = db.Column(db.Integer, db.ForeignKey('chambre.id'), nullable=False)
    date_debut = db.Column(db.DateTime, nullable=False)
    date_fin = db.Column(db.DateTime, nullable=False)
    statut = db.Column(db.String(20), default='en_attente')  # en_attente, confirmée, annulée
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='reservations')
    chambre = db.relationship('Chambre', backref='reservations')

class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    sujet = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    date_envoi = db.Column(db.DateTime, default=datetime.utcnow)
    traite = db.Column(db.Boolean, default=False)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    image = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Product {self.name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': self.price,
            'image': self.image,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        } 