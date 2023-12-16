function suspend --wraps=/etc/acpi/actions/powerbtn.sh --description 'alias suspend=/etc/acpi/actions/powerbtn.sh'
  /etc/acpi/actions/powerbtn.sh $argv; 
end
