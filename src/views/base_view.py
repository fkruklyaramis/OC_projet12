class BaseView:
    """Vue de base - Pattern MVC"""

    def display_error(self, message: str):
        """Afficher un message d'erreur"""
        print(f"ERREUR: {message}")

    def display_success(self, message: str):
        """Afficher un message de succès"""
        print(f"SUCCES: {message}")

    def display_info(self, message: str):
        """Afficher une information"""
        print(f"INFO: {message}")

    def get_user_input(self, prompt: str) -> str:
        """Récupérer une saisie utilisateur"""
        return input(f"{prompt}: ").strip()

    def get_user_choice(self, options: dict, prompt: str = "Votre choix") -> str:
        """Afficher un menu et récupérer le choix"""
        print("\nOptions disponibles:")
        for key, value in options.items():
            print(f"{key}. {value}")

        while True:
            choice = self.get_user_input(prompt)
            if choice in options.keys():
                return choice
            print("Choix invalide, veuillez réessayer.")

    def confirm_action(self, message: str) -> bool:
        """Demander confirmation"""
        response = self.get_user_input(f"{message} (o/n)")
        return response.lower() in ['o', 'oui', 'y', 'yes']
