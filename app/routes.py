from flask import render_template, request, jsonify, redirect, url_for, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from sqlalchemy import or_, and_
from datetime import datetime
import os

from app import db, mail
from app.models import Product, Chambre, User, Reservation, Contact
from flask_mail import Message

def init_routes(app):
    # Routes principales
    @app.route('/')
    def index():
        chambres = Chambre.query.filter_by(disponible=True).all()
        return render_template('home/index.html', chambres=chambres)

    @app.route('/about')
    def about():
        return render_template('about.html')

    @app.route('/services')
    def services():
        return render_template('services.html')

    @app.route('/product/<int:id>')
    def product_details(id):
        product = Product.query.get_or_404(id)
        return render_template('product_details.html', product=product)

    # Routes API
    @app.route('/api/products', methods=['GET'])
    def get_products():
        products = Product.query.all()
        return jsonify([product.to_dict() for product in products])

    @app.route('/api/products', methods=['POST'])
    def create_product():
        data = request.get_json()
        product = Product(
            name=data['name'],
            description=data.get('description'),
            price=data['price'],
            image=data.get('image')
        )
        db.session.add(product)
        db.session.commit()
        return jsonify(product.to_dict()), 201

    # Routes d'authentification
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('index'))
        
        if request.method == 'POST':
            email = request.form.get('email')
            password = request.form.get('password')
            user = User.query.filter_by(email=email).first()
            
            if user and user.check_password(password):
                login_user(user)
                flash(f'Bienvenue {user.username} !', 'success')
                return redirect(url_for('index'))
            flash('Email ou mot de passe incorrect', 'danger')
        
        return render_template('auth/login.html')

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for('index'))
        
        if request.method == 'POST':
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')
            
            if User.query.filter_by(username=username).first():
                flash('Ce nom d\'utilisateur est déjà pris', 'danger')
                return redirect(url_for('register'))
            
            if User.query.filter_by(email=email).first():
                flash('Cet email est déjà utilisé', 'danger')
                return redirect(url_for('register'))
            
            user = User(username=username, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            
            flash('Votre compte a été créé avec succès', 'success')
            return redirect(url_for('login'))
        
        return render_template('auth/register.html')

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        return redirect(url_for('index'))

    @app.route('/profile')
    @login_required
    def profile():
        return render_template('auth/profile.html', user=current_user)

    # Routes des chambres
    @app.route('/chambres')
    def chambres():
        chambres = Chambre.query.all()
        return render_template('chambre/rooms.html', chambres=chambres)

    @app.route('/chambre/<int:id>')
    def chambre_details(id):
        chambre = Chambre.query.get_or_404(id)
        return render_template('room_details.html', chambre=chambre)

    @app.route('/chambre/create', methods=['GET', 'POST'])
    @login_required
    def chambre_create():
        if current_user.role != 'admin':
            flash('Accès non autorisé', 'danger')
            return redirect(url_for('chambres'))
        
        if request.method == 'POST':
            numero = request.form.get('numero')
            type_chambre = request.form.get('type_chambre')
            prix = float(request.form.get('prix'))
            description = request.form.get('description')
            
            if 'image' in request.files:
                file = request.files['image']
                if file.filename:
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                    image = filename
                else:
                    image = None
            else:
                image = None
            
            chambre = Chambre(
                numero=numero,
                type_chambre=type_chambre,
                prix=prix,
                description=description,
                image=image
            )
            
            db.session.add(chambre)
            db.session.commit()
            
            flash('Chambre créée avec succès', 'success')
            return redirect(url_for('chambres'))
        
        return render_template('room_create.html')

    # Routes des réservations
    @app.route('/reservations')
    @login_required
    def reservations():
        if current_user.role == 'admin':
            reservations = Reservation.query.all()
        else:
            reservations = Reservation.query.filter_by(user_id=current_user.id).all()
        return render_template('reservation/reservations.html', reservations=reservations)

    @app.route('/reservation/<int:id>')
    @login_required
    def reservation_details(id):
        reservation = Reservation.query.get_or_404(id)
        if current_user.role != 'admin' and reservation.user_id != current_user.id:
            flash('Accès non autorisé', 'danger')
            return redirect(url_for('reservations'))
        return render_template('reservation/details.html', reservation=reservation)

    @app.route('/reservation/<int:id>/annuler')
    @login_required
    def reservation_annuler(id):
        reservation = Reservation.query.get_or_404(id)
        if current_user.role != 'admin' and reservation.user_id != current_user.id:
            flash('Accès non autorisé', 'danger')
            return redirect(url_for('reservations'))
        
        if reservation.statut != 'en_attente':
            flash('Seules les réservations en attente peuvent être annulées', 'danger')
            return redirect(url_for('reservation_details', id=id))
        
        reservation.statut = 'annulée'
        db.session.commit()
        flash('Réservation annulée avec succès', 'success')
        return redirect(url_for('reservations'))

    @app.route('/reservation/create', methods=['GET', 'POST'])
    @login_required
    def reservation_create():
        if request.method == 'POST':
            chambre_id = request.form.get('chambre_id')
            date_debut = datetime.strptime(request.form.get('date_debut'), '%Y-%m-%d')
            date_fin = datetime.strptime(request.form.get('date_fin'), '%Y-%m-%d')
            
            chambre = Chambre.query.get_or_404(chambre_id)
            if not chambre.disponible:
                flash('Cette chambre n\'est pas disponible', 'danger')
                return redirect(url_for('reservation_create'))
            
            conflits = Reservation.query.filter(
                Reservation.chambre_id == chambre_id,
                Reservation.statut != 'annulée',
               or_(
                     and_(Reservation.date_debut <= date_debut, Reservation.date_fin >= date_debut),
                    and_(Reservation.date_debut <= date_fin, Reservation.date_fin >= date_fin),
                    and_(Reservation.date_debut >= date_debut, Reservation.date_fin <= date_fin)
                    )
            ).first()
            
            if conflits:
                flash('Cette chambre est déjà réservée pour cette période', 'danger')
                return redirect(url_for('reservation_create'))
            
            reservation = Reservation(
                user_id=current_user.id,
                chambre_id=chambre_id,
                date_debut=date_debut,
                date_fin=date_fin
            )
            
            db.session.add(reservation)
            db.session.commit()
            
            flash('Réservation créée avec succès', 'success')
            return redirect(url_for('reservations'))
        
        chambres = Chambre.query.filter_by(disponible=True).all()
        return render_template('reservation/create.html', chambres=chambres)

    # Routes de contact
    @app.route('/contact', methods=['GET', 'POST'])
    def contact():
        if request.method == 'POST':
            nom = request.form.get('nom')
            email = request.form.get('email')
            sujet = request.form.get('sujet')
            message = request.form.get('message')
            
            contact = Contact(
                nom=nom,
                email=email,
                sujet=sujet,
                message=message
            )
            
            db.session.add(contact)
            db.session.commit()
            
            msg = Message(
                subject=f"Confirmation de réception - {sujet}",
                recipients=[email],
                body=f"Bonjour {nom},\n\nNous avons bien reçu votre message concernant '{sujet}'. Nous vous répondrons dans les plus brefs délais.\n\nCordialement,\nL'équipe de la résidence"
            )
            mail.send(msg)
            
            flash('Votre message a été envoyé avec succès', 'success')
            return redirect(url_for('contact'))
        
        return render_template('contact.html')

    @app.route('/admin/contacts')
    @login_required
    def admin_contacts():
        if current_user.role != 'admin':
            flash('Accès non autorisé', 'danger')
            return redirect(url_for('index'))
        
        contacts = Contact.query.order_by(Contact.date_envoi.desc()).all()
        return render_template('admin_contacts.html', contacts=contacts) 