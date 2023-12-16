# Defined via `source`
function wake_win10_desktop --wraps='wakeonlan ‎-i "192.168.1.102" "80:EE:73:E3:00:9F"' --description 'alias wake_win10_desktop wakeonlan ‎-i "192.168.1.102" "80:EE:73:E3:00:9F"'
  wakeonlan ‎-i "192.168.1.102" "80:EE:73:E3:00:9F" $argv; 
end
