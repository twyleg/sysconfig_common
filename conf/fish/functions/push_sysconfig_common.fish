function push_sysconfig_common --wraps=bash\ -c\ \'cd\ /home/twyleg/dev/sysconfig/sysconfig_common/\ \&\&\ git\ commit\ -a\ \&\&\ git\ push\ origin\ master\' --wraps=bash\ -c\ \'cd\ /home/twyleg/dev/sysconfig/sysconfig_common/\ \&\&\ git\ add\ .\ \&\&\ git\ commit\ \&\&\ git\ push\ origin\ master\' --description alias\ push_sysconfig_common=bash\ -c\ \'cd\ /home/twyleg/dev/sysconfig/sysconfig_common/\ \&\&\ git\ add\ .\ \&\&\ git\ commit\ \&\&\ git\ push\ origin\ master\'
  bash -c 'cd /home/twyleg/dev/sysconfig/sysconfig_common/ && git add . && git commit && git push origin master' $argv
        
end
