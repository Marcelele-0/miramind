# miramind

comands required to run in terminal
cd miramind
pip install -e .

cd miramind/src/miramind/api/
uvicorn main:app --reload

cd miramind/src/miramind/frontend
npm install
npm run dev
