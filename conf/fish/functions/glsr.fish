function glsr --wraps='git ls-remote' --description 'alias glsr=git ls-remote'
  git ls-remote $argv; 
end
