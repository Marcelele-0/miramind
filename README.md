# miramind

comands required to run in terminal
cd miramind
pip install -e .

cd miramind/src/
uvicorn miramind.api.main:app --reload

cd miramind/src/miramind/frontend
npm install
npm run dev
