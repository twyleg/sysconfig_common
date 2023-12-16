function server --wraps='ssh twyleg.de' --description 'alias server=ssh twyleg.de'
  ssh twyleg.de $argv; 
end
