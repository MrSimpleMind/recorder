"""
Test suite for AudioRecorder class
"""

import unittest
import sys
import os
import threading
import time

# Aggiungi parent directory al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from recorder_app import AudioRecorder
from PyQt5.QtCore import QThread


class TestAudioRecorderThreadSafety(unittest.TestCase):
    """Test thread safety del AudioRecorder"""

    def test_stop_event_is_thread_safe(self):
        """Test che stop_event sia thread-safe"""
        # Crea recorder (non lo avviamo realmente)
        recorder = AudioRecorder(device_index=0)

        # Verifica che stop_event esista ed è un threading.Event
        self.assertIsInstance(recorder.stop_event, threading.Event)

        # Test set/is_set
        self.assertFalse(recorder.stop_event.is_set())
        recorder.stop()
        self.assertTrue(recorder.stop_event.is_set())

    def test_stop_method_sets_event(self):
        """Test che stop() imposta correttamente l'event"""
        recorder = AudioRecorder(device_index=0)

        self.assertFalse(recorder.stop_event.is_set())
        recorder.stop()
        self.assertTrue(recorder.stop_event.is_set())

    def test_multiple_stop_calls_safe(self):
        """Test che chiamare stop() multipole volte sia sicuro"""
        recorder = AudioRecorder(device_index=0)

        # Chiama stop più volte
        recorder.stop()
        recorder.stop()
        recorder.stop()

        # Dovrebbe essere sempre settato
        self.assertTrue(recorder.stop_event.is_set())

    def test_recorder_initialization(self):
        """Test inizializzazione corretta"""
        device_index = 5
        sample_rate = 44100

        recorder = AudioRecorder(device_index, sample_rate)

        self.assertEqual(recorder.device_index, 5)
        self.assertEqual(recorder.sample_rate, 44100)
        self.assertIsInstance(recorder.stop_event, threading.Event)
        self.assertFalse(recorder.stop_event.is_set())

    def test_recorder_is_qthread(self):
        """Test che AudioRecorder eredita da QThread"""
        recorder = AudioRecorder(device_index=0)
        self.assertIsInstance(recorder, QThread)


class TestAudioRecorderSignals(unittest.TestCase):
    """Test signals di AudioRecorder"""

    def test_has_finished_signal(self):
        """Test che abbia il signal finished"""
        recorder = AudioRecorder(device_index=0)
        self.assertTrue(hasattr(recorder, 'finished'))

    def test_has_error_signal(self):
        """Test che abbia il signal error"""
        recorder = AudioRecorder(device_index=0)
        self.assertTrue(hasattr(recorder, 'error'))


def run_tests():
    """Esegue tutti i test"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestAudioRecorderThreadSafety))
    suite.addTests(loader.loadTestsFromTestCase(TestAudioRecorderSignals))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(run_tests())
