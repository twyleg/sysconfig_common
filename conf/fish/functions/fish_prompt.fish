function fish_prompt
	
    set -q __fish_git_prompt_showupstream
    or set -g __fish_git_prompt_showupstream auto

    function _nim_prompt_wrapper
        set retc $argv[1]
        set field_name $argv[2]
        set field_value $argv[3]

        set_color normal
        set_color $retc
        set_color -o green
        #echo -n '['
        set_color normal
        test -n $field_name
        and echo -n $field_name:
        set_color $retc
        echo -n $field_value
        set_color -o green
        #echo -n ']'
    end
    
    and set retc yellow
    #or set retc red

    _nim_prompt_wrapper $retc '' (date +%X)
    set_color $retc
    echo -n ' - '
    set_color -o blue
    echo -n (prompt_pwd)' '
    #set_color -o green
    #echo -n ']'

    # Date
    #_nim_prompt_wrapper $retc '' (date +%X)

    # Virtual Environment
    set -q VIRTUAL_ENV
    and _nim_prompt_wrapper $retc V (basename "$VIRTUAL_ENV")

    # git
    set prompt_git (__fish_git_prompt | string trim -c ' ()')
    test -n "$prompt_git"
    and _nim_prompt_wrapper $retc G $prompt_git

    # Battery status
    type -q acpi
    and test (acpi -a 2> /dev/null | string match -r off)
    and _nim_prompt_wrapper $retc B (acpi -b | cut -d' ' -f 4-)

    # New line
    echo

    # Background jobs
    set_color normal
    for job in (jobs)
        echo -n '╰─>'
        echo $job
    end
    set_color normal
    set_color $retc
    
    # ssh session
    if [ -n "$SSH_CLIENT" ]
        set_color -o yellow
        echo -n 'ssh '
    end
    
    # prompt #
    if test "$USER" = root -o "$USER" = toor
        set_color -o red
    else
        set_color -o green
    end


    #echo -n [
    if test "$USER" = root -o "$USER" = toor
        set_color -o red
    else
        set_color -o green
    end
    echo -n $USER
    echo -n @
    echo -n (prompt_hostname)    
    #set_color -o blue

    echo -n ' $ '
    set_color normal
end
