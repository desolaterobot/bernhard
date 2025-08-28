# bernhard
SimplifyNext Agentic AI Hackathon

## Running steps for streamlit app:
1. Install dependencies
```
pip install -r requirements.txt
```
2. Run the streamlit app:
```
streamlit run app.py
```
3. Should appear in browser as localhost
   
## Running steps for vector.py:
1. Install dependencies
```
pip install -r requirements.txt
```
2. Run the python file:
```
python vector.py
```
3. Move relevant documents to the documents folder.
4. Store text documents: type 's'
5. Query: type 'q'

Sample queries:
- Who is the joker?
- What did Heath Ledger do?
- Where did the last days of production take place?
- What is the general reception to The Dark Knight?

Initial findings: Works acceptably, but can be improved by using a better embedding model and better document splitting.
