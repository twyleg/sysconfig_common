function act --wraps='source venv/bin/activate.fish' --description 'alias act=source venv/bin/activate.fish'
  source venv/bin/activate.fish $argv
        
end
