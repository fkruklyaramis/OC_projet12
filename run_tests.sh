#!/bin/bash
# Script pour lancer les tests avec coverage
# Fichier: run_tests.sh

echo "🧪 Lancement des tests Epic Events CRM avec coverage..."
echo "=================================================="

# Nettoyer les anciens rapports
rm -rf htmlcov/
rm -f .coverage

# Lancer les tests avec coverage
python -m pytest src/tests/ \
    --cov=src \
    --cov-report=html:htmlcov \
    --cov-report=term-missing \
    --cov-report=xml \
    --cov-fail-under=80 \
    --verbose

# Vérifier le code de sortie
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Tests réussis !"
    echo "📊 Rapport de coverage disponible dans htmlcov/index.html"
    echo ""
    echo "📈 Statistiques de coverage:"
    python -m coverage report --show-missing
else
    echo ""
    echo "❌ Certains tests ont échoué ou la couverture est insuffisante"
    exit 1
fi
