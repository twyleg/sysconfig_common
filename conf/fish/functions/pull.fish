function pull --wraps='git pull origin master' --description 'alias pull=git pull origin master'
  git pull origin master $argv; 
end
