import nltk
nltk.download("punkt")

class NLP:
    @staticmethod
    def contain_phrase(paragraph, phrase, case_insensitive=True):
        if case_insensitive:
            paragraph = paragraph.lower()
            phrase = phrase.lower()

        paragraph_words = nltk.tokenize.word_tokenize(paragraph)
        phrase_words = nltk.tokenize.word_tokenize(phrase)

        contains = False
        for i in range(len(paragraph_words)):
            if i + len(phrase_words) > len(paragraph_words):
                break
            matched = True
            for j in range(len(phrase_words)):
                if phrase_words[j] != paragraph_words[i + j]:
                    matched = False
                    break
            if matched:
                contains = True
                break

        return contains
