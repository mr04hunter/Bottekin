from bot.logging import get_logger
from bot.config import get_word_list

logger = get_logger("message_detector")


class MessageDetector:

    @staticmethod
    def is_duplicated_words(word_list: list[str], word_count: int) -> bool:
        """Returns True if the number of unique words multiplied by 5 is less than the total word count"""
        unique_words = set(word_list)

        if len(unique_words) * 5 <= word_count:
            logger.bind(
                unique_words=str(unique_words)
            ).info(f"Unique words")
            logger.bind(
                word_list=str(word_list)
            ).info(f"Too many duplicated words in feedback")
            return True
        return False

    @staticmethod
    def is_gibberish(words: list[str]) -> bool:
        """Return True if at least %70 of the words are gibberish"""
        word_list = get_word_list()
        total = len(words)
        if total == 0:
            return True

        valid_words = []
        invalid_words = []

        for word in words:
            word = word.lower()
            
            if word in word_list:
                valid_words.append(word)
                continue
            else:
                invalid_words.append(word)
            
        logger.bind(
            invalid_words=str(invalid_words),
            valid_words=str(valid_words)
        ).info("Valid and Invalid words on fb message")
        return not ((len(valid_words) / total) >= 0.7)

        
    



