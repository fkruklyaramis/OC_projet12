"""Service d'authentification JWT pour Epic Events"""
import os
import json
import jwt
from datetime import datetime, timedelta
from pathlib import Path
from django.contrib.auth import get_user_model
from django.conf import settings


def get_auth_services():
    """Import différé des services d'authentification"""
    from .auth import AuthService, PermissionService
    return AuthService, PermissionService


class JWTAuthService:
    """Service d'authentification JWT avec stockage persistant"""

    JWT_SECRET = getattr(settings, 'JWT_SECRET', 'epic-events-jwt-secret-key-for-development')
    JWT_ALGORITHM = 'HS256'
    JWT_EXPIRATION_HOURS = getattr(settings, 'JWT_EXPIRATION_HOURS', 8)
    TOKEN_FILE = Path.home() / '.epicevents_token'

    @classmethod
    def login(cls, username, password):
        """Authentifie un utilisateur et génère un token JWT persistant"""
        AuthService, _ = get_auth_services()

        # Nettoyer le token existant avant la nouvelle connexion
        cls.logout()

        user = AuthService.authenticate_user(username, password)
        if not user:
            return None, "Identifiants invalides"

        now = datetime.utcnow()
        token_data = {
            'user_id': user.id,
            'username': user.username,
            'role': user.role,
            'employee_number': user.employee_number,
            'exp': int((now + timedelta(hours=cls.JWT_EXPIRATION_HOURS)).timestamp()),
            'iat': int(now.timestamp())
        }

        try:
            token = jwt.encode(token_data, cls.JWT_SECRET, algorithm=cls.JWT_ALGORITHM)
            cls._store_token(token, user)
            return token, f"Connexion réussie pour {user.username}"
        except Exception as e:
            return None, f"Erreur lors de la génération du token: {e}"

    @classmethod
    def logout(cls):
        """Supprime le token stocké localement"""
        try:
            if cls.TOKEN_FILE.exists():
                cls.TOKEN_FILE.unlink()
                return True, "Déconnexion réussie"
            else:
                return False, "Aucune session active"
        except Exception as e:
            return False, f"Erreur lors de la déconnexion: {e}"

    @classmethod
    def get_current_user(cls):
        """Récupère l'utilisateur actuel depuis le token stocké"""
        try:
            User = get_user_model()
            token_data = cls._load_token()
            if not token_data:
                return None, "Aucune session active"

            payload = jwt.decode(
                token_data['token'],
                cls.JWT_SECRET,
                algorithms=[cls.JWT_ALGORITHM]
            )

            user = User.objects.get(id=payload['user_id'])
            return user, "Session valide"

        except jwt.ExpiredSignatureError:
            cls.logout()
            return None, "Session expirée, veuillez vous reconnecter"
        except jwt.InvalidSignatureError:
            cls.logout()
            return None, "Signature du token invalide, veuillez vous reconnecter"
        except jwt.InvalidTokenError:
            cls.logout()
            return None, "Token invalide, veuillez vous reconnecter"
        except User.DoesNotExist:
            cls.logout()
            return None, "Utilisateur introuvable, veuillez vous reconnecter"
        except Exception as e:
            cls.logout()
            return None, f"Erreur d'authentification: {e}"

    @classmethod
    def check_permission(cls, permission):
        """Vérifie si l'utilisateur actuel a une permission spécifique"""
        _, PermissionService = get_auth_services()
        user, message = cls.get_current_user()
        if not user:
            return False, message

        has_permission = getattr(PermissionService, permission, lambda u: False)(user)

        if has_permission:
            return True, f"Permission '{permission}' accordée"
        else:
            return False, f"Permission '{permission}' refusée pour le rôle {user.role}"

    @classmethod
    def is_authenticated(cls):
        """Vérifie si un utilisateur est connecté"""
        user, _ = cls.get_current_user()
        return user is not None

    @classmethod
    def get_token_info(cls):
        """Récupère les informations du token actuel"""
        try:
            token_data = cls._load_token()
            if not token_data:
                return None

            payload = jwt.decode(
                token_data['token'],
                cls.JWT_SECRET,
                algorithms=[cls.JWT_ALGORITHM],
                options={"verify_exp": False}
            )

            exp_timestamp = payload.get('exp')
            exp_date = datetime.fromtimestamp(exp_timestamp) if exp_timestamp else None

            return {
                'username': payload.get('username'),
                'role': payload.get('role'),
                'employee_number': payload.get('employee_number'),
                'expires_at': exp_date,
                'is_expired': exp_date < datetime.utcnow() if exp_date else True
            }
        except Exception:
            cls.logout()
            return None

    @classmethod
    def _store_token(cls, token, user):
        """Stocke le token dans un fichier local sécurisé"""
        token_data = {
            'token': token,
            'username': user.username,
            'role': user.role,
            'stored_at': datetime.utcnow().isoformat(),
            'secret_hash': hash(cls.JWT_SECRET)  # Pour debug
        }

        try:
            cls.TOKEN_FILE.parent.mkdir(exist_ok=True)
            with open(cls.TOKEN_FILE, 'w') as f:
                json.dump(token_data, f, indent=2)

            os.chmod(cls.TOKEN_FILE, 0o600)

        except Exception as e:
            raise Exception(f"Impossible de stocker le token: {e}")

    @classmethod
    def _load_token(cls):
        """Charge le token depuis le fichier local"""
        try:
            if not cls.TOKEN_FILE.exists():
                return None

            with open(cls.TOKEN_FILE, 'r') as f:
                data = json.load(f)
                return data

        except Exception:
            return None

    @classmethod
    def refresh_token_if_needed(cls):
        """Rafraîchit le token s'il expire bientôt"""
        token_info = cls.get_token_info()
        if not token_info or token_info['is_expired']:
            return False, "Token expiré ou invalide"

        time_until_expiry = token_info['expires_at'] - datetime.utcnow()
        if time_until_expiry < timedelta(minutes=30):
            user, _ = cls.get_current_user()
            if user:
                now = datetime.utcnow()
                new_token_data = {
                    'user_id': user.id,
                    'username': user.username,
                    'role': user.role,
                    'employee_number': user.employee_number,
                    'exp': int((now + timedelta(hours=cls.JWT_EXPIRATION_HOURS)).timestamp()),
                    'iat': int(now.timestamp())
                }

                new_token = jwt.encode(new_token_data, cls.JWT_SECRET,
                                       algorithm=cls.JWT_ALGORITHM)
                cls._store_token(new_token, user)
                return True, "Token rafraîchi"

        return True, "Token valide"

    @classmethod
    def debug_token(cls):
        """Méthode de debug pour vérifier le token"""
        try:
            token_data = cls._load_token()
            if not token_data:
                return "Aucun fichier token trouvé"

            print(f"Fichier token: {cls.TOKEN_FILE}")
            print(f"Secret utilisé (hash): {hash(cls.JWT_SECRET)}")
            print(f"Secret stocké (hash): {token_data.get('secret_hash', 'N/A')}")
            print(f"Contenu: {token_data}")

            # Test de décodage avec options de debug
            try:
                payload = jwt.decode(
                    token_data['token'],
                    cls.JWT_SECRET,
                    algorithms=[cls.JWT_ALGORITHM],
                    options={"verify_exp": False}
                )
                print(f"Payload décodé: {payload}")

                # Test avec vérification d'expiration
                jwt.decode(
                    token_data['token'],
                    cls.JWT_SECRET,
                    algorithms=[cls.JWT_ALGORITHM]
                )
                print("Token valide avec vérification d'expiration")

            except jwt.ExpiredSignatureError:
                print("Token expiré")
            except jwt.InvalidSignatureError:
                print("Signature invalide")
            except Exception as decode_error:
                print(f"Erreur de décodage: {decode_error}")

            return "Debug terminé"

        except Exception as e:
            return f"Erreur debug: {e}"
