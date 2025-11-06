"""
Test suite for SummaryWorker parsing methods
"""

import unittest
import sys
import os

# Aggiungi parent directory al path per importare recorder_app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from recorder_app import SummaryWorker


class TestSummaryParsing(unittest.TestCase):
    """Test parsing delle risposte GPT4All"""

    def setUp(self):
        """Setup test - crea worker instance"""
        self.worker = SummaryWorker("test transcript")

    def test_parse_valid_json(self):
        """Test parsing JSON valido"""
        json_response = '''
        {
            "summary": "Questo è un riassunto di prova con informazioni importanti.",
            "key_points": ["Punto chiave 1", "Punto chiave 2", "Punto chiave 3"],
            "action_items": ["Task 1", "Task 2"]
        }
        '''
        result = self.worker._parse_response(json_response)

        self.assertIn("summary", result)
        self.assertIn("key_points", result)
        self.assertIn("action_items", result)

        self.assertIn("riassunto", result["summary"].lower())
        self.assertEqual(len(result["key_points"]), 3)
        self.assertEqual(len(result["action_items"]), 2)

    def test_parse_json_with_extra_text(self):
        """Test parsing JSON con testo prima/dopo"""
        json_response = '''
        Ecco il JSON richiesto:
        {
            "summary": "Riassunto della riunione di progetto.",
            "key_points": ["Budget approvato", "Deadline estesa"],
            "action_items": []
        }
        Spero sia utile!
        '''
        result = self.worker._parse_response(json_response)

        self.assertEqual(result["summary"], "Riassunto della riunione di progetto.")
        self.assertEqual(len(result["key_points"]), 2)
        self.assertEqual(len(result["action_items"]), 0)

    def test_parse_fallback_textual(self):
        """Test fallback parsing testuale quando JSON non disponibile"""
        text_response = '''
        SUMMARY: Questo è un riassunto in formato testo semplice.

        KEY POINTS:
        - Primo punto importante
        - Secondo punto chiave
        - Terzo elemento rilevante

        ACTION ITEMS:
        - Completare report entro venerdì
        - Chiamare cliente lunedì
        '''
        result = self.worker._parse_response(text_response)

        self.assertIn("riassunto", result["summary"].lower())
        self.assertEqual(len(result["key_points"]), 3)
        self.assertEqual(len(result["action_items"]), 2)

    def test_parse_italian_keywords(self):
        """Test parsing con keyword italiane"""
        text_response = '''
        RIASSUNTO: Meeting di retrospettiva sprint.

        PUNTI CHIAVE:
        1. Team soddisfatto della velocity
        2. Necessario migliorare code review
        3. Bug in produzione risolto rapidamente

        AZIONI:
        - Organizzare training su code review
        '''
        result = self.worker._parse_response(text_response)

        self.assertIn("retrospettiva", result["summary"].lower())
        self.assertEqual(len(result["key_points"]), 3)
        self.assertGreater(len(result["action_items"]), 0)

    def test_parse_no_action_items(self):
        """Test parsing quando non ci sono action items"""
        json_response = '''
        {
            "summary": "Briefing informativo senza task.",
            "key_points": ["Info A", "Info B"],
            "action_items": []
        }
        '''
        result = self.worker._parse_response(json_response)

        self.assertEqual(len(result["action_items"]), 0)

    def test_parse_empty_response(self):
        """Test parsing risposta vuota"""
        result = self.worker._parse_response("")

        # Dovrebbe avere valori di default
        self.assertIn("summary", result)
        self.assertIn("key_points", result)
        self.assertIn("action_items", result)

        # Summary di default
        self.assertIn("non disponibile", result["summary"].lower())

    def test_parse_malformed_json(self):
        """Test parsing JSON malformato - usa fallback"""
        malformed = '''
        {
            "summary": "Test",
            "key_points": ["A", "B"
            // JSON incompleto
        '''
        result = self.worker._parse_response(malformed)

        # Dovrebbe usare fallback e comunque restituire struttura valida
        self.assertIsInstance(result["summary"], str)
        self.assertIsInstance(result["key_points"], list)
        self.assertIsInstance(result["action_items"], list)

    def test_parse_mixed_bullet_styles(self):
        """Test parsing con diversi stili di bullet points"""
        text_response = '''
        SUMMARY: Test con vari bullet

        KEY POINTS:
        • Bullet con pallino
        - Bullet con trattino
        * Bullet con asterisco
        1. Bullet numerato
        2) Altro stile numerico

        ACTION ITEMS:
        ☐ Task con checkbox
        [] Task con parentesi
        '''
        result = self.worker._parse_response(text_response)

        # Dovrebbe riconoscere tutti i punti
        self.assertGreater(len(result["key_points"]), 0)
        self.assertGreater(len(result["action_items"]), 0)

    def test_parse_filter_nessuno_keyword(self):
        """Test che filtra correttamente 'nessuno' negli action items"""
        text_response = '''
        SUMMARY: Test filtro nessuno

        KEY POINTS:
        - Punto 1

        ACTION ITEMS:
        - Nessuno
        - N/A
        - Non applicabile
        '''
        result = self.worker._parse_response(text_response)

        # Dovrebbe filtrare tutti gli "nessuno"
        self.assertEqual(len(result["action_items"]), 0)


class TestSummaryParsingEdgeCases(unittest.TestCase):
    """Test edge cases e casi limite"""

    def setUp(self):
        self.worker = SummaryWorker("test")

    def test_very_long_response(self):
        """Test con risposta molto lunga"""
        long_summary = "A" * 10000
        json_response = f'''
        {{
            "summary": "{long_summary}",
            "key_points": ["P1", "P2"],
            "action_items": []
        }}
        '''
        result = self.worker._parse_response(json_response)

        self.assertEqual(len(result["summary"]), 10000)

    def test_unicode_characters(self):
        """Test con caratteri unicode e emoji"""
        json_response = '''
        {
            "summary": "Test con emoji 🎉 e caratteri speciali àèéìòù",
            "key_points": ["日本語", "中文", "한국어"],
            "action_items": ["Task con ✅"]
        }
        '''
        result = self.worker._parse_response(json_response)

        self.assertIn("emoji", result["summary"])
        self.assertEqual(len(result["key_points"]), 3)

    def test_nested_json_in_text(self):
        """Test con JSON annidato in testo"""
        response = '''
        Ecco un esempio: {"nested": "value"}
        Ma il vero JSON è questo:
        {
            "summary": "Riassunto corretto",
            "key_points": ["A"],
            "action_items": []
        }
        '''
        result = self.worker._parse_response(response)

        self.assertEqual(result["summary"], "Riassunto corretto")

    def test_multiple_sections_markers(self):
        """Test con marker di sezioni multipli"""
        text_response = '''
        SUMMARY: Prima parte
        Continuazione summary SUMMARY: non è un nuovo marker

        KEY POINTS:
        - Punto 1
        KEY POINTS: non ricomincia
        - Punto 2
        '''
        result = self.worker._parse_response(text_response)

        # Dovrebbe gestire correttamente
        self.assertIsInstance(result["summary"], str)
        self.assertGreater(len(result["key_points"]), 0)


def run_tests():
    """Esegue tutti i test"""
    # Crea test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestSummaryParsing))
    suite.addTests(loader.loadTestsFromTestCase(TestSummaryParsingEdgeCases))

    # Esegui test con output verboso
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Ritorna 0 se successo, 1 se fallito
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(run_tests())
