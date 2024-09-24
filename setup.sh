#!/usr/bin/env bash
set -e

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
CONF_DIR=$SCRIPT_DIR/conf

# echo $USER
# echo $HOME
# whoami
# 
# if [ ! "$(whoami)" == "$USER" ]; then
#     echo "Please run without sudo!!!"
#     echo "When setting up for root, startup a root shell with 'su' or 'sudo -s' and run again!"
#     exit 1
# fi
# 
# exit 0


source /etc/os-release

echo "Setting up for user: $USER"
echo "Home dir: $HOME"


as_root () {    
    if [ ! "$(whoami)" == "root" ]; then
        sh -c "sudo $*"
    else
        sh -c "$*"
    fi
}


setup_arch_linux () {
    echo "Setting up Arch Linux specifics"
    
    as_root pacman -Sy --noconfirm \
        git \
        curl \
        fish \
        neovim \
        tmux \
        tldr \
		fdfdsf
        
}


setup_debian_gnu_linux () {
    echo "Setting up Debian GNU/Linux specifics"
        
    as_root apt-get -y update 
    as_root apt-get -y install \
        git \
        curl \
        fish \
        neovim \
        tmux \
        tldr
        
    as_root update-alternatives --set vim /usr/bin/nvim
    as_root update-alternatives --set vi /usr/bin/nvim

}

sym_link () {
    echo "Creating sym link: $1 -> $2"
    if [ -e "$2" ]; then
        echo "'$2' Already existing. Skipping!!!" 
    fi
    ln -s $1 $2
}

setup_common () {
    echo "Setting up common stuff"
    
    mkdir -p $HOME/.config
    mkdir -p  $HOME/.config/nvim
    
    # fish
    ln -s $CONF_DIR/fish $HOME/.config/fish
    
    # git
    ln -s $CONF_DIR/git/gitconfig $HOME/.gitconfig
    
    # tmux
    ln -s $CONF_DIR/tmux/tmux.conf $HOME/.tmux.conf
    ln -s $CONF_DIR/tmux/tmux.conf.local $HOME/.tmux.conf.local
    
    # vi/vim/nvim
    ln -s $CONF_DIR/vim/vimrc $HOME/.config/nvim/init.vim
    ln -s $CONF_DIR/vim/vimrc $HOME/.vimrc
    curl -fLo "${XDG_DATA_HOME:-$HOME/.local/share}"/nvim/site/autoload/plug.vim --create-dirs \
        https://raw.githubusercontent.com/junegunn/vim-plug/master/plug.vim
        
    local _file
    for _file in vim edit ex vedit vi view; do
        ln -s nvim "/usr/bin/$_file"
    done
    vi -c "PlugInstall | qa!"
    
    as_root usermod -s /usr/bin/fish $(whoami)

}


case $NAME in

    "Arch Linux")
        setup_arch_linux
        ;;
    "Debian GNU/Linux" | "TUXEDO OS" | "Ubuntu")
        setup_debian_gnu_linux
        ;;
    *)
        echo "OS: \"$NAME\" not supported! Good Luck!!!"
        ;;
esac


setup_common
