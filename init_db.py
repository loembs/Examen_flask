import os
from app import create_app, db
from app.models import Chambre

# Créer le dossier instance s'il n'existe pas
instance_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
if not os.path.exists(instance_path):
    os.makedirs(instance_path)

app = create_app()

with app.app_context():
    # Créer toutes les tables
    db.create_all()
    
    # Insérer les données de test
    Chambre.insert_test_data()
    
    print("Base de données initialisée avec succès !") 