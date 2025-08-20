import jwt
import json
import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from pathlib import Path
from src.database.config import SECRET_KEY


class JWTManager:
    """Gestionnaire JWT pour l'authentification persistante"""

    def __init__(self):
        self.secret_key = SECRET_KEY
        self.algorithm = "HS256"
        self.token_file = Path.home() / ".epic_events" / "token"
        self.expiration_hours = 8

    def _ensure_token_dir(self):
        """Créer le répertoire de stockage du token si nécessaire"""
        self.token_file.parent.mkdir(parents=True, exist_ok=True)

    def generate_token(self, user_id: int, email: str, department: str,
                       employee_number: str) -> str:
        """Générer un JWT token pour l'utilisateur"""
        payload = {
            'user_id': user_id,
            'email': email,
            'department': department,
            'employee_number': employee_number,
            'exp': datetime.now(timezone.utc) + timedelta(hours=self.expiration_hours),
            'iat': datetime.now(timezone.utc)
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Vérifier et décoder un JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    def save_token(self, token: str) -> bool:
        """Sauvegarder le token sur le disque"""
        try:
            self._ensure_token_dir()
            with open(self.token_file, 'w') as f:
                json.dump({
                    'token': token,
                    'created_at': datetime.now(timezone.utc).isoformat()
                }, f)
            # Sécuriser le fichier (lecture/écriture pour le propriétaire uniquement)
            os.chmod(self.token_file, 0o600)
            return True
        except Exception:
            return False

    def load_token(self) -> Optional[str]:
        """Charger le token depuis le disque"""
        try:
            if not self.token_file.exists():
                return None

            with open(self.token_file, 'r') as f:
                data = json.load(f)
                return data.get('token')
        except Exception:
            return None

    def clear_token(self) -> bool:
        """Supprimer le token stocké"""
        try:
            if self.token_file.exists():
                self.token_file.unlink()
            return True
        except Exception:
            return False

    def get_current_user_data(self) -> Optional[Dict[str, Any]]:
        """Récupérer les données de l'utilisateur actuellement connecté"""
        token = self.load_token()
        if not token:
            return None

        payload = self.verify_token(token)
        if not payload:
            # Token expiré ou invalide, le supprimer
            self.clear_token()
            return None

        return payload

    def is_authenticated(self) -> bool:
        """Vérifier si un utilisateur est authentifié"""
        return self.get_current_user_data() is not None
