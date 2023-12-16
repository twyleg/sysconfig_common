#!/usr/bin/env bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
CONF_DIR=$SCRIPT_DIR/conf

source /etc/os-release

echo "Home dir: $HOME"


setup_arch_linux () {
    echo "Setting up Arch Linux specifics"
    
    pacman -Sy --noconfirm \
        git \
        curl \
        fish \
        neovim \
        tmux \
        tldr
        
}


setup_debian_gnu_linux () {
    echo "Setting up Debian GNU/Linux specifics"
        
    apt-get -y update
    apt-get -y install \
        git \
        curl \
        fish \
        neovim \
        tmux \
        tldr
        
}

setup_common () {
    echo "Setting up common stuff"
    
    mkdir -p ~/.config
    mkdir -p ~/.config/nvim
    
    # fish
    ln -s $CONF_DIR/fish $HOME/.config/fish
    
    # tmux
    ln -s $CONF_DIR/tmux/tmux.conf $HOME/.tmux.conf
    ln -s $CONF_DIR/tmux/tmux.conf.local $HOME/.tmux.conf.local
    
    # vi/vim/nvim
    ln -s $CONF_DIR/vim/vimrc $HOME/.config/nvim/init.vim
    ln -s $CONF_DIR/vim/vimrc $HOME/.vimrc
    sh -c 'curl -fLo "${XDG_DATA_HOME:-$HOME/.local/share}"/nvim/site/autoload/plug.vim --create-dirs \
        https://raw.githubusercontent.com/junegunn/vim-plug/master/plug.vim'
        
    local _file
    for _file in vim edit ex vedit vi view; do
        ln -s nvim "/usr/bin/$_file"
    done
    vi -c "PlugInstall | qa!"
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
