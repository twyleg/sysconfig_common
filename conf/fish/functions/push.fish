function push --wraps='git push origin master' --description 'alias push=git push origin master'
  git push origin master $argv; 
end
