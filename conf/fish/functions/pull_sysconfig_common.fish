function pull_sysconfig_common --wraps='cd /home/twyleg/dev/sysconfig/sysonfig_common/ && git pull origin master' --wraps='cd /home/twyleg/dev/sysconfig/sysconfig_common/ && git pull origin master' --wraps=bash\ -c\ \'cd\ /home/twyleg/dev/sysconfig/sysconfig_common/\ \&\&\ git\ pull\ origin\ master\' --description alias\ pull_sysconfig_common=bash\ -c\ \'cd\ /home/twyleg/dev/sysconfig/sysconfig_common/\ \&\&\ git\ pull\ origin\ master\'
  bash -c 'cd /home/twyleg/dev/sysconfig/sysconfig_common/ && git pull origin master' $argv
        
end
