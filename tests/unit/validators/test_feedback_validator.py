from bot.utils.message_detector import MessageDetector


class TestMessageDetector:

    def test_gibberish_rejects_random_chars(self):
        words = ["asdfgh", "qwerty", "zxcvbn", "poiuyt"]
        assert MessageDetector.is_gibberish(words) is True

    def test_gibberish_accepts_real_words(self):
        words = ["this", "track", "has", "great", "melody", "and", "good", "mix"]
        assert MessageDetector.is_gibberish(words) is False

    def test_gibberish_empty_list(self):
        assert MessageDetector.is_gibberish([]) is True

    def test_gibberish_threshold_is_seventy_percent(self):
        words = ["this", "track", "has", "great", "melody", "good", "mix",
                 "asdfgh", "qwerty", "zxcvbn"]
        assert MessageDetector.is_gibberish(words) is False

    def test_duplicated_words_rejects_spam(self):
        words = ["good", "good", "good", "good", "good", "good"]
        assert MessageDetector.is_duplicated_words(words, word_count=6) is True

    def test_duplicated_words_accepts_varied_content(self):
        words = ["this", "track", "has", "great", "melody", "and",
                 "the", "mix", "is", "clean"]
        assert MessageDetector.is_duplicated_words(words, word_count=10) is False

    def test_duplicated_words_boundary(self):
        words = ["a", "b"]
        assert MessageDetector.is_duplicated_words(words, word_count=10) is True