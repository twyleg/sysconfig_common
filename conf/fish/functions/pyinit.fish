function pyinit --wraps='python -m venv venv/ && source venv/bin/activate.fish && pip install -r requirements.txt' --description 'alias pyinit=python -m venv venv/ && source venv/bin/activate.fish && pip install -r requirements.txt'
  python -m venv venv/ && source venv/bin/activate.fish && pip install -r requirements.txt $argv; 
end
