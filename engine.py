import pandas as pd
import numpy as np
import google.generativeai as genai
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import re

# --- CONFIGURATION ---
DATA_FILE = "shl_assessments_advanced.csv" 
MODEL_NAME = 'all-MiniLM-L6-v2'

class RecommendationEngine:
    def __init__(self):
        print("Initializing Engine...")
        try:
            self.df = pd.read_csv(DATA_FILE).fillna('')
        except FileNotFoundError:
            print(f"⚠️ Could not find {DATA_FILE}. Using basic file if available.")
            self.df = pd.read_csv("shl_assessments.csv").fillna('')

        # Context Engineering: Combine fields for better search matching
        self.df['combined_text'] = (
            self.df['name'] + " " + 
            self.df['description'] + " " + 
            self.df.get('test_type', '')
        )
        
        self.model = SentenceTransformer(MODEL_NAME)
        self.embeddings = self.model.encode(self.df['combined_text'].tolist())
        print("Engine Ready.")

    def detect_intent(self, query):
        """Analyzes if query needs Technical, Behavioral, or Hybrid tests."""
        intent = {'tech': False, 'behavior': False}
        query_lower = query.lower()
        if any(w in query_lower for w in ['java', 'python', 'sql', 'coding', 'technical', 'developer', 'data']):
            intent['tech'] = True
        if any(w in query_lower for w in ['lead', 'communicat', 'collaborat', 'personality', 'behavior', 'manager', 'sales']):
            intent['behavior'] = True
        return intent

    def format_for_compliance(self, row, score):
        """
        STRICT FORMATTING: Matches the PDF Appendix 3 JSON requirements exactly.
        """
        # 1. Clean Duration (Convert "30 mins" -> 11)
        dur_str = str(row.get('duration', '30'))
        dur_match = re.search(r'\d+', dur_str)
        duration_val = int(dur_match.group(0)) if dur_match else 30

        # 2. Format Test Type (String -> List ["Knowledge & Skills"])
        type_str = row.get('test_type', 'General')
        type_list = [t.strip() for t in type_str.split(',')]

        return {
            "url": row['url'],
            "name": row['name'],
            "adaptive support": row.get('adaptive_support', 'No'), # PDF requires space
            "description": row['description'],
            "duration": duration_val, # PDF requires Integer
            "remote support": row.get('remote_support', 'Yes'), # PDF requires space
            "test_type": type_list, # PDF requires List
            "score": float(score) # Helper for UI (not in PDF, but useful)
        }

    def search(self, query, top_k=5):
        # 1. Semantic Search
        q_vec = self.model.encode([query])
        scores = cosine_similarity(q_vec, self.embeddings)[0]
        
        # 2. Candidate Selection
        top_indices = np.argsort(scores)[-30:][::-1]
        candidates = self.df.iloc[top_indices].copy()
        candidates['score'] = scores[top_indices]
        
        # 3. Constraint Filtering (Duration)
        time_limit = 999
        match = re.search(r'(?:max duration|less than|within|under)\s*(?:of)?\s*(\d+)', query.lower())
        if match:
            time_limit = int(match.group(1))
            candidates['duration_int'] = candidates['duration'].astype(str).str.extract('(\d+)').astype(float).fillna(999)
            candidates = candidates[candidates['duration_int'] <= time_limit]

        # 4. Hybrid Balancing
        intent = self.detect_intent(query)
        final_rows = []
        
        if intent['tech'] and intent['behavior']:
            tech = candidates[candidates['test_type'].str.contains("Knowledge", case=False)].head(3)
            behav = candidates[candidates['test_type'].str.contains("Personality", case=False)].head(2)
            combined = pd.concat([tech, behav]).drop_duplicates().head(top_k)
        else:
            combined = candidates.head(top_k)
            
        # 5. FINAL FORMATTING LOOP
        results = []
        for idx, row in combined.iterrows():
            # Use original score from the candidate dataframe
            score = row['score']
            formatted_item = self.format_for_compliance(row, score)
            results.append(formatted_item)

        return results

    def generate_ai_explanation(self, query, recommendations, api_key):
        if not api_key: return None
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-2.5-flash')
            
            rec_list = "\n".join([f"- {r['name']} ({', '.join(r['test_type'])})" for r in recommendations])
            
            prompt = f"""
            Act as an Expert SHL Consultant. User Query: "{query}"
            Recommendations:
            {rec_list}
            Write a concise 3-sentence justification for this selection, focusing on how it balances the specific hard and soft skills requested.
            """
            return model.generate_content(prompt).text
        except Exception as e:
            return f"AI Analysis Unavailable: {str(e)}"