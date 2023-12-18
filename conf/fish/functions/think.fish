function think --wraps='ssh think-arch' --wraps='ssh twyleg-think-arch' --description 'alias think=ssh twyleg-think-arch'
  ssh twyleg-think-arch $argv
        
end
