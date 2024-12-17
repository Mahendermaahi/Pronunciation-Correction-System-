import tkinter as tk
from tkinter import ttk, messagebox
import speech_recognition as sr
import pyttsx3
from difflib import get_close_matches
from fuzzywuzzy import fuzz
import phonetics  # For Metaphone algorithm
import spacy  # NLP model for semantic similarity

class PronunciationChecker:
    def __init__(self, root):
        self.root = root
        self.root.title("Pronunciation Checker")

        self.label = ttk.Label(root, text="Enter a word or phrase:")
        self.label.pack(pady=10)

        self.entry = ttk.Entry(root, width=30)
        self.entry.pack(pady=10)
        self.check_button = ttk.Button(root, text="Check Pronunciation", command=self.check_pronunciation)
        self.check_button.pack(pady=10)
        self.history_button = ttk.Button(root, text="Show History", command=self.show_history)
        self.history_button.pack(pady=10)
        self.semantic_threshold = ttk.Scale(root, from_=0.5, to_=1.0, value=0.85, orient="horizontal")
        self.semantic_threshold.pack(pady=10)
        ttk.Label(root, text="Adjust Semantic Similarity Threshold").pack()

        self.pronunciation_history = []
        self.nlp = spacy.load("en_core_web_md")

    def check_pronunciation(self):
        # Get the target word or phrase from the entry widget
        target_text = self.entry.get()

        if not target_text:
            messagebox.showwarning("Warning", "Please enter a word or phrase.")
            return

        # Recognize speech
        spoken_text = self.listen()
        if not spoken_text:
            messagebox.showerror("Error", "Unable to recognize speech. Please try again.")
            return

        # Handle OOV (Out of Vocabulary)
        if self.handle_oov(target_text):
            result = f"The word/phrase '{target_text}' is out of vocabulary for semantic comparison."
            self.speak(result)
            messagebox.showinfo("Result", result)
            return

        # Phonetic and semantic comparisons
        phonetic_similarity = self.phonetic_comparison(spoken_text.lower(), target_text.lower())
        semantic_similarity = self.semantic_comparison(spoken_text.lower(), target_text.lower())
        threshold = self.semantic_threshold.get()

        # Provide feedback
        result = (
            f"Target Word/Phrase: {target_text}\n"
            f"Spoken: {spoken_text}\n"
            f"Phonetic Similarity: {phonetic_similarity}%\n"
            f"Semantic Similarity: {semantic_similarity:.2f}\n"
        )

        # Provide final feedback
        if phonetic_similarity > 75 and semantic_similarity > threshold:
            result += "Great pronunciation!"
        else:
            corrected_word = self.correct_word(spoken_text.lower(), target_text.lower())
            result += f"Incorrect pronunciation! Did you mean: {corrected_word}?"

        self.pronunciation_history.append((target_text, spoken_text, result))
        self.speak(result)
        messagebox.showinfo("Result", result)

    def listen(self):
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            print("Speak now...")
            recognizer.adjust_for_ambient_noise(source)
            audio = recognizer.listen(source)

        try:
            print("Recognizing...")
            spoken_text = recognizer.recognize_google(audio)
            print("You said:", spoken_text)
            return spoken_text
        except sr.UnknownValueError:
            print("Unable to recognize speech")
            return ""
        except sr.RequestError as e:
            print(f"Speech recognition request error: {str(e)}")
            return ""

    def phonetic_comparison(self, spoken_word, target_word):
        spoken_metaphone = phonetics.metaphone(spoken_word)
        target_metaphone = phonetics.metaphone(target_word)
        phonetic_similarity = fuzz.ratio(spoken_metaphone, target_metaphone)
        print(f"Phonetic similarity: {phonetic_similarity}%")
        return phonetic_similarity

    def semantic_comparison(self, spoken_phrase, target_phrase):
        spoken_doc = self.nlp(spoken_phrase)
        target_doc = self.nlp(target_phrase)
        similarity = spoken_doc.similarity(target_doc)
        print(f"Semantic similarity: {similarity}")
        return similarity

    def correct_word(self, mispronounced_word, target_word):
        pronunciation_dict = {
            "helo": "hello",
            "wold": "world",
        }

        if mispronounced_word in pronunciation_dict:
            return pronunciation_dict[mispronounced_word]

        close_matches = get_close_matches(mispronounced_word, [target_word], n=1, cutoff=0.6)
        return close_matches[0] if close_matches else mispronounced_word

    def handle_oov(self, phrase):
    # Check if the phrase has a vector representation in spaCy
        doc = self.nlp(phrase)
    
    # If the vector is all zeros or not present, the phrase is out of vocabulary
        if not doc.vector.any():
            print(f"Phrase '{phrase}' is out of vocabulary (OOV).")
            return True
        return False


    def speak(self, text):
        engine = pyttsx3.init()
        engine.say(text)
        engine.runAndWait()

    def show_history(self):
        history_window = tk.Toplevel(self.root)
        history_window.title("Pronunciation History")
        text_area = tk.Text(history_window, wrap="word", width=50, height=20)
        text_area.pack(pady=10)

        for target, spoken, result in self.pronunciation_history:
            text_area.insert(tk.END, f"Word/Phrase: {target}\nYou said: {spoken}\nFeedback: {result}\n\n")

        text_area.config(state="disabled")

if __name__ == "__main__":
    root = tk.Tk()
    app = PronunciationChecker(root)
    root.mainloop()

